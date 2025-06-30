from django.shortcuts import render
from .forms import CodeForm
import subprocess
import tempfile

def run_code(language, code):
    with tempfile.NamedTemporaryFile(delete=False, suffix={
        'python': '.py',
        'cpp': '.cpp',
        'java': '.java'
    }[language]) as temp:
        temp.write(code.encode())
        temp.flush()
        temp_name = temp.name

    try:
        if language == 'python':
            result = subprocess.run(['python3', temp_name], capture_output=True, text=True, timeout=5)
        elif language == 'cpp':
            executable = temp_name.replace('.cpp', '')
            compile = subprocess.run(['g++', temp_name, '-o', executable], capture_output=True, text=True)
            if compile.returncode != 0:
                return compile.stderr
            result = subprocess.run([executable], capture_output=True, text=True, timeout=5)
        elif language == 'java':
            compile = subprocess.run(['javac', temp_name], capture_output=True, text=True)
            if compile.returncode != 0:
                return compile.stderr
            classname = temp_name.split('/')[-1].replace('.java', '')
            result = subprocess.run(['java', '-cp', '/tmp', classname], capture_output=True, text=True, timeout=5)
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

def compiler_view(request):
    output = ''
    if request.method == 'POST':
        form = CodeForm(request.POST)
        if form.is_valid():
            language = form.cleaned_data['language']
            code = form.cleaned_data['code']
            output = run_code(language, code)
    else:
        form = CodeForm()
    return render(request, 'submission/submission.html', {'form': form, 'output': output})


