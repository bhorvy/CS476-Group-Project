from django.test import TestCase

from .models import Tournament, UserGameAccount
from .views import fetch_game_rank
#Robustness tests 
#1. Admin: Manage tournament 2. User: game account inputs 3. User: create tournament inputs 4: user; input score 
class RobustnessTests(TestCase):
    def test_admin_manage_tournament(self):
        pass

    def test_user_game_account_inputs(self):
        pass

    def test_user_create_tournament_inputs(self):
        pass

    def test_input_score(self):
        pass