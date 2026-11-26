# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: forms.py
# Purpose: Code for form classes
#
#
# List of form fields: https://docs.djangoproject.com/en/6.1/ref/forms/fields/#django.forms.CharField
# List of widgets: https://docs.djangoproject.com/en/6.1/ref/forms/widgets/
# Reference for how choices in the ChoiceField work: https://docs.djangoproject.com/en/6.1/ref/models/fields/#field-choices.

# List of important modules
from django import forms
from django.contrib.auth import get_user_model

from matchMaker.tournamentFactory.doubleElim import DoubleElimination
from matchMaker.tournamentFactory.pools import Pools
from matchMaker.tournamentFactory.singleElim import SingleElimination
from .models import Tournament, Member, TournamentRegistration 
from .ranks.helpers import GAME_TITLE_CHOICES, RANK_CHOICES, rank_choices_for_game, VALORANT_REGIONS, LEAGUE_REGIONS

# list of values for Gender option
GENDER = {
    "M": "Male",
    "F": "Female",
    "O": "Other",
}

# form for registering new users
class RegisterForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput, max_length=255)
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    gender = forms.ChoiceField(widget=forms.RadioSelect, choices=GENDER)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    img = forms.FileField(widget=forms.ClearableFileInput(attrs={"type": "file"}), required=False)

    # error message if username is already taken by another user
    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    # error message if password violates length policy
    def clean_password(self):
        password = self.cleaned_data["password"]
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        return password

# form for logging users in
class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput, max_length=255)

# form for registering new users with the additional information
class MemberProfileForm(forms.Form):
    firstname = forms.CharField(max_length=255, label="First name")
    lastname = forms.CharField(max_length=255, label="Last name")
    gender = forms.ChoiceField(choices=GENDER)
    DOB = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

# form for registering game accounts
class GameLinkForm(forms.Form):
    game_title = forms.ChoiceField(choices=GAME_TITLE_CHOICES, label="Game")
    other_game_title = forms.CharField(max_length=100, required=False, label="Other game name")
    game_username = forms.CharField(max_length=100, label="Game account name")
    game_tag = forms.CharField(max_length=100, required=False, label="Riot tag")
    external_player_id = forms.CharField(max_length=100, required=False, label="External player ID")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("game_title") in ("Valorant", "League of Legends"):
            if not cleaned_data.get("game_tag"):
                self.add_error("game_tag", "Enter your Riot tag.")
            if "#" in cleaned_data.get("game_tag", ""):
                self.add_error("game_tag", "Enter your tag without #.")
            if cleaned_data.get("game_title") == "Valorant":
                if not cleaned_data.get("external_player_id") or cleaned_data.get("external_player_id") not in VALORANT_REGIONS:
                    self.add_error("external_player_id", "Choose a valid region.")
            if cleaned_data.get("game_title") == "League of Legends":
                if not cleaned_data.get("external_player_id") or cleaned_data.get("external_player_id") not in LEAGUE_REGIONS:
                    self.add_error("external_player_id", "Choose a valid region.")
        else:
            cleaned_data["game_tag"] = ""
        if cleaned_data.get("game_title") != "OTHER":
            return cleaned_data
        # Custom games require a name
        if cleaned_data.get("other_game_title"):
            cleaned_data["game_title"] = cleaned_data.get("other_game_title")
        else:
            self.add_error("other_game_title", "Enter the name of the game.")
        cleaned_data["external_player_id"] = ""
        return cleaned_data

# flist of options for solo or team-based tournaments
ENTRY_TYPE = {
    "SOLO": "Solo (individuals)",
    "TEAM": "Team",
}
FORMAT = {
    "SINGLE_ELIM": "Single Elimination",
    "DOUBLE_ELIM": "Double Elimination",
    "POOLS": "Pools"
}

