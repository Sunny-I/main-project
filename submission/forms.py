from django import forms
from .models import LANGUAGE_CHOICES

class CodeForm(forms.Form):
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
    code = forms.CharField(widget=forms.Textarea(attrs={'rows': 25, 'cols': 100}))
