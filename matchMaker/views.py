from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Member, Tournament, TournamentRegistration, Team
from datetime import datetime
from .forms import RegisterForm, LoginForm, GameLinkForm, TournamentCreation, ScoreSubmissionForm, ManageTournament, CreateTeamForm
from .tournamentFactory.singleElim import SingleElimination
from .tournamentFactory.tournamentCreate import TournamentCreate
from .observers.bracketUpdateSubject import notify_tournament_updated
from .models import TournamentNotification

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
            try:
                with transaction.atomic():
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
            except IntegrityError:
                form.add_error("username", "That username is already taken.")
            else:
                messages.success(request, "Account created. Log in to continue.")
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

def _sync_tournament_roster(tournament):
    registrations = TournamentRegistration.objects.filter(tournament=tournament)
    member_ids = list(registrations.values_list("member_id", flat=True))
    team_member_ids = list(
        Member.objects.filter(teams__tournament_registrations__tournament=tournament).values_list("id", flat=True)
    )
    tournament.participants.set(set(member_ids) | set(team_member_ids))
    tournament.current_participants = registrations.count()
    tournament.save(update_fields=["current_participants"])
    return registrations.select_related("member__user", "team").prefetch_related("team__members__user")

@never_cache
def tournamentPage(request, tid):
    tournament = SingleElimination(tid)
    scoreSubmittable = False
    #This POST request is from the score submission popup.
    if request.method == "POST" and "player1_score" in request.POST:
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            #TODO: Modify updateScore parameters to submit proper round and match ids 
            #   based on user accessing webpage (i.e. cookies for user).
            round_id = form.cleaned_data["roundVal"]
            match_id = form.cleaned_data["matchVal"]

            match = tournament.layout["bracket"][round_id][match_id]
            player_ids = [
                player["player_id"]
                for player in match ["players"]
                if player["player_id"] != 0
            ]

            members = Member.objects.filter(id__in=player_ids)

            tournament.updateScore(
                round_id,
                match_id,
                [
                    form.cleaned_data['player1_score'], 
                    form.cleaned_data['player2_score']
                ]
            )

            notify_tournament_updated(
            tournament.object,
            members,
            "Your match score was updated.",
            )
            if form.cleaned_data['matchCompleted']:
                if not tournament.determineWinner(form.cleaned_data['roundVal'], form.cleaned_data['matchVal']):
                    #TODO: HTTP error for invalid submission
                    return

            winner_id = tournament.layout["bracket"][round_id][match_id]["winner_id"]
            winner = Member.objects.filter(pk=winner_id)

            notify_tournament_updated(
            tournament.object,
            winner,
            "You advance, please refer to the bracket for your next match.",
            )       

            return redirect(request.path)

    round_id = None
    match_id = None
    already_registered = False
    user_teams = Team.objects.none()
    member = _member_or_none(request.user)
    registrations = _sync_tournament_roster(tournament.object)
    if member:
        userPos = tournament.findUserInBracket(member.id)
        if userPos is not None:
            round_id = userPos["round_id"]
            match_id = userPos["match_id"]
            scoreSubmittable = not tournament.IsMatchComplete(round_id, match_id)
        already_registered = (
            registrations.filter(member=member).exists()
            or registrations.filter(team__members=member).exists()
        )
        user_teams = member.led_teams.all()
    return render(
        request,
        "tournament.html",
        {
            "tournament": tournament,
            "score_submittable": scoreSubmittable,
            "round": round_id,
            "match": match_id,
            "registrations": registrations,
            "already_registered": already_registered,
            "user_teams": user_teams,
        },
    )

