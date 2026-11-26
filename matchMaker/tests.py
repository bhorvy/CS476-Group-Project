from django.test import TestCase

from .forms import GameLinkForm, ManageTournament, ScoreSubmissionForm, RegisterForm,LoginForm,MemberProfileForm
from .models import Tournament, Member,TournamentRegistration
from django.urls import reverse
from time import perf_counter
from django.contrib.auth.models import User
import requests 
#Robustness tests 
#1. Admin: Manage tournament 2. User: game account inputs 3. User: create tournament inputs 4: user; input score 
class RobustnessTests(TestCase):
    # Test incorrect min and max ranks for tournaments
    def test_admin_manage_tournament(self):
        form_data = {
            "tournament_name": "Test Tournament",
            "description": "The description",
            "game_title": "Deadlock",
            "min_rank": "Not the correct rank",
            "max_rank": "123",
            "entry_type": "Solo (individuals)",
            "start_date": "2026-1-25",
            "format": "Single Elimination"
        }
        form = ManageTournament(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["min_rank"], ["Choose a rank for this game."])
        self.assertEqual(form.errors["max_rank"], ["Choose a rank for this game."])
        #test max rank less than min rank
        form_data = {
                    "tournament_name": "Test Tournament",
                    "description": "The description",
                    "game_title": "Valorant",
                    "min_rank": "15",
                    "max_rank": "6",
                    "entry_type": "Solo (individuals)",
                    "start_date": "2026-1-25",
                    "format": "Single Elimination"
                }
        form = ManageTournament(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["max_rank"], ["Maximum rank must be at least the minimum rank."])

    def test_member_game_account_inputs(self):
        #test missing other game title when game title is OTHER
        form_data = {
            "game_title": "OTHER",
            "other_game_title": "",
            "game_username": "player1",
        }
        form = GameLinkForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["other_game_title"], ["Enter the name of the game."])
        #test tag with # included and region not specified correctly
        form_data = {
                "game_title": "Valorant",
                "game_username": "test",
                "game_tag": "#test",
                "external_player_id": "12839721"
            }
        form = GameLinkForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["game_tag"], ["Enter your tag without #."])
        self.assertEqual(form.errors["external_player_id"], ["Choose a valid region."])


    def test_member_create_tournament_inputs(self):
        #test blank description, name, and other_game_title show errors when blank
        form_data = {
            "tournament_name": "",
            "description": "",
            "game_title": "OTHER",
            "other_game_title": "",
            "entry_type": "Solo (individuals)",
            "start_date": "2026-1-25",
            "format": "Pools"
        }
        form = ManageTournament(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["tournament_name"], ["This field is required."])
        self.assertEqual(form.errors["other_game_title"], ["Enter the name of the game."])
        self.assertEqual(form.errors["description"], ["This field is required."])

        #test if max participants is greater than the limit of 16
        form_data = {
        "tournament_name": "Test Tournament",
        "description": "test description",
        "game_title": "OTHER",
        "other_game_title": "Other Game",
        "entry_type": "Solo (individuals)",
        "start_date": "2026-1-25",
        "max_participants": 32,
        "format": "Double Elimination"
    }
        form = ManageTournament(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["max_participants"], ["Ensure this value is less than or equal to 16."])

    def test_input_score(self):
        # check robustness when string and negative integer
        form_data = {
            "player1_score": "abc",
            "player2_score": -12
        }
        form = ScoreSubmissionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["player1_score"], ["Enter a whole number."])
        self.assertEqual(form.errors["player2_score"], ["Ensure this value is greater than or equal to 0."])
        form_data = {
                    "player1_score": None,
                    "player2_score": 3.1415
                }
        form = ScoreSubmissionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["player1_score"], ["This field is required."])
        self.assertEqual(form.errors["player2_score"], ["Enter a whole number."])


