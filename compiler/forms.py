from django import forms
from .models import TestCase
from .models import Problem, LANGUAGE_CHOICES

class CodeForm(forms.Form):
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        initial='python',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': 'Select programming language',
            'x-model': 'language'  # For integration with Alpine.js
        })
    )
    code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control code-textarea',
            'rows': 15,
            'spellcheck': 'false',
            'placeholder': 'Write your solution here...',
            'x-data': 'codeEditor',
            '@keydown': 'handleTab($event)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop('problem', None)
        super().__init__(*args, **kwargs)
        
       
        
        # Add problem ID as hidden field
        self.fields['problem_id'] = forms.CharField(
            initial=self.problem.id if self.problem else None,
            widget=forms.HiddenInput(),
            required=False
        )

class InputForm(forms.Form):
    stdin = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control code-textarea',
            'rows': 5,
            'placeholder': 'Enter custom test input here...',
            'spellcheck': 'false',
            'x-model': 'customInput'  # For integration with Alpine.js
        })
    )
    run_mode = forms.ChoiceField(
        choices=[
            ('test', 'Run against sample test cases'),
            ('custom', 'Run with custom input')
        ],
        initial='test',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'x-model': 'runMode'
        })
    )

class SubmitSolutionForm(CodeForm):
    """Extended form for final solution submission"""
    agree_terms = forms.BooleanField(
        required=True,
        label='I confirm this is my original work',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': 'required'
        })
    )
    debug_mode = forms.BooleanField(
        required=False,
        label='Enable detailed debugging',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Show detailed execution logs (for debugging)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make code field required for final submission
        self.fields['code'].required = True
        # Add honeypot field
        self.fields['website'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
            label='Leave blank if you are human'
        )

class TestCaseForm(forms.ModelForm):
    """Form for creating/editing test cases (admin use)"""
    class Meta:
        model = TestCase
        fields = ['problem', 'order', 'input', 'expected_output', 'is_public']
        widgets = {
            'input': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'expected_output': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Validate input/output format
        input_data = cleaned_data.get('input', '')
        output_data = cleaned_data.get('expected_output', '')
        
        if not input_data.strip():
            raise forms.ValidationError("Input cannot be empty")
            
        if not output_data.strip():
            raise forms.ValidationError("Expected output cannot be empty")
        
        return cleaned_data