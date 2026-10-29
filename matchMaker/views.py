from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Member
from .models import Tournament
from datetime import datetime
from .forms import RegisterForm, LoginForm, GameLinkForm, TournamentCreation, ScoreSubmissionForm
from .tournament import TournamentInstance, Scoring

def matchMaker(request):
  template = loader.get_template('demo.html')
  return HttpResponse(template.render())

def signUpPage(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            User = get_user_model()
            data = form.cleaned_data

            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
            )

            Member.objects.create(
                user=user,
                firstname=data["first_name"],
                lastname=data["last_name"],
                gender=data["gender"],
                DOB=data["date_of_birth"],
            )
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/loginPage/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def loginPage(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/homePage/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def gameAccount(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = GameLinkForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/homePage/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = GameLinkForm()

    return render(request, 'gameacc.html', {'form': form})

def tournamentPage(request, tid):
    if(request.method == "POST"):
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            obj = Scoring(tid)
            obj.updateScore(0,2, [form.cleaned_data['player1_score'], form.cleaned_data['player2_score']])
            print(form.cleaned_data)
            return redirect(request.path)
    tournament = TournamentInstance(tid)
    return render(request, 'tournament.html', {'tournament': tournament})

def tournamentCreatePage(request):
    if request.method == "POST":
           # create a form instance and populate it with data from the request:
           form = TournamentCreation(request.POST)
           # check whether it's valid:
           if form.is_valid():
               data = form.cleaned_data

               tournament = Tournament.objects.create(
                   name=data["tournament_name"],
                   description=data["description"],
                   game_title = data["game_title"],
                   #generating an empty json bracket for now. Once registrations happen, then generate bracket  
                   layout = {"bracket": []},
                   status = "UPCOMING",
                   is_public = True,
                   min_rank = data["min_rank"],
                   max_rank = data["max_rank"],
                   max_participants = data["max_participants"],
                   start_date = data["start_date"],
                   created_at = datetime.now(),
               )
               # redirect to a newly created tournament URL:
               return HttpResponseRedirect(f'/tournament/{tournament.id}/')
   
       # if a GET (or any other method) we'll create a blank form
    else:
        form = TournamentCreation()
    # reusing the registation html file as it's just displaying a form. 
    return render(request, 'register.html', {'form': form})

def homePage(request):
  template = loader.get_template('homepage.html')
  return HttpResponse(template.render())

def logoutPage(request):
    template = loader.get_template('demo.html')
    return HttpResponse(template.render())

def profilePage(request):
    template = loader.get_template('profile.html')
    return HttpResponse(template.render())

def scorePopup(request):
    if(request.method == "GET"):
        form = ScoreSubmissionForm()
        return render(request, 'modules/scoreSubmission.html', {'form': form})

