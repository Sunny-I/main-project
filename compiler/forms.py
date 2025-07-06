from django import forms

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]

class Code_Form(forms.Form):
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select language-selector',
            'style': 'width: 200px; height: 40px; font-size: 14px; margin-bottom: 10px;'
        })
    )
    
    code = forms.CharField(
        label='Code Editor',
        widget=forms.Textarea(attrs={
            'rows': 25,
            'cols': 80,
            'class': 'form-control code-editor',
            'placeholder': 'Write your code here...',
            'style': '''
                font-family: 'Fira Code, Consolas, Monaco, monospace;'
                font-size: 14px;
                line-height: 1.5;
                border: 2px solid #007bff;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
                resize: vertical;
            '''
        })
    )
    
    input = forms.CharField(
        label='Input (Optional)',
        widget=forms.Textarea(attrs={
            'rows': 8,
            'cols': 80,
            'class': 'form-control input-area',
            'placeholder': 'Enter input for your program (if needed)...',
            'style': '''
                font-family: 'Fira Code, Consolas, Monaco, monospace;'
                font-size: 13px;
                line-height: 1.4;
                border: 2px solid #28a745;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
                resize: vertical;
            '''
        }),
        required=False
    )
    
    class Media:
        css = {
            'all': ('css/compiler.css',)
        }
        js = ('js/compiler.js',)