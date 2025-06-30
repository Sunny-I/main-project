from django.shortcuts import get_object_or_404, render
from .models import Problem

def problems_list(request):
    problems = Problem.objects.all().order_by('id')  
    return render(request, 'problems/problems_list.html', {'problems': problems})

def problem_detail(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    return render(request, 'problems/problem.html', {'problem': problem})


