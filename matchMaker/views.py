from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Member
from .models import Tournament
from datetime import datetime
from .forms import RegisterForm, LoginForm, GameLinkForm, TournamentCreation, ScoreSubmissionForm, ManageTournament
from .tournamentFactory.singleElim import SingleElimination
from .tournamentFactory.tournamentCreate import TournamentCreate

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
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/homePage/')
            else:
                form.add_error(None, "Invalid username or password.")

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
    scoreSubmittable = False
    #This POST request is from the score submission popup.
    if(request.method == "POST"):
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            tournament = SingleElimination(12)
            #TODO: Modify updateScore parameters to submit proper round and match ids 
            #   based on user accessing webpage (i.e. cookies for user).
            tournament.updateScore(form.cleaned_data['roundVal'], form.cleaned_data['matchVal'], 
                            [form.cleaned_data['player1_score'], form.cleaned_data['player2_score']])
            if form.cleaned_data['matchCompleted']:
                if not tournament.determineWinner(form.cleaned_data['roundVal'], form.cleaned_data['matchVal']):
                    #TODO: HTTP error for invalid submission
                    return
            return redirect(request.path)
    tournament = SingleElimination(tid)
    if(request.user.is_authenticated):
        userPos = tournament.findUserInBracket(request.user.id)
        scoreSubmittable = (userPos != None) and not tournament.IsMatchComplete(userPos["round_id"], userPos["match_id"])
        return render(request, 'tournament.html', {'tournament': tournament, 'score_submittable': scoreSubmittable,
                                                       'round': userPos["round_id"], 'match': userPos["match_id"] } )
    return render(request, 'tournament.html', {'tournament': tournament, 'score_submittable': scoreSubmittable})

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
    return render(request, 'manageTournament.html', {'form': form})

def homePage(request):
  template = loader.get_template('homepage.html')
  return HttpResponse(template.render())

def logoutHandler(request):
    if(request.user.is_authenticated):
        logout(request)
    return HttpResponseRedirect('/homePage/')

def profilePage(request):
    template = loader.get_template('profile.html')
    return HttpResponse(template.render())

def scorePopup(request):
    if(request.method == "GET"):
        print(request.GET.get('roundId'))
        print(request.GET.get('matchId'))
        form = ScoreSubmissionForm(round_id=request.GET.get('roundId'), match_id=request.GET.get('matchId'))
        return render(request, 'modules/scoreSubmission.html', {'form': form})

def manageTournament(request, tid):
    tournament = Tournament.objects.get(id=tid)
    if request.method == "POST":
            # create a form instance and populate it with data from the request:
            form = ManageTournament(request.POST)
            # check whether it's valid:
            if form.is_valid():
                data = form.cleaned_data

                tournament.name=data["tournament_name"]
                tournament.description=data["description"]
                tournament.game_title = data["game_title"]
                min_rank = data["min_rank"]
                max_rank = data["max_rank"]
                max_participants = data["max_participants"]
                start_date = data["start_date"]

                participants= data["participants"]
                if len(participants) == max_participants:
                    player_ids = list(participants.values_list('id', flat=True))
                    tournament.layout = TournamentCreate(tournament.name, tournament.description, 
                                                         player_ids, tournament.game_title).layout

                tournament.save()
            # redirect to a newly updated tournament URL:
            return HttpResponseRedirect(f'/tournament/{tournament.id}/')

        # if a GET (or any other method) we'll get the tournamenet with its information
    else:
        form = ManageTournament(initial={
            "tournament_name": tournament.name,
            "description": tournament.description,
            "game_title": tournament.game_title,
            "format": tournament.format,
            "max_participants": tournament.max_participants,
            "min_rank": tournament.min_rank,
            "max_rank": tournament.max_rank,
            "start_date": tournament.start_date,
            "participants": tournament.participants.all(),
            })
    # reusing the registation html file as it's just displaying a form. 
    return render(request, 'manageTournament.html', {'form': form})

def TournamentList(request, id=1):
    pageNumber = request.GET.get('page') or 1
    tournamentList = Tournament.objects.all().order_by('id')
    paginator = Paginator(tournamentList, 10)

    try:
        page = paginator.get_page(pageNumber)
    except PageNotAnInteger:
        page = paginator.get_page(1)
    except EmptyPage:
        page = paginator.get_page(paginator.num_pages)

    return render(request, 'tournament_list.html', {'page':page})
