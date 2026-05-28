from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()
FIELD_STYLE = 'background:#0f1422;border:1px solid #1e2333;border-radius:8px;color:#f1f5f9;padding:9px 14px;font-size:14px;width:100%;'


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ["name", "email", "role"]

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'role', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'style': FIELD_STYLE}),
            'email': forms.EmailInput(attrs={'style': FIELD_STYLE}),
            'role': forms.Select(attrs={'style': FIELD_STYLE}),
            'status': forms.Select(attrs={'style': FIELD_STYLE}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.is_active = (self.cleaned_data.get('status') == 'Active')
        if commit:
            user.save()
        return user