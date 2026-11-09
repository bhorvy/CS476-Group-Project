from django import forms
from django.contrib.auth import get_user_model
from .models import Tournament, Member, Team 
from django.utils import timezone

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

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        return password

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput, max_length=255)

class GameLinkForm(forms.Form):
    game_title = forms.CharField(max_length=100)
    game_username = forms.CharField(max_length=100)
    external_player_id = forms.CharField(max_length=100)    

ENTRY_TYPE = {
    "SOLO": "Solo (individuals)",
    "TEAM": "Team",
}

class TournamentCreation(forms.Form):
    tournament_name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    game_title = forms.CharField(max_length=255)
    entry_type = forms.ChoiceField(widget=forms.RadioSelect, choices=ENTRY_TYPE)
    max_participants = forms.IntegerField(max_value=16)
    min_rank = forms.CharField(max_length=255) # change this once we implement game ranks 
    max_rank = forms.CharField(max_length=255) # change this once we implement game ranks
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

class ScoreSubmissionForm(forms.Form):
    player1_score = forms.IntegerField(min_value=0)
    player2_score = forms.IntegerField(min_value=0)
    roundVal = forms.IntegerField(initial=-1, required=False, label="", widget=forms.HiddenInput())
    matchVal = forms.IntegerField(initial=-1, required=False, label="", widget=forms.HiddenInput())
    matchCompleted = forms.BooleanField(label="Match Completed:", required=False)

    def __init__(self, *args, **kwargs):
        self.matchId = kwargs.pop('match_id', None)
        self.roundId = kwargs.pop('round_id', None)
        super().__init__(*args, **kwargs)
        self.fields['roundVal'].initial = self.roundId
        self.fields['matchVal'].initial = self.matchId


class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=100)
    tag = forms.CharField(max_length=100, required=False)

class ManageTournament(forms.Form):
    participants = forms.ModelMultipleChoiceField(
        queryset=Member.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    tournament_name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    game_title = forms.CharField(max_length=255)
    entry_type = forms.ChoiceField(widget=forms.RadioSelect, choices=ENTRY_TYPE)
    max_participants = forms.IntegerField(max_value=16)
    min_rank = forms.CharField(max_length=255) # change this once we implement game ranks 
    max_rank = forms.CharField(max_length=255) # change this once we implement game ranks
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    