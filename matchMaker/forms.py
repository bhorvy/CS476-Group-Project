from django import forms

GENDER = {
    "M": "Male",
    "F": "Female",
    "O": "Other",
}

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    contact_email = forms.EmailField()
    urgent = forms.BooleanField(required=False)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255)
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    gender = forms.MultipleChoiceField(widget=forms.RadioSelect, choices=GENDER)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    img = forms.FileField(widget=forms.ClearableFileInput(attrs={"type": "file"}))

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255)