from django import forms

GENDER = {
    "M": "Male",
    "F": "Female",
    "O": "Other",
}

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput, max_length=255)
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    gender = forms.ChoiceField(widget=forms.RadioSelect, choices=GENDER)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    img = forms.FileField(widget=forms.ClearableFileInput(attrs={"type": "file"}), required=False)

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput, max_length=255)

class GameLinkForm(forms.Form):
    game_title = forms.CharField(max_length=100)
    game_username = forms.CharField(max_length=100)
    external_player_id = forms.CharField(max_length=100)    