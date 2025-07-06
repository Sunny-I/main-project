from django.shortcuts import get_object_or_404, render
from submissions.models import Submission
from django.db.models import Q

def my_submissions(request):
    query = request.GET.get('q', '')
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    if query:
        submissions = submissions.filter(
            Q(problem__title__icontains=query) |
            Q(verdict__icontains=query) |
            Q(language__icontains=query)
        )

    submissions = submissions.order_by('-submitted_at')
    return render(request, 'my_submissions.html', {'submissions': submissions,'query': query,})

def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    problem = submission.problem
    print(submission.problem.slug)
    return render(request, 'submission_detail.html', {
        'submission': submission,
        'problem': problem,
    })




