from django import forms
from .models import Contract


ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'tiff'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class QuickUploadForm(forms.Form):
    """Step 1 — user provides just a document hint name and the file."""
    contract_hint = forms.CharField(
        required=False,
        label='Contract Name (optional hint)',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Microsoft Enterprise Agreement — or leave blank'}),
    )
    file = forms.FileField(
        label='Contract Document',
        widget=forms.ClearableFileInput(),
    )

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            ext = f.name.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    'Unsupported file type. Allowed: PDF, DOCX, DOC, JPG, PNG, TIFF.'
                )
            if f.size > MAX_FILE_SIZE:
                raise forms.ValidationError('File too large. Maximum size is 20 MB.')
        return f


class WorkbenchConfirmForm(forms.ModelForm):
    """Step 2 — pre-filled from AI extraction, user can edit before saving."""
    class Meta:
        model = Contract
        fields = ['name', 'vendor', 'expiry', 'risk', 'version', 'status', 'clauses']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contract name'}),
            'vendor': forms.TextInput(attrs={'placeholder': 'Vendor / party name'}),
            'expiry': forms.DateInput(attrs={'type': 'date'}),
            'risk': forms.Select(),
            'version': forms.TextInput(attrs={'placeholder': 'e.g. v1.0'}),
            'status': forms.Select(),
            'clauses': forms.NumberInput(attrs={'min': '0', 'placeholder': '0'}),
        }
