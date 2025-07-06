from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Problem
from .forms import Code_Form
from django.db.models import Q

@login_required
def problem_list(request):
    query = request.GET.get('q')  # Get the search query from the URL (?q=...)

    if query:
        problems = Problem.objects.filter(
            Q(title__icontains=query) |
            Q(tags__icontains=query) |
            Q(difficulty__icontains=query)
        ).order_by('-created_at')
    else:
        problems = Problem.objects.all().order_by('title')  # Default ordering

    return render(request, 'compiler/problem_list.html', {
        'problems': problems,
        'query': query,  # So the input box can stay filled with last search
    })


@login_required
def problem_detail(request, slug):
    # This gets the problem from the database using the slug from the URL.
    problem = get_object_or_404(Problem, slug=slug)
    form = Code_Form()

    # Render the template with the problem object
    return render(request, 'compiler/problem_detail.html', {'problem': problem,'form' : form})
    