# https://django-testing-docs.readthedocs.io/en/latest/views.html
# https://www.geeksforgeeks.org/python/time-perf_counter-function-in-python/
class TimeEfficiencyTests(TestCase):
    repeat_count = 10
    # i did not read the assignment, this test is not needed
    # test the mean time of loading the deadlock API for rank syncing
    def test_deadlock_api(self):
        # this is my external player ID for testing purposes. As of now Im oracle 4.
        #if not working, uncomment out the following code below
        external_player_id = 76561198309725683
        # API to get rank value
        url = f"https://api.deadlock-api.com/v1/players/{external_player_id}/rank"

        start_time = perf_counter()
        # send request 10 times
        for _ in range(self.repeat_count):
            response = requests.get(url, headers={})
        end_time = perf_counter()
        
        data = response.json();
        # get badge value, mapping is in helpers.py
        value = (data.get("badge"))
        #self.assertIsNotNone(value)
        self.assertEqual(value, 84)
        self.assertEqual(response.status_code, 200)
        print(f"Mean time taken to load deadlock API: {(end_time - start_time) / self.repeat_count} seconds")

    #Test the time taken to load the register page 
    # this test is not needed anymore, we only need 2
    def test_register_to_site(self):
        start_time = perf_counter()
        for _ in range(self.repeat_count):
            response = self.client.get(reverse("signUpPage"))
        end_time = perf_counter()
        self.assertEqual(response.status_code, 200)
        print(f"Mean time taken to load register page: {(end_time - start_time) / self.repeat_count} seconds")


        # test the time taken to submit the form and redirect to the login page
        start_time = perf_counter()
        for i in range(self.repeat_count):
            form_data = {
                "username": f"testuser{i}",
                "password": "testpassword",
                "first_name": "test",
                "last_name": "user",
                "gender": "M",
                "date_of_birth": "2000-01-01",
            }
            form = RegisterForm(data=form_data)
            self.assertTrue(form.is_valid())
            # submit the registration form
            response = self.client.post(reverse("signUpPage"), data=form_data)
            # check that the response status code is 302 (redirect)
            self.assertEqual(response.status_code, 302)
            # ensure the response redirects to the login page after successful registration
            self.assertRedirects(response, reverse("loginPage"))

        end_time = perf_counter()
        print(f"Mean time taken to submit register form: {(end_time - start_time) / self.repeat_count} seconds")

    # Test the time taken to load the tournament page
    def test_load_tournament_page(self):
        # create a large number of tournaments to test performance
        for i in range(2000):
            Tournament.objects.create(
                name=f"Tournament {i}",
                description="Test",
                game_title="Deadlock",
            )
        start_time = perf_counter()
        for _ in range(self.repeat_count):
            response = self.client.get(reverse("tournamentList"))
        end_time = perf_counter()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tournament")
        print(f"Mean time taken to load tournament page: {(end_time - start_time) / self.repeat_count} seconds")

    def test_load_admin_member_list(self):
        # create a number of members to populate admin member list page
        for i in range(50):
                user = User.objects.create_user(username=f"user{i}", password="testpassword")
                Member.objects.create(
                    user=user,
                    firstname="test",
                    lastname="user",
                    gender="M",
                    DOB="2000-01-01"
                )
        # create a superuser to access the admin member list page
        User.objects.create_superuser('myuser', 'myemail@test.com', 'testpassword')
        #login as super user 
        self.client.login(username="myuser", password="testpassword")
        start_time = perf_counter()
        for _ in range(self.repeat_count):
            # load the admin member list page
            response = self.client.get(reverse("adminMemberList"))
        end_time = perf_counter()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Members")
        print(f"Mean time taken to load admin member list page: {(end_time - start_time) / self.repeat_count} seconds")

#correctness testing
# 1.User:login into account 2.User:user update their personal information 3.Admin: banning a member account 4.User: signing up for tournments
class CorrectnessTests(TestCase):
    #Testing the user login with correct username and password
    def test_user_login(self):
        user= User.objects.create_user(username="user123",password="password123")
        Member.objects.create(
            user=user,
            firstname="userfirst",
            lastname="userlast",
            gender="M",
            DOB="2003-05-04"
        )
        form_data= {
            "username":"user123",
            "password":"password123"
        }
        form= LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        response= self.client.post(reverse("loginPage"),data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("homePage"))

    # Testing that user can update their personal information 
    def test_user_edit_profile(self):
        user= User.objects.create_user(username="user123",password="password123")
        member= Member.objects.create(
            user=user,
            firstname="userfirst",
            lastname="userlast",
            gender="M",
            DOB="2003-05-04"
        )
        self.client.login(username="user123",password="password123")
        form_data= {
            "firstname":"first123",
            "lastname":"last123",
            "gender":"M",
            "DOB":"2004-05-02"
        }
        form= MemberProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
        response= self.client.post(reverse("editProfile"),data=form_data)
        self.assertEqual(response.status_code, 302)
        # checking if the information is updated
        member.refresh_from_db()
        self.assertEqual(member.firstname,"first123")
        self.assertEqual(member.lastname,"last123")
        self.assertEqual(str(member.DOB),"2004-05-02")

    # Testing if admin can ban a user 
    def test_admin_ban_member(self):
        user= User.objects.create_user(username="user123",password="password123")
        member= Member.objects.create(
            user=user,
            firstname="first123",
            lastname="last123",
            gender="M",
            DOB="2003-05-03"
        )
        # creating admin to ban member
        User.objects.create_superuser('admin','admin@test.com','admin123')
        self.client.login(username="admin",password="admin123")
        form_data= {
            "reason": "baned for testing"
        }
        #member id is for the url 
        response= self.client.post(reverse("adminBanMember",args=[member.id]),data=form_data)
        self.assertRedirects(response, reverse("adminMemberList"))
        # checking if the member is baned with reason 
        member.refresh_from_db()
        self.assertTrue(member.is_banned)
        self.assertEqual(member.ban_reason,"baned for testing")

    # Testing if the user can signup for tournament
    def test_user_tournament_signup(self):
        user= User.objects.create_user(username="user123",password="password123")
        member= Member.objects.create(
            user=user,
            firstname="first123",
            lastname="last123",
            gender="M",
            DOB="2005-09-05"
        )
        #creating tournament
        tournament= Tournament.objects.create(
            name="test tournament",
            description="created tournament for testing",
            game_title="Deadlock",
            max_participants=8
        )
        self.client.login(username="user123",password="password123")
        #tournament id is for the url
        response = self.client.post(reverse("registerTournament",args=[tournament.id]))
        self.assertRedirects(response, reverse("tournamentPage",args=[tournament.id]))
        # checking if the is user is signedup and exist in the tournament
        self.assertTrue(TournamentRegistration.objects.filter(tournament=tournament,member=member).exists())