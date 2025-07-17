
import subprocess
from sys import meta_path
import tempfile
import os

from requests import Response
from .forms import Code_Form
from problem_list.models import Problem  
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from submissions.models import Submission
import google.generativeai as genai
genai.configure(api_key= "AIzaSyDxK_VjyVBuvNfBXhQ_Aup1Ye0v79ApR88")
model = genai.GenerativeModel("models/gemini-2.0-flash")


@login_required
def run_code(request):
    output = ""
    if request.method == "POST":
        form = Code_Form(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            language = form.cleaned_data["language"]
            slug = request.POST.get("slug")
            print(slug)
            user_input = form.cleaned_data.get("input", "")

            try:
                if language == 'python':
                    output = run_python(code, user_input)
                elif language == 'cpp':
                    output = run_cpp(code, user_input)
                elif language == 'java':
                    output = run_java(code, user_input)
                else:
                    output = "Unsupported language selected."
            except Exception as e:
                output = f"Error: {str(e)}"

            #Get the problem using slug to re-render problem_detail page
            problem = Problem.objects.get(slug=slug)
            return render(request, 'problem_detail.html', {
                'form': form,
               'problem': problem,
                'output': output,
            })
        else:
            output = "Invalid form submission."
    else:
        form = Code_Form()

    return render(request, 'problem_detail.html', {"form": form, "output": output})


def run_python(code,user_input):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as temp:
        temp.write(code)
        temp.flush()
        try:
            result = subprocess.run(
                ['python3', temp.name],
                input=user_input.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            stdout = result.stdout.decode()
            stderr = result.stderr.decode()

            if result.returncode != 0:
                if "SyntaxError" in stderr or "IndentationError" in stderr:
                    return f"Compilation Error:\n{stderr}"
                else:
                    return f"Runtime Error:\n{stderr}"
            print(stdout)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            return "Time Limit Exceeded"

        except MemoryError:
            return "Memory Limit Exceeded"

        except Exception as e:
            return f"Internal Error:\n{str(e)}"

        finally:
            os.remove(temp.name)
            


def run_cpp(code, user_input):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.cpp', delete=False) as source:
        source.write(code)
        source.flush()
        binary_path = source.name + ".out"
        try:
            compile_result = subprocess.run(
                ['g++', source.name, '-o', binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if compile_result.returncode != 0:
                return compile_result.stderr.decode()

            run_result = subprocess.run(
                [binary_path],
                input=user_input.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return run_result.stdout.decode() + run_result.stderr.decode()
        finally:
            os.remove(source.name)
            if os.path.exists(binary_path):
                os.remove(binary_path)

def run_java(code, user_input):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, 'Main.java')
        with open(file_path, 'w') as f:
            f.write(code)
        try:
            compile_result = subprocess.run(
                ['javac', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if compile_result.returncode != 0:
                return compile_result.stderr.decode()

            run_result = subprocess.run(
                ['java', '-cp', temp_dir, 'Main'],
                input=user_input.encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return run_result.stdout.decode() + run_result.stderr.decode()
        finally:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))


@login_required
def problem_detail(request, slug):
    # This gets the problem from the database using the slug from the URL.
    problem = get_object_or_404(Problem, slug=slug)
    form = Code_Form()

    # Render the template with the problem object
    return render(request, 'problem_detail.html', {'problem': problem,'form' : form})

def submit_code(request):
    output = ""
    verdicts = []  # To store verdicts for each test case

    if request.method == "POST":
        form = Code_Form(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            language = form.cleaned_data["language"]
            slug = request.POST.get("slug")
            problem = Problem.objects.get(slug=slug)
            testcases = problem.test_cases.all()

            for index, testcase in enumerate(testcases):
                user_input = testcase.input_data

                try:
                    # Run the code
                    if language == 'python':
                        output = run_python(code, user_input)
                    elif language == 'cpp':
                        output = run_cpp(code, user_input)
                    elif language == 'java':
                        output = run_java(code, user_input)
                    else:
                        output = "Unsupported language selected."
                    
                    # Normalize output and expected_output by stripping whitespace
                    if output.strip() == testcase.expected_output.strip():
                        verdicts.append((f"Test Case {index+1}", "Accepted", output.strip()))
                    else:
                        verdicts.append((f"Test Case {index+1}", "Wrong Answer", output.strip()))

                except subprocess.TimeoutExpired:
                    verdicts.append((f"Test Case {index+1}", "Time Limit Exceeded", "TLE"))
                except MemoryError:
                    verdicts.append((f"Test Case {index+1}", "Memory Limit Exceeded", "MLE"))
                except Exception as e:
                    verdicts.append((f"Test Case {index+1}", f"Runtime Error", str(e)))

            # Summary verdict
            if all(v[1] == "Accepted" for v in verdicts):
                summary_verdict = "All test cases Passed ✅"
            else:
                summary_verdict = "Some test cases Failed ❌"

            passed_count = sum(1 for case, result, output in verdicts if result == "Accepted")
            total_count = len(verdicts)


            Submission.objects.create(
                user=request.user,
                problem=problem,
                code=code,
                language=language,
                verdict=summary_verdict,
            )

            return render(request, 'problem_detail.html', {
                'form': form,
                'problem': problem,
                'verdicts': verdicts,
                'summary_verdict': summary_verdict,
                'passed_count': passed_count,
                'total_count': total_count,
            })
        else:
            output = "Invalid form submission."

    else:
        form = Code_Form()

    return render(request, 'problem_detail.html', {"form": form})


def ai_review(request):
    if request.method == "POST":
        form = Code_Form(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            slug = request.POST.get("slug")
            problem = Problem.objects.get(slug=slug)
            prompt = f"This is my problem desciption {problem.description} and this is my code {code} review my code and of there are any errors target them or tell me the imporvements if there are any and return and compare the time and space complexity to that of the optimal code and give me the ouput in less number of lines and give me only whats required"
            try:
                response = model.generate_content(prompt)
                output = response.text
            except Exception as e:
                return render(request, 'problem_detail.html', {
                'form': form,
                'problem': problem,
                'output' : 'Please try again',
            })
        
            return render(request, 'problem_detail.html', {
                'form': form,
                'problem': problem,
                'output' : output,
            })
        
        return render(request, 'problem_detail.html', {
                'form': form,
                'problem': problem,
                'output' : "The form is not valid",
            })
                



