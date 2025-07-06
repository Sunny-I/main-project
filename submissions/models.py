from django.db import models
from django.contrib.auth.models import User
from problem_list.models import Problem


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20)
    verdict = models.CharField(max_length=50)
    submitted_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} - {self.verdict}"

