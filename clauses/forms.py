from django import forms
from .models import Clause


class ClauseForm(forms.ModelForm):
    class Meta:
        model = Clause
        fields = [
            'id', 'name', 'category', 'risk_level', 'version', 'status', 'document',
            'mandatory', 'standard_rule', 'restricted_terms', 'deviation_rule',
            'ai_recommendation', 'escalation_required', 'clause_category', 'clause_name',
        ]
        widgets = {
            'id': forms.TextInput(attrs={'placeholder': 'e.g. CL-010', 'class': 'clause-form-input'}),
            'name': forms.TextInput(attrs={'placeholder': 'Clause name', 'class': 'clause-form-input'}),
            'category': forms.Select(attrs={'class': 'clause-form-input'}),
            'risk_level': forms.Select(attrs={'class': 'clause-form-input'}),
            'version': forms.TextInput(attrs={'placeholder': 'v1.0', 'class': 'clause-form-input'}),
            'status': forms.Select(attrs={'class': 'clause-form-input'}),
            'document': forms.ClearableFileInput(attrs={'class': 'clause-form-input clause-form-file'}),
            'mandatory': forms.Select(attrs={'class': 'clause-form-input'}, choices=[(True, 'Yes'), (False, 'No')]),
            'standard_rule': forms.Textarea(attrs={'class': 'clause-form-input', 'rows': 3, 'placeholder': 'Standard clause text or value'}),
            'restricted_terms': forms.Textarea(attrs={'class': 'clause-form-input', 'rows': 3, 'placeholder': 'Restricted terms / conditions'}),
            'deviation_rule': forms.Textarea(attrs={'class': 'clause-form-input', 'rows': 3, 'placeholder': 'Deviation handling rule'}),
            'ai_recommendation': forms.Textarea(attrs={'class': 'clause-form-input', 'rows': 3, 'placeholder': 'AI recommendation for this clause'}),
            'escalation_required': forms.Select(attrs={'class': 'clause-form-input'}, choices=[(True, 'Yes'), (False, 'No')]),
            'clause_category': forms.Select(attrs={'class': 'clause-form-input'}),
            'clause_name': forms.TextInput(attrs={'placeholder': 'Display clause name', 'class': 'clause-form-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        if self.is_edit:
            self.fields['id'].widget.attrs['readonly'] = True


class UploadClauseFileForm(forms.Form):
    file = forms.FileField(
        label='Clause Document',
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'clause-form-input clause-form-file'
            }
        ),
    )
