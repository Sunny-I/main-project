from django.shortcuts import render
import subprocess
import tempfile
import os
from django.shortcuts import render

def run_code(request):
    output=""
    if request.method == "POST":
        language = request.POST.get("language")
        code = request.POST.get("code")
        user_input = request.POST.get("input" , "")

        try :
            if language == 'python':
                output = run_python(code,user_input)
            elif language == 'cpp':
                output = run_cpp(code,user_input)
            elif language == 'java':
                output = run_java(code,user_input)
            else:
                output = "Unsupported language selected."
        except Exception as e: # used to show the error message
            output = f"Error:{str(e)}"

    return render(request,'compiler.html',{"output": output})

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
            return result.stdout.decode() + result.stderr.decode()
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



    