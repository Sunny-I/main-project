from django.db import models

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]


class CodeSubmission(models.Model):
    input = models.TextField()
    launguage = models.CharField(choices=LANGUAGE_CHOICES)
    output = models.TextField(blank=True,null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.language} @ {self.timestamp}'
    