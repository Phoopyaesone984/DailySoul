# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import JournalEntry

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Choose a username",
            "class": "input",
            "autocomplete": "username",
            "required": True
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com (optional)",
            "class": "input",
            "autocomplete": "email"
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create a password",
            "class": "input pw-input",
            "autocomplete": "new-password"
        })
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm your password",
            "class": "input pw-input",
            "autocomplete": "new-password"
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = User.objects.filter(email__iexact=email)
            if qs.exists():
                raise forms.ValidationError("An account with this email already exists.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Username",
        "class": "input",
        "autocomplete": "username",
        "required": True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "placeholder": "Password",
        "class": "input pw-input",
        "autocomplete": "current-password",
        "required": True
    }))


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Entry title...', 'class': 'form-input'}),
            'content': forms.Textarea(attrs={'placeholder': 'Write your thoughts...', 'class': 'form-textarea', 'rows': 6}),
        }