class TournamentRankFormBase(forms.Form):
    # Base form for tournament rank constraints, shared by TournamentCreation and ManageTournament
    rank_options_by_game = RANK_CHOICES

    game_title = forms.ChoiceField(choices=GAME_TITLE_CHOICES, initial="Deadlock")
    other_game_title = forms.CharField(max_length=100, required=False,)
    min_rank = forms.CharField(required=False, widget=forms.Select)
    max_rank = forms.CharField(required=False, widget=forms.Select)

    def clean(self):
        cleaned_data = super().clean()
        #check that if other that it has a title 
        if cleaned_data.get("game_title") == "OTHER":
            other_title = cleaned_data.get("other_game_title", "").strip()
            if not other_title:
                self.add_error("other_game_title", "Enter the name of the game.")
            else:
                cleaned_data["game_title"] = other_title
            # other games don't need min or max rank
            cleaned_data["min_rank"] = ""
            cleaned_data["max_rank"] = ""
        else:
            #games with ranks do not need other game title
            cleaned_data["other_game_title"] = ""

        minimum = cleaned_data.get("min_rank")
        maximum = cleaned_data.get("max_rank")
        game_title = cleaned_data.get("game_title")
        # data gets stored as value string, label string pairs and we use the ints for the data
        valid_values = { value for value, _ in rank_choices_for_game(game_title)}
        # check min and max rank validity
        if minimum and minimum not in valid_values:
            self.add_error("min_rank", "Choose a rank for this game.")
        if maximum and maximum not in valid_values:
            self.add_error("max_rank", "Choose a rank for this game.")
        # check if min rank is greater than max 
        if minimum and maximum and minimum in valid_values and maximum in valid_values:
            if int(minimum) > int(maximum):
                self.add_error("max_rank", "Maximum rank must be at least the minimum rank.")
        return cleaned_data


# append the rank form base to the start of the tournament creation
class TournamentCreation(TournamentRankFormBase):
    tournament_name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    entry_type = forms.ChoiceField(widget=forms.RadioSelect, choices=ENTRY_TYPE)
    format = forms.ChoiceField(widget=forms.Select, choices=FORMAT)
    max_participants = forms.IntegerField(max_value=16)
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

# form for submitting scores
class ScoreSubmissionForm(forms.Form):
    player1_score = forms.IntegerField(min_value=0)
    player2_score = forms.IntegerField(min_value=0)
    roundVal = forms.IntegerField(initial=-1, required=False, label="", widget=forms.HiddenInput())
    matchVal = forms.IntegerField(initial=-1, required=False, label="", widget=forms.HiddenInput())
    isBracket = forms.BooleanField(initial=False, required=False, label="", widget=forms.HiddenInput())
    matchCompleted = forms.BooleanField(label="Match Completed:", required=False)

    def __init__(self, *args, **kwargs):
        self.matchId = kwargs.pop('match_id', None)
        self.roundId = kwargs.pop('round_id', None)
        self.isBracket = kwargs.pop('is_bracket', None)
        self.tid = kwargs.pop('tid', None)
        super().__init__(*args, **kwargs)
        #Grab tournament info to populate labels with user names.

        if(self.tid):
            tournament = Tournament.objects.get(id=self.tid)
            format = tournament.format
            match format:
                case "SINGLE_ELIM":
                    tournament = SingleElimination(self.tid)
                case "DOUBLE_ELIM":
                    tournament = DoubleElimination(self.tid)
                case "POOLS":
                    tournament = Pools(self.tid)
            bracketBool = True if self.isBracket == "True" else False
            userids = tournament.getPlayerMatchIds(int(self.roundId), int(self.matchId), bracketBool)
            self.fields['player1_score'].label = (("Null Player's Score") if userids[0] <= 0 else 
                                                (f"{Member.objects.get(id=userids[0]).user.username}'s Score:"))
            self.fields['player2_score'].label = (("Null Player's Score") if userids[1] <= 0 else 
                                                (f"{Member.objects.get(id=userids[1]).user.username}'s Score:"))

        #Set the other values in the hidden inputs so they can be passed along after the score gets submitted
        self.fields['roundVal'].initial = self.roundId
        self.fields['matchVal'].initial = self.matchId
        self.fields['isBracket'].initial = self.isBracket

# form for creating teams
class CreateTeamForm(forms.Form):
    name = forms.CharField(max_length=100)
    tag = forms.CharField(max_length=100, required=False)

# form for managing tournament, append form base to top of manage tournament
class ManageTournament(TournamentRankFormBase):
    participants = forms.ModelMultipleChoiceField(
        queryset=Member.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    tournament_name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    entry_type = forms.ChoiceField(widget=forms.RadioSelect, choices=ENTRY_TYPE)
    format = forms.ChoiceField(widget=forms.Select, choices=FORMAT)
    max_participants = forms.IntegerField(max_value=16)
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))