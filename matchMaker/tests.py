from django.test import TestCase

from .forms import GameLinkForm, ManageTournament, ScoreSubmissionForm
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

    def test_user_game_account_inputs(self):
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


    def test_user_create_tournament_inputs(self):
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
