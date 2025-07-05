from django import forms

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]

class Code_Form(forms.Form):
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
    code = forms.CharField(widget=forms.Textarea(attrs={'rows' : 15, 'cols' : 50}))
    input = forms.CharField(widget=forms.Textarea(attrs={'rows' : 15, 'cols' : 50}))
    