@login_required
def registerForTournament(request, tid):
    tournament = get_object_or_404(Tournament, id=tid)
    if request.method != "POST":
        return HttpResponseRedirect(f"/tournament/{tid}/")
    try:
        member = request.user.member
    except Member.DoesNotExist:
        messages.error(request, "Your account has no member profile, so you cannot register.")
        return HttpResponseRedirect(f"/tournament/{tid}/")

    already_registered = TournamentRegistration.objects.filter(
        tournament=tournament, member=member
    ).exists()
    if already_registered:
        _sync_tournament_roster(tournament)
        messages.success(request, "You are already registered for this tournament.")
        return HttpResponseRedirect(f"/tournament/{tid}/")

    team = None
    team_id = request.POST.get("team_id")
    if tournament.entry_type == Tournament.EntryType.TEAM:
        if not team_id:
            messages.error(request, "This is a team tournament. Choose a team to register.")
            return HttpResponseRedirect(f"/tournament/{tid}/")
    elif team_id:
        messages.error(request, "This is a solo tournament. Register as yourself.")
        return HttpResponseRedirect(f"/tournament/{tid}/")

    if team_id:
        team = get_object_or_404(Team, id=team_id)
        if team.leader_id != member.id:
            messages.error(request, "Only the team leader can register this team.")
            return HttpResponseRedirect(f"/tournament/{tid}/")
        if team.members.count() < 1:
            messages.error(request, "That team has no members.")
            return HttpResponseRedirect(f"/tournament/{tid}/")
        if TournamentRegistration.objects.filter(tournament=tournament, team=team).exists():
            messages.error(request, f"{team.name} is already registered for this tournament.")
            return HttpResponseRedirect(f"/tournament/{tid}/")
        if TournamentRegistration.objects.filter(tournament=tournament, member__in=team.members.all()).exists():
            messages.error(request, "A member of this team is already registered.")
            return HttpResponseRedirect(f"/tournament/{tid}/")

    if TournamentRegistration.objects.filter(tournament=tournament).count() >= tournament.max_participants:
        messages.error(request, "This tournament is full.")
        return HttpResponseRedirect(f"/tournament/{tid}/")

    TournamentRegistration.objects.create(
        tournament=tournament,
        member=member,
        team=team,
        status=TournamentRegistration.RegistrationStatus.PENDING,
    )
    _sync_tournament_roster(tournament)
    if team:
        messages.success(request, f"{team.name} joined this tournament.")
    else:
        messages.success(request, "You joined this tournament.")
    return HttpResponseRedirect(f"/tournament/{tid}/")

@login_required
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
                   status = tournament.status.UPCOMING,
                   is_public = True,
                   entry_type = data["entry_type"],
                   min_rank = data["min_rank"],
                   max_rank = data["max_rank"],
                   current_participants = 0,
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

@login_required
def profilePage(request):
    member = _member_or_none(request.user)
    return render(request, "profile.html", {"member": member})

def scorePopup(request):
    if(request.method == "GET"):
        print(request.GET.get('roundId'))
        print(request.GET.get('matchId'))
        form = ScoreSubmissionForm(round_id=request.GET.get('roundId'), match_id=request.GET.get('matchId'))
        return render(request, 'modules/scoreSubmission.html', {'form': form})

@login_required
def manageTournament(request, tid):
    # implementing the is_staff for now, so only admins can change it
    if not request.user.is_staff:
        raise PermissionDenied

    tournament = get_object_or_404(Tournament, id=tid)
    if request.method == "POST":
            # create a form instance and populate it with data from the request:
            form = ManageTournament(request.POST)
            # check whether it's valid:
            if form.is_valid():
                data = form.cleaned_data

                tournament.name=data["tournament_name"]
                tournament.description=data["description"]
                tournament.game_title = data["game_title"]
                tournament.entry_type = data["entry_type"]
                tournament.min_rank = data["min_rank"]
                tournament.max_rank = data["max_rank"]
                tournament.max_participants = data["max_participants"]
                tournament.start_date = data["start_date"]

                participants= data["participants"]
                if len(participants) == tournament.max_participants:
                    player_ids = list(participants.values_list('id', flat=True))
                    tournament.layout = TournamentCreate(tournament.name, tournament.description, 
                                                         player_ids, tournament.game_title).layout

                tournament.save()

                notify_tournament_updated(tournament, tournament.participants.all(), "The tournament bracket was updated.")
            # redirect to a newly updated tournament URL:
            return HttpResponseRedirect(f'/tournament/{tournament.id}/')

        # if a GET (or any other method) we'll get the tournamenet with its information
    else:
        form = ManageTournament(initial={
            "tournament_name": tournament.name,
            "description": tournament.description,
            "game_title": tournament.game_title,
            "entry_type": tournament.entry_type,
            "max_participants": tournament.max_participants,
            "min_rank": tournament.min_rank,
            "max_rank": tournament.max_rank,
            "start_date": tournament.start_date,
            "participants": tournament.participants.all(),
            })
    # reusing the registation html file as it's just displaying a form. 
    return render(request, 'manageTournament.html', {'form': form})

