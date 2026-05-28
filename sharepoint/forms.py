from django import forms
from .models import SharePointConfig

_style = 'background:#0f1422;border:1px solid #1e2333;border-radius:8px;color:#f1f5f9;padding:9px 14px;font-size:14px;width:100%;'


class SharePointConfigForm(forms.ModelForm):
    class Meta:
        model = SharePointConfig
        fields = ['url', 'folder', 'auto_sync', 'meta_sync']
        widgets = {
            'url': forms.URLInput(attrs={'placeholder': 'https://company.sharepoint.com/sites/contracts', 'style': _style}),
            'folder': forms.TextInput(attrs={'placeholder': '/Shared Documents/Contracts', 'style': _style}),
            'auto_sync': forms.CheckboxInput(attrs={'style': 'width:18px;height:18px;accent-color:#6366f1;'}),
            'meta_sync': forms.CheckboxInput(attrs={'style': 'width:18px;height:18px;accent-color:#6366f1;'}),
        }
