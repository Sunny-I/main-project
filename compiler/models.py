from django.db import models


class Submission(models.Model):
   LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('cpp', 'C++'),
        ('java', 'Java'),
    ]
   
   code = models.TextField()
   language = models.CharField(max_length=15,choices=LANGUAGE_CHOICES)
   input = models.CharField(null=True,blank=True)
   output = models.CharField(null=True,blank=True)
   created_at = models.DateTimeField(auto_now_add=True)