@never_cache
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

    return render(request, 'tournamentList.html', {'page':page})

def _member_or_none(user):
    if not user.is_authenticated:
        return None
    try:
        return user.member
    except Member.DoesNotExist:
        return None

@never_cache
def teamPage(request):
    member = _member_or_none(request.user)
    form = CreateTeamForm()
    if request.method == "POST":
        if not member:
            messages.error(request, "Log in with a signup account to create a team.")
            return HttpResponseRedirect("/team/")
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            if Team.objects.filter(name__iexact=name).exists():
                messages.error(request, "A team with that name already exists.")
            else:
                team = Team.objects.create(
                    name=name,
                    tag=form.cleaned_data["tag"],
                    leader=member,
                )
                team.members.add(member)
                messages.success(request, f"Team {team.name} created.")
                return HttpResponseRedirect("/team/")
    teams = Team.objects.select_related("leader__user").prefetch_related("members__user").order_by("name")
    return render(
        request,
        "teams.html",
        {
            "form": form,
            "teams": teams,
            "member": member,
        },
    )

@login_required
def joinTeam(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method != "POST":
        return HttpResponseRedirect("/team/")
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot join a team.")
        return HttpResponseRedirect("/team/")
    if team.members.filter(pk=member.pk).exists():
        messages.success(request, f"You are already on {team.name}.")
        return HttpResponseRedirect("/team/")
    team.members.add(member)
    messages.success(request, f"You joined {team.name}.")
    return HttpResponseRedirect("/team/")

def _member_or_none(user):
    if not user.is_authenticated:
        return None
    try:
        return user.member
    except Member.DoesNotExist:
        return None

@never_cache
def teamPage(request):
    member = _member_or_none(request.user)
    form = CreateTeamForm()
    if request.method == "POST":
        if not member:
            messages.error(request, "Log in with a signup account to create a team.")
            return HttpResponseRedirect("/team/")
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            if Team.objects.filter(name__iexact=name).exists():
                messages.error(request, "A team with that name already exists.")
            else:
                team = Team.objects.create(
                    name=name,
                    tag=form.cleaned_data["tag"],
                    leader=member,
                )
                team.members.add(member)
                messages.success(request, f"Team {team.name} created.")
                return HttpResponseRedirect("/team/")
    teams = Team.objects.select_related("leader__user").prefetch_related("members__user").order_by("name")
    return render(
        request,
        "teams.html",
        {
            "form": form,
            "teams": teams,
            "member": member,
        },
    )

@login_required
def joinTeam(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method != "POST":
        return HttpResponseRedirect("/team/")
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot join a team.")
        return HttpResponseRedirect("/team/")
    if team.members.filter(pk=member.pk).exists():
        messages.success(request, f"You are already on {team.name}.")
        return HttpResponseRedirect("/team/")
    team.members.add(member)
    messages.success(request, f"You joined {team.name}.")
    return HttpResponseRedirect("/team/")


@login_required
def tournamentNotifications(request):
    notifications = list(
        TournamentNotification.objects.filter(
        member = request.user.member,
        is_read=False,
    ))

    
    for notification in notifications:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    
    return JsonResponse({
        "notifications": [
            {
                "id": notification.id,
                "message": notification.message,
                "tournament_id": notification.tournament_id
            }
            for notification in notifications
        ]
    })