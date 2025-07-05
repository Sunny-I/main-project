import os
import subprocess
import tempfile
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Problem, Submission, TestCase, TestCaseResult
from .forms import CodeForm, InputForm

# ========================
# VIEW FUNCTIONS
# ========================

@login_required
def problem_list(request):
    """Display list of all problems"""
    problems = Problem.objects.all()
    return render(request, 'compiler/problem_list.html', {'problems': problems})

@login_required
def problem_detail(request, slug):
    """Display problem detail with editor and submission history"""
    problem = get_object_or_404(Problem, slug=slug)
    
    # Get user submissions for this problem
    submissions = Submission.objects.filter(
        problem=problem,
        user=request.user
    ).order_by('-submitted_at')[:5]  # Last 5 submissions
    
    # Forms for code submission
    code_form = CodeForm()
    input_form = InputForm()
    
    context = {
        'problem': problem,
        'submissions': submissions,  # Changed from 'user_submissions'
        'code_form': code_form,
        'input_form': input_form,
    }
    return render(request, 'compiler/problem_detail.html', context)

@login_required
def submit_code(request, problem_id):
    """Handle code submission and execute against test cases"""
    problem = get_object_or_404(Problem, id=problem_id)
    code = request.POST.get('code')
    language = request.POST.get('language')
    custom_input = request.POST.get('stdin', '')
    
    # Create submission
    submission = Submission.objects.create(
        user=request.user,
        problem=problem,
        code=code,
        language=language,
        status='P'  # Pending
    )
    
    # Get test cases for this problem
    test_cases = TestCase.objects.filter(problem=problem).order_by('order')
    
    if custom_input:
        # Execute with custom input (single test)
        result = execute_single_test(submission, custom_input, problem.time_limit)
        response_data = format_single_result(result)
    else:
        # Execute against all test cases
        results = execute_test_cases(submission, test_cases, problem.time_limit)
        response_data = process_test_results(submission, results)
    
    return JsonResponse({
        'status': 'success',
        'message': 'Submission received!',
        'submission_id': submission.id
    })

@login_required
def submission_detail(request, submission_id):
    """Show detailed results for a specific submission"""
    submission = get_object_or_404(
        Submission.objects.select_related('problem', 'user'),
        id=submission_id,
        user=request.user
    )
    
    # Get test results for this submission
    test_results = TestCaseResult.objects.filter(
        submission=submission
    ).select_related('test_case')
    
    return render(request, 'compiler/submission_detail.html', {
        'submission': submission,
        'problem': submission.problem,
        'test_results': test_results
    })

@login_required
def user_submissions(request):
    """Show all submissions for the current user"""
    submissions = Submission.objects.filter(
        user=request.user
    ).select_related('problem').order_by('-submitted_at')
    
    return render(request, 'compiler/submission_detail.html', {
        'submissions': submissions
    })

# ========================
# EXECUTION FUNCTIONS
# ========================

def execute_single_test(submission, input_data, timeout):
    """Execute code with custom input (not against test cases)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare execution environment
        setup_result = prepare_execution_environment(submission, tmpdir)
        if 'error' in setup_result:
            return setup_result
        
        # Run the test
        return run_test_case(
            setup_result['cmd'], 
            input_data, 
            timeout,
            expected_output=None  # No validation for custom input
        )

def execute_test_cases(submission, test_cases, timeout):
    """Execute code against all test cases"""
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare execution environment
        setup_result = prepare_execution_environment(submission, tmpdir)
        if 'error' in setup_result:
            # If compilation failed, return error for all test cases
            return [{
                **setup_result,
                'test_case': test_case
            } for test_case in test_cases]
        
        # Execute against each test case
        for test_case in test_cases:
            result = run_test_case(
                setup_result['cmd'], 
                test_case.input, 
                timeout,
                test_case.expected_output
            )
            results.append({
                'test_case': test_case,
                **result
            })
    
    return results

def prepare_execution_environment(submission, tmpdir):
    """Prepare code for execution (write to file, compile if needed)"""
    # Get file extension based on language
    ext = {
        'python': 'py',
        'cpp': 'cpp',
        'java': 'java'
    }.get(submission.language, 'txt')
    
    # Write code to file
    filename = f"submission.{ext}"
    filepath = os.path.join(tmpdir, filename)
    
    try:
        with open(filepath, 'w') as f:
            f.write(submission.code)
    except Exception as e:
        return {
            'output': '',
            'error': f"File write error: {str(e)}",
            'runtime': 0,
            'status': 'CE'
        }
    
    # Handle language-specific compilation
    if submission.language == 'cpp':
        return compile_cpp(filepath, tmpdir)
    elif submission.language == 'java':
        return compile_java(filepath, tmpdir)
    else:  # Python doesn't need compilation
        return {
            'cmd': ['python3', filepath],
            'executable': filepath
        }

def compile_cpp(filepath, tmpdir):
    """Compile C++ code and return execution command"""
    executable = os.path.join(tmpdir, 'a.out')
    compile_proc = subprocess.run(
        ['g++', filepath, '-o', executable],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if compile_proc.returncode != 0:
        return {
            'output': '',
            'error': compile_proc.stderr.decode(),
            'runtime': 0,
            'status': 'CE'
        }
    return {
        'cmd': [executable],
        'executable': executable
    }

def compile_java(filepath, tmpdir):
    """Compile Java code and return execution command"""
    # Java requires class name to match filename
    classname = "Main"
    javafile = os.path.join(tmpdir, f"{classname}.java")
    os.rename(filepath, javafile)
    
    # Compile Java code
    compile_proc = subprocess.run(
        ['javac', javafile],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmpdir
    )
    if compile_proc.returncode != 0:
        return {
            'output': '',
            'error': compile_proc.stderr.decode(),
            'runtime': 0,
            'status': 'CE'
        }
    return {
        'cmd': ['java', '-cp', tmpdir, classname],
        'executable': javafile
    }

def run_test_case(cmd, input_data, timeout, expected_output=None):
    """Execute code with given input and return results"""
    try:
        start_time = time.time()
        process = subprocess.run(
            cmd,
            input=input_data.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        runtime = (time.time() - start_time) * 1000  # ms
        
        output = process.stdout.decode()
        error = process.stderr.decode()
        status = 'AC' if process.returncode == 0 else 'RE'
        
        # Validate output if expected output is provided
        if expected_output and status == 'AC':
            actual_output = output.strip().replace('\r\n', '\n')
            expected_output = expected_output.strip().replace('\r\n', '\n')
            
            if actual_output != expected_output:
                status = 'WA'
        
        return {
            'output': output,
            'error': error,
            'runtime': runtime,
            'status': status
        }
        
    except subprocess.TimeoutExpired:
        return {
            'output': '',
            'error': 'Time Limit Exceeded',
            'runtime': timeout * 1000,
            'status': 'TLE'
        }
    except Exception as e:
        return {
            'output': '',
            'error': str(e),
            'runtime': 0,
            'status': 'RE'
        }

# ========================
# RESULT PROCESSING
# ========================

def format_single_result(result):
    """Format result for custom input execution"""
    return {
        'status': result['status'],
        'output': result['output'],
        'error': result['error'],
        'runtime': result['runtime'],
        'is_custom': True
    }

def process_test_results(submission, results):
    """Process results from test case execution and save to DB"""
    # Calculate overall verdict
    verdicts = [r['status'] for r in results]
    
    # Determine final verdict based on priority
    if 'CE' in verdicts:
        final_verdict = 'CE'
    elif 'TLE' in verdicts:
        final_verdict = 'TLE'
    elif 'RE' in verdicts:
        final_verdict = 'RE'
    elif 'WA' in verdicts:
        final_verdict = 'WA'
    else:
        final_verdict = 'AC'
    
    # Calculate