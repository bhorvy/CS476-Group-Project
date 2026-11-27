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

from .models import GameAccount, Member, Tournament, TournamentRegistration, Team, TournamentNotification, BanError
from .forms import RegisterForm, LoginForm, GameLinkForm, TournamentCreation, ScoreSubmissionForm, ManageTournament, CreateTeamForm, MemberProfileForm
from .tournamentFactory.singleElim import SingleElimination
from .tournamentFactory.doubleElim import DoubleElimination
from .tournamentFactory.pools import Pools
from .tournamentFactory.tournamentCreate import TournamentCreate
from .observers.bracketUpdateSubject import notify_tournament_updated
from functools import wraps
from django.views.decorators.http import require_POST
from .ranks.lookup import RankLookupError, fetch_game_rank
from .ranks.helpers import GAME_ACCOUNT_HELP, SUPPORTED_RANKED_GAMES, rank_label_for_value
from .ranks.eligibility import rank_eligibility_errors


# render demo page
def matchMaker(request):
  template = loader.get_template('homepage.html')
  return HttpResponse(template.render())

# View for the user signup webpage.
def signUpPage(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            data = form.cleaned_data
            #Attempt to create User and Member role objects given the username isn't
            #   already taken.
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

# View for the user login webpage.
def loginPage(request):
    #GET: Render the login webpage.
    #POST: Authenticate the user's credentials.
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                #is the users is baned they get fstring messsage that their account are banned with reason
                member=_member_or_none(user)
                if member and member.is_banned:
                    form.add_error(None,f"this account is baned by admin reason: {member.ban_reason}")
                else:
                    login(request, user)
                    return HttpResponseRedirect('/homePage/')
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

#View for adding a game account.
@login_required
def gameAccount(request):
    #GET: Render the form to add a game account.
    #POST: Add the account to the database
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot link a game account.")
        return HttpResponseRedirect("/homePage/")

    if request.method == "POST":
        form = GameLinkForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            account, created = GameAccount.objects.get_or_create(
                member=member,
                game_title=data["game_title"],
                defaults={
                    "game_username": data["game_username"],
                    "game_tag": data["game_tag"],
                    "external_player_id": data["external_player_id"],
                },
            )
            if not created:
                # Reset rank if game account changed
                update_fields = ["game_username", "game_tag", "external_player_id"]
                if (account.game_username != data["game_username"] or account.game_tag != data["game_tag"] or account.external_player_id != data["external_player_id"]):
                    account.rank_or_elo = None
                    account.rank_value = None
                    update_fields.extend(["rank_or_elo", "rank_value"])
                account.game_username = data["game_username"]
                account.game_tag = data["game_tag"]
                account.external_player_id = data["external_player_id"]
                account.save(update_fields=update_fields)
            messages.success(request, f"Saved {data['game_title']} account.")
            return HttpResponseRedirect("/gameAccount/")
    else:
        form = GameLinkForm()

    accounts = member.game_accounts.all()
    return render(request, "gameacc.html", {"form": form, "accounts": accounts, "game_help": GAME_ACCOUNT_HELP, "ranked_games": SUPPORTED_RANKED_GAMES})

#sync game rank with specified game title
@login_required
def syncGameRank(request, account_id):
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile.")
        return HttpResponseRedirect("/gameAccount/")

    account = get_object_or_404(member.game_accounts, pk=account_id)
    try:
        rank_result = fetch_game_rank(
            account.game_title,
            account.game_username,
            account.external_player_id,
            account.game_tag,
        )
    except RankLookupError as error:
        messages.error(request, str(error))
    else:
        display, value = rank_result
        account.rank_or_elo = display
        account.rank_value = value
        account.save(update_fields=["rank_or_elo", "rank_value", "last_synced"])
        messages.success(request, f"Updated {account.game_title} rank: {display}.",)
    return HttpResponseRedirect("/gameAccount/")


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

# View for the tournament bracket webpage
@never_cache
def tournamentPage(request, tid):
    #Get the bracket-specific class based on the format type. 
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
    #GET: Render the webpage and all the options/parameters specific to who is logged in
    #   and the type of tournament bracket rendered.
    #POST: Submit scores for a specific match using the score popup.
    if request.method == "POST" and "player1_score" in request.POST:
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            round_id = form.cleaned_data["roundVal"]
            match_id = form.cleaned_data["matchVal"]
            is_bracket = form.cleaned_data["isBracket"]
            #The JSON for the bracket layout is different for each bracket type.
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

            #Use the observer to notify all current participants in the tournament.
            notify_tournament_updated(
            tournament.object,
            members,
            f"Your score in {tournament.object.name} was updated.",
            )
            if form.cleaned_data['matchCompleted']:
                if not tournament.determineWinner(round_id, match_id, is_bracket):
                    return

            #The JSON for the bracket layout is different for each bracket type. Therefore, 
            #   the winner id gets placed slightly different based on bracket type.
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

            #Notify the winner of that match using the observer.
            winner = Member.objects.filter(pk=winner_id)
            notify_tournament_updated(
            tournament.object,
            winner,
            f"You advance in {tournament.object.name}. Check the bracket for your next match.",
            )       

            return redirect(request.path)

    #Parameters needed to properly render the tournament bracket webpage.
    round_id = None
    match_id = None
    is_bracket = False
    already_registered = False
    user_teams = Team.objects.none()
    member = _member_or_none(request.user)
    registrations = _sync_tournament_roster(tournament.object)
    userList = TournamentRegistration.objects.filter(tournament=Tournament.objects.get(id=tid))
    champion = Tournament.objects.get(id=tid).winner
    userInfo = {}
    for i in userList:
        userInfo[i.member.id] = i.member.user.username
    if member:
        userPos = tournament.findUserInBracket(member.id)
        if userPos is not None:
            #Values for round_id, match_id, is_bracket, and bracket_check differ based
            #   on the bracket type.
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
    # Get the minimum and maximum rank labels for display.
    minimum_rank_label = rank_label_for_value(tournament.object.game_title, tournament.object.min_rank)
    maximum_rank_label = rank_label_for_value(tournament.object.game_title, tournament.object.max_rank)
    return render(
        request,
        "tournament.html",
        {
            "tournament": tournament,
            "tid": tid,
            "score_submittable": scoreSubmittable,
            "round": round_id,
            "match": match_id,
            "registrations": registrations,
            "already_registered": already_registered,
            "user_teams": user_teams,
            "format": format,
            "is_bracket": is_bracket,
            "user_info": userInfo,
            "minimum_rank_label": minimum_rank_label,
            "maximum_rank_label": maximum_rank_label,
            "champion": champion
        },
    )

# View for handling tournament registration.
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

    if team:
        registering_members = team.members.select_related("user").all()
    else:
        registering_members = [member]

    # Check all members meet rank eligibility constraints
    eligibility_errors = rank_eligibility_errors(registering_members, tournament)
    if eligibility_errors:
        messages.error(request, " ".join(eligibility_errors))
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

# View for the webpage used to create a tournament.
@login_required
def tournamentCreatePage(request):
    #GET: Render an empty from for tournament creation.
    #POST: Submit the form to create a new Tournament object.
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

# Home page view.
def homePage(request):
  template = loader.get_template('homepage.html')
  return render(request, "homepage.html", {})

# View for logging out the user.
def logoutHandler(request):
    if(request.user.is_authenticated):
        logout(request)
    return HttpResponseRedirect('/')

# View for rendering the user's profile.
@login_required
def profilePage(request):
    member = _member_or_none(request.user)
    return render(request, "profile.html", {"member": member})

# View for displaying the form that allows the user to edit their profile.
@login_required
def editProfile(request):
    member = _member_or_none(request.user)
    if not member:
        messages.error(request, "Your account has no member profile, so you cannot edit your profile.")
        return HttpResponseRedirect("/profilePage/")

    #GET: Render the form to edit their profile.
    #POST: Submit the form to make the changes.
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

# Render the score submission popup that allows the user to submit the score
#   for the associated tournamnet.
def scorePopup(request):
    if(request.method == "GET"):
        
        form = ScoreSubmissionForm(round_id=request.GET.get('roundId'), match_id=request.GET.get('matchId'), 
                                   is_bracket=request.GET.get('is_bracket'), tid=request.GET.get('tid'))
        return render(request, 'modules/scoreSubmission.html', {'form': form})
 
#listing all the matches in the backet for admit to edit it
def _list_matches(tournament):
    choices= []
    layout=tournament.layout
    #two bracket for double elimination
    labels = ["Round", ""]
    if tournament.format=="DOUBLE_ELIM":
        bracketType = DoubleElimination(tournament.id)
        upper=layout["bracket"]["upper_bracket"]
        lower=layout["bracket"]["lower_bracket"]
        labels[0] = "Upper"
        labels[1] = "Lower"
    elif tournament.format == "POOLS":
        bracketType = Pools(tournament.id)
        upper=layout["bracket"]
        lower=layout["pools"]
        labels[0] = "Bracket Round"
        labels[1] = "Pool"
    else:
        bracketType = SingleElimination(tournament.id)    
        upper=layout["bracket"]
        lower=[]

    #Valid matches are added to a list to be selected from. Any match with an invalid
    #   userid is omitted.
    #Adding matches to list from upper bracket.
    for round_id in range(len(upper)):
        for match_id in range(len(upper[round_id])):
            userIds = bracketType.getPlayerMatchIds(round_id, match_id, True)
            if(userIds[0] > 0 and userIds[1] > 0):
                choices.append({"value": f"roundId={round_id}&matchId={match_id}&is_bracket=True","label": 
                                f"{labels[0]} {round_id + 1}, Match {match_id + 1}"})
    #Adding matches to list from lower bracket.
    for round_id in range(len(lower)):
        if(tournament.format == "POOLS"):
            #Listing must omit the last array position in the pool.
            for match_id in range(6):
                userIds = bracketType.getPlayerMatchIds(round_id, match_id, False)
                if(userIds[0] > 0 and userIds[1] > 0):
                    choices.append({"value": f"roundId={round_id}&matchId={match_id}&is_bracket=False","label": 
                                    f"{labels[1]} {round_id + 1}, Match {match_id + 1}"})
        else:
            for match_id in range(len(lower[round_id])):
                userIds = bracketType.getPlayerMatchIds(round_id, match_id, False)
                if(userIds[0] > 0 and userIds[1] > 0):
                    choices.append({"value": f"roundId={round_id}&matchId={match_id}&is_bracket=False","label": 
                                f"{labels[1]} {round_id + 1}, Match {match_id + 1}"})
    return choices

# Renders the tournament management page for an administrator.
@login_required
def manageTournament(request, tid):
    # implementing the is_staff for now, so only admins can change it
    if not request.user.is_staff:
        raise PermissionDenied
    tournament = get_object_or_404(Tournament, id=tid)
    #GET: Render the tournament management form.
    #POST: Handle various management actions.
    if request.method == "POST":
            # create a form instance and populate it with data from the request:
            form = ManageTournament(request.POST)
            if form.is_valid():
                format = tournament.format
                #Check if the tournament deletion or tournament initiation buttons
                #   were pressed and handle their actions.
                match format:
                    case "SINGLE_ELIM":
                        tournamentType = SingleElimination(tid)
                    case "DOUBLE_ELIM":
                        tournamentType = DoubleElimination(tid)
                    case "POOLS":
                        tournamentType = Pools(tid)
                action = request.POST.get("action")
                if(action == "delete_tournament"):
                    # Notify before deleting; the notice is kept with tournament set to NULL.
                    notify_tournament_updated(tournament, tournament.participants.all(),
                                              f"Tournament {tournament.name} was deleted.")
                    tournamentType.deleteTournament()
                    return HttpResponseRedirect(f'/tournament/') 
                elif(action == "start_tournament"):
                    tournamentType.startTournament()
                    notify_tournament_updated(tournament, tournament.participants.all(),
                                              f"Tournament {tournament.name} has started. Check the bracket for your first match.")
                    return HttpResponseRedirect(f'/tournament/{tournament.id}/')
                #If those buttons were not press, the submit button was pressed instead.
                #Handle the form as a result.
                data = form.cleaned_data
                
                #If any participants were added, they will also need to be synced to the TournamentRegistration model,
                #   and any related values need to be updated like participant count.
                participants= data["participants"]
                if participants.count() > data["max_participants"]:
                    form.add_error("participants", "The selected participants exceed the tournament capacity.")
                else:
                    # Set rank constraints based on selected game
                    tournament.game_title = data["game_title"]
                    tournament.min_rank = data["min_rank"]
                    tournament.max_rank = data["max_rank"]

                    # Verify all participants meet rank eligibility
                    eligibility_errors = rank_eligibility_errors(participants, tournament)
                    if eligibility_errors:
                        form.add_error("participants", " ".join(eligibility_errors))
                    else:
                        # Update tournament details and bracket
                        tournament.name = data["tournament_name"]
                        tournament.description = data["description"]
                        tournament.entry_type = data["entry_type"]
                        tournament.format = data["format"]
                        tournament.max_participants = data["max_participants"]
                        tournament.start_date = data["start_date"]


                        player_ids = list(participants.values_list('id', flat=True))
                        tournament.layout = TournamentCreate(tournament.name, tournament.description,
                                                             player_ids, tournament.game_title, tournament.format).layout
                        for participant in participants:
                            if not TournamentRegistration.objects.filter(member=participant, tournament=tournament).exists():
                                registration = TournamentRegistration.objects.create(
                                    tournament=tournament, member=participant, status="ACCEPTED")
                                registration.save()
                                
                        # remove registrations for players who were unselected
                        removed_registrations = TournamentRegistration.objects.filter(tournament=tournament).exclude(member__in=participants)
                        removed_members = Member.objects.filter(pk__in=removed_registrations.values_list('member_id', flat=True))
                        notify_tournament_updated(tournament, removed_members,
                                                  f"You were removed from Tournament{tournament.name}.")
                        removed_registrations.delete()
                        _sync_tournament_roster(tournament)
                        tournament.current_participants = participants.count()
                        tournament.save()
                        #Let the tournament participants know that the bracket is updated.
                        notify_tournament_updated(tournament, tournament.participants.all(),
                                                  f"The tournament bracket for {tournament.name} was updated.")
            # redirect to the newly updated tournament's URL, if no errors
            if not form.errors:
                return HttpResponseRedirect(f'/tournament/{tournament.id}/')

        # if a GET (or any other method) we'll get the tournamenet with its information
    else:
        form = ManageTournament(initial={
            "tournament_name": tournament.name,
            "description": tournament.description,
            "game_title": tournament.game_title,
            "entry_type": tournament.entry_type,
            "max_participants": tournament.max_participants,
            "start_date": tournament.start_date,
            "participants": tournament.participants.all(),
            })
        if tournament.game_title not in SUPPORTED_RANKED_GAMES:
            form.initial["game_title"] = "OTHER"
            form.initial["other_game_title"] = tournament.game_title
            form.initial["min_rank"] = ""
            form.initial["max_rank"] = ""
        else:
            form.initial["min_rank"] = tournament.min_rank
            form.initial["max_rank"] = tournament.max_rank
    # reusing the registation html file as it's just displaying a form. 
    return render(request, 'manageTournament.html', {'form': form,'tournament':tournament,'match_choices':_list_matches(tournament)})

# View for the list of tournaments.
@never_cache
def TournamentList(request, id=1):
    #Utilize the builtin django paginator to limit the amount of entries per page.
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

#Method for checking if there is a user and if that user has a Member role.
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

@never_cache
def teamDetail(request, team_id):
    team = get_object_or_404(
        Team.objects.select_related("leader__user").prefetch_related("members__user"),
        id=team_id,
    )
    member = _member_or_none(request.user)
    already_on_team = bool(member and team.members.filter(pk=member.pk).exists())
    return render(
        request,
        "teamDetail.html",
        {
            "team": team,
            "member": member,
            "already_on_team": already_on_team,
        },
    )

# render send notifications
@login_required
def tournamentNotifications(request):
    notifications = list(
        TournamentNotification.objects.filter(
        member = request.user.member,
        is_read=False,
    ).order_by("created_at"))
    
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

@login_required
def acknowledgeTournamentNotifications(request):
    notification_id = request.POST.get("id")
    TournamentNotification.objects.filter(member=request.user.member, id=notification_id).update(is_read=True)

    return HttpResponse()

#only allow admin to open page
def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *argument, **keywordargument):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *argument, **keywordargument)
    return wrapper

#function for admin to ban a member with a message with username  
#check if admin provided the reason 
#ban error if its admin/super user 
@admin_required
@require_POST
def adminBanMember(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, "Please enter a ban reason")
    else:
        try:
            member.ban(reason)
            messages.success(request,f"{member.user.username} has been banned.")
        except BanError as e:
            messages.error(request,str(e))
    return redirect("adminMemberList")

#function to unban a user with a message with username
@admin_required
@require_POST
def adminUnbanMember(request,member_id):
    member=get_object_or_404(Member,id=member_id)
    member.unban()
    messages.success(request,f"{member.user.username} was unbanned successfully")
    return redirect("adminMemberList")

#only admin can view the list of all the users
@admin_required
def adminMemberList(request):
    members=(
        Member.objects
        .select_related("user")
        .prefetch_related("led_teams","teams")
        .order_by("user__username")
    )
    return render(request,"manage_Members.html",{"members":members})