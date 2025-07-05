from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError

# Status choices reused across models
STATUS_CHOICES = [
    ('P', 'Pending'),
    ('R', 'Running'),
    ('AC', 'Accepted'),
    ('WA', 'Wrong Answer'),
    ('TLE', 'Time Limit Exceeded'),
    ('CE', 'Compilation Error'),
    ('RE', 'Runtime Error'),
]

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard')
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Problem details
    #input_format = models.TextField(blank=True, help_text="Format of input data")
    #output_format = models.TextField(blank=True, help_text="Format of expected output")
    sample_input = models.TextField(blank=True, help_text="Sample input data")
    sample_output = models.TextField(blank=True, help_text="Sample output data")
    constraints = models.TextField(blank=True, help_text="Problem constraints")
    time_limit = models.PositiveIntegerField(default=2, help_text="Time limit in seconds")
    memory_limit = models.PositiveIntegerField(default=128, help_text="Memory limit in MB")

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while Problem.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def test_case_count(self):
        return self.test_cases.count()


class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE,
        related_name='test_cases'
    )
    input = models.TextField()
    expected_output = models.TextField()
    is_public = models.BooleanField(
        default=False,
        help_text="Show this test case to users"
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['problem', 'order']

    def clean(self):
        if self.order < 0:
            raise ValidationError("Order must be a positive integer")

    def __str__(self):
        return f"Test Case #{self.order} for {self.problem.title}"


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='P')
    
    # Background execution fields
    task_id = models.CharField(max_length=255, blank=True, null=True)
    is_finished = models.BooleanField(default=False)
    
    # Result metrics
    runtime = models.PositiveIntegerField(null=True, blank=True)  # in milliseconds
    memory = models.PositiveIntegerField(null=True, blank=True)   # in KB
    passed_test_cases = models.PositiveIntegerField(default=0)
    total_test_cases = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Submission #{self.id} for {self.problem.title} by {self.user.username}"

    def update_status(self):
        """Update overall status based on test case results"""
        if self.status == 'CE':  # Compilation error affects all tests
            return
            
        results = self.test_case_results.all()
        if not results.exists():
            return
            
        # Get worst-case status priority
        status_priority = {'RE': 1, 'TLE': 2, 'WA': 3, 'AC': 4}
        current_priority = 0
        worst_status = 'AC'

        for result in results:
            if result.status == 'AC':
                continue
                
            # Handle running/pending submissions
            if result.status in ['P', 'R']:
                self.status = 'R'
                self.save()
                return
                
            # Determine worst status
            priority = status_priority.get(result.status, 0)
            if priority > current_priority:
                current_priority = priority
                worst_status = result.status

        self.status = worst_status
        self.save()


class TestCaseResult(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='test_case_results'
    )
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='P')
    runtime = models.PositiveIntegerField(null=True, blank=True)  # in milliseconds
    memory = models.PositiveIntegerField(null=True, blank=True)   # in KB
    output = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['submission', 'test_case']

    def __str__(self):
        return f"Result for TC #{self.test_case_id} on Submission #{self.submission_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent submission status when result changes
        self.submission.update_status()