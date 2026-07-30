import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from map3.map3 import SCREEN_HEIGHT, SCREEN_WIDTH, create_night_overlay
from map1.map1 import FINAL_VICTORY_DIALOGUE, create_story_dialogue
from npc1 import HealingNPC
from player import Player


class Map3NightAndNpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 320))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map3_is_dark_except_around_player(self):
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        overlay = create_night_overlay(center)
        self.assertEqual(overlay.get_at(center).a, 0)
        self.assertGreater(overlay.get_at((0, 0)).a, 220)

    def test_npc1_only_heals_with_e_interaction(self):
        player = Player(100, 200)
        npc = HealingNPC(player.rect.centerx, player.rect.bottom)
        player.health = 1

        self.assertTrue(npc.talk(player))
        self.assertEqual(player.health, player.max_health)
        self.assertFalse(hasattr(npc, "draw_store"))
        self.assertFalse(hasattr(npc, "handle_event"))

    def test_headmaster_praises_player_after_final_boss(self):
        player = Player(100, 200)
        player.map8_cleared = True

        dialogue, kind = create_story_dialogue(player, "map8", {})

        self.assertIsNotNone(dialogue)
        self.assertEqual(kind, "final")
        praise = " ".join(line["text"] for line in FINAL_VICTORY_DIALOGUE)
        self.assertIn("defeated the Ogre", praise)
        self.assertIn("proud of you", praise)


if __name__ == "__main__":
    unittest.main()
