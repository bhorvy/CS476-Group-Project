# Class: CS 476
# Professor: Dr. Samira Sadaoui
# filename: views.py
# Purpose: Code for views

# Algorithm for posting each form is found here: https://docs.djangoproject.com/en/6.1/topics/forms/

# List of important modules
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
from datetime import datetime

from .models import Member, Tournament, TournamentRegistration, Team
from .forms import RegisterForm, LoginForm, GameLinkForm, TournamentCreation, ScoreSubmissionForm, ManageTournament, CreateTeamForm, MemberProfileForm
from .tournamentFactory.singleElim import SingleElimination
from .tournamentFactory.doubleElim import DoubleElimination
from .tournamentFactory.pools import Pools
from .tournamentFactory.tournamentCreate import TournamentCreate
from .observers.bracketUpdateSubject import notify_tournament_updated
from .models import TournamentNotification
from functools import wraps
from .admin_services import ban_member, BanError

# render demo page
def matchMaker(request):
  template = loader.get_template('demo.html')
  return HttpResponse(template.render())

# render signup page
def signUpPage(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
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

    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

# render login page
def loginPage(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/homePage/')
            else:
                form.add_error(None, "Invalid username or password.")

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@login_required
def gameAccount(request):
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot link a game account.")
        return HttpResponseRedirect("/homePage/")

    if request.method == "POST":
        form = GameLinkForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            GameAccount.objects.update_or_create(
                member=member,
                game_title=data["game_title"],
                defaults={
                    "game_username": data["game_username"],
                    "external_player_id": data["external_player_id"],
                },
            )
            messages.success(request, f"Saved {data['game_title']} account.")
            return HttpResponseRedirect("/gameAccount/")
    else:
        form = GameLinkForm()

    accounts = member.game_accounts.all()
    return render(request, "gameacc.html", {"form": form, "accounts": accounts})

# render tournament roster
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

# render tournament page
@never_cache
def tournamentPage(request, tid):
    format = Tournament.objects.get(id=tid).format
    tournament = None
    match format:
        case "SINGLE_ELIM":
            tournament = SingleElimination(tid)
        case "DOUBLE_ELIM":
            tournament = DoubleElimination(tid)
        case "POOLS":
            tournament = Pools(tid)
    scoreSubmittable = False
    #This POST request is from the score submission popup.
    if request.method == "POST" and "player1_score" in request.POST:
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            round_id = form.cleaned_data["roundVal"]
            match_id = form.cleaned_data["matchVal"]
            is_bracket = form.cleaned_data["isBracket"]
            match format:
                case "SINGLE_ELIM":
                    match = tournament.layout["bracket"][round_id][match_id]
                case "DOUBLE_ELIM":
                    if(is_bracket):
                        match = tournament.layout["bracket"]["upper_bracket"][round_id][match_id]
                    else:
                        match = tournament.layout["bracket"]["lower_bracket"][round_id][match_id]
                case "POOLS":
                    if(is_bracket):
                        match = tournament.layout["bracket"][round_id][match_id]
                    else:
                        match = tournament.layout["pools"][round_id][match_id]
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
                ],
                is_bracket
            )

            notify_tournament_updated(
            tournament.object,
            members,
            "Your match score was updated.",
            )
            if form.cleaned_data['matchCompleted']:
                if not tournament.determineWinner(round_id, match_id, is_bracket):
                    return

            match format:
                case "SINGLE_ELIM":
                    winner_id = tournament.layout["bracket"][round_id][match_id]["winner_id"]
                case "DOUBLE_ELIM":
                    if(is_bracket):
                        winner_id = tournament.layout["bracket"]["upper_bracket"][round_id][match_id]["winner_id"]
                    else:
                        winner_id = tournament.layout["bracket"]["lower_bracket"][round_id][match_id]["winner_id"]
                case "POOLS":
                    if(is_bracket):
                        winner_id = tournament.layout["bracket"][round_id][match_id]["winner_id"]
                    else:
                        winner_id = tournament.layout["pools"][round_id][match_id]["winner_id"]
            winner = Member.objects.filter(pk=winner_id)

            notify_tournament_updated(
            tournament.object,
            winner,
            "You advance, please refer to the bracket for your next match.",
            )       

            return redirect(request.path)

    round_id = None
    match_id = None
    is_bracket = False
    already_registered = False
    user_teams = Team.objects.none()
    member = _member_or_none(request.user)
    registrations = _sync_tournament_roster(tournament.object)
    if member:
        print(member.id)
        userPos = tournament.findUserInBracket(member.id)
        if userPos is not None:
            match format:
                case "SINGLE_ELIM":
                    round_id = userPos["round_id"]
                    match_id = userPos["match_id"]
                case "DOUBLE_ELIM":
                    round_id = userPos["round_id"]
                    match_id = userPos["match_id"]
                    is_bracket = userPos["is_upper_bracket"]
                case "POOLS":
                    is_bracket = userPos["is_bracket"]
                    if(is_bracket):
                        round_id = userPos["round_id"]
                    else:   
                        round_id = userPos["pool_id"]
                    match_id = userPos["match_id"]
                    
            
            bracket_check = None
            if(format == "DOUBLE_ELIM"):
                bracket_check = userPos["is_upper_bracket"]
            elif(format == "POOLS"):
                bracket_check = userPos["is_bracket"]
            scoreSubmittable = not tournament.IsMatchComplete(round_id, match_id, bracket_check)
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
            "format": format,
            "is_bracket": is_bracket
        },
    )

# render tournament reigsteration
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

# render tournament creation
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
                   status = Tournament.Status.UPCOMING,
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

# render home page
def homePage(request):
  template = loader.get_template('homepage.html')
  return render(request, "homepage.html", {})

# enable log out
def logoutHandler(request):
    if(request.user.is_authenticated):
        logout(request)
    return HttpResponseRedirect('/')

# render profile page
@login_required
def profilePage(request):
    member = _member_or_none(request.user)
    return render(request, "profile.html", {"member": member})

# enable profile edit
@login_required
def editProfile(request):
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot edit your profile.")
        return HttpResponseRedirect("/profilePage/")

    if request.method == "POST":
        form = MemberProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            member.firstname = data["firstname"]
            member.lastname = data["lastname"]
            member.gender = data["gender"]
            member.DOB = data["DOB"]
            member.save()
            return redirect("profilePage")
    else:
        form = MemberProfileForm(
            initial={
                "firstname": member.firstname,
                "lastname": member.lastname,
                "gender": member.gender,
                "DOB": member.DOB,
            },
        )

    return render(request, "profileEdit.html", {"form": form})

# render score
def scorePopup(request):
    if(request.method == "GET"):
        print(request.GET.get('roundId'))
        print(request.GET.get('matchId'))
        form = ScoreSubmissionForm(round_id=request.GET.get('roundId'), match_id=request.GET.get('matchId'), 
                                   is_bracket=request.GET.get('is_bracket'))
        return render(request, 'modules/scoreSubmission.html', {'form': form})

# render tournament management
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
                tournament.format = data["format"]
                tournament.min_rank = data["min_rank"]
                tournament.max_rank = data["max_rank"]
                tournament.max_participants = data["max_participants"]
                tournament.start_date = data["start_date"]

                participants= data["participants"]
                if len(participants) <= tournament.max_participants:
                    player_ids = list(participants.values_list('id', flat=True))
                    tournament.layout = TournamentCreate(tournament.name, tournament.description, 
                                                         player_ids, tournament.game_title, tournament.format).layout

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

# render tournament list
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

# render team page
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

# enable joining teams
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

# render enable team page
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

# enable join team
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

# render send notifications
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

#only allow admin to open page
def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *argument, **keywordargument):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *argument, **keywordargument)
    return wrapper

#only for admin to ban a member
@admin_required
def adminBanMember(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(request, "Please enter a ban reason")
    else:
        try:
            ban_member(member, reason)
            messages.success(request, f"{member.user.username} has been banned.")
        except BanError as e:
            messages.error(request, str(e))
    return HttpResponseRedirect("/team/")

#only admin can view the list of members
@admin_required
def adminMemberList(request):
  members = Member.objects.select_related("user").order_by("user__username")
  return render(request, "manage_Members.html", {"members": members})