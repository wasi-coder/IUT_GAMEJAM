import os
import unittest

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from map8.map8 import (
    MUSIC_PATH,
    complete_final_boss,
    create_platform_rects,
    load_map,
)
from map8.platform import platform
from Orge.ogre import (
    OGRE_ATTACK_COOLDOWN,
    OGRE_ATTACK_DAMAGE,
    OGRE_ATTACK_DURATION,
    OGRE_MAX_HEALTH,
    OgreBoss,
)
from player import Player
from player.player import KICK_DURATION, KICK_IMPACT_TIME


class DamageTarget:
    def __init__(self, rect):
        self.rect = rect
        self.damage_taken = 0

    def take_damage(self, amount):
        self.damage_taken += amount


class Map8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 320))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_map8_uses_native_size_and_platform_array(self):
        self.assertEqual(load_map().get_size(), (960, 320))
        expected_count = sum(
            tile != -1 for row in platform for tile in row
        )
        self.assertEqual(len(create_platform_rects()), expected_count)
        self.assertTrue(MUSIC_PATH.is_file())

    def test_ogre_has_three_rage_stages(self):
        ogre = OgreBoss(790, 272, 250, 950)
        self.assertEqual(ogre.max_health, OGRE_MAX_HEALTH)
        self.assertEqual(ogre.rage_stage, 0)
        ogre.health = round(ogre.max_health * 0.5)
        self.assertEqual(ogre.rage_stage, 1)
        ogre.health = round(ogre.max_health * 0.2)
        self.assertEqual(ogre.rage_stage, 2)

    def test_ogre_damage_is_reduced_across_rage_stages(self):
        self.assertEqual(OGRE_ATTACK_DAMAGE, (20, 30, 40))

    def test_ogre_attack_animation_deals_damage(self):
        player = Player(730, 200)
        ogre = OgreBoss(790, 272, 250, 950)
        player.rect.centerx = ogre.rect.centerx - 40
        player.rect.centery = ogre.rect.centery
        player.position.update(player.rect.topleft)

        ogre.update(0.01, player)
        ogre.update(0.40, player)
        ogre.update(0.01, player)

        self.assertLess(player.health, player.max_health)

    def test_ogre_waits_eight_seconds_after_each_swing(self):
        player = Player(730, 200)
        ogre = OgreBoss(790, 272, 250, 950)
        player.rect.center = (
            ogre.rect.centerx - 40,
            ogre.rect.centery,
        )
        player.position.update(player.rect.topleft)

        ogre._start_attack()
        ogre.update(OGRE_ATTACK_DURATION, player)
        self.assertEqual(ogre.attack_cooldown_left, 8.0)

        ogre.update(7.9, player)
        self.assertFalse(ogre.attack_time_left > 0)
        ogre.update(0.1, player)
        self.assertTrue(ogre.attack_time_left > 0)
        self.assertEqual(OGRE_ATTACK_COOLDOWN, 8.0)

    def test_final_boss_returns_player_to_map1_headmaster(self):
        player = Player(0, 0)
        starting_points = player.points

        destination, arrived_from = complete_final_boss(player)

        self.assertEqual(destination, "map1")
        self.assertEqual(arrived_from, "map8")
        self.assertTrue(player.map8_cleared)
        self.assertEqual(player.points, starting_points + 250)

    def test_kick_deals_same_level_scaled_damage_as_space_attack(self):
        player = Player(100, 200)
        player.attack_damage = 35
        target = DamageTarget(player.get_kick_rect())
        kick = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k)

        self.assertTrue(player.handle_event(kick))
        player._update_kick(KICK_IMPACT_TIME - 0.01, [target])
        self.assertEqual(target.damage_taken, 0)

        player._update_kick(0.01, [target])

        self.assertEqual(target.damage_taken, player.attack_damage)

    def test_map2_style_contact_damage_does_not_cancel_kick(self):
        player = Player(100, 200)
        # Overlap the player's rear half, as a chasing slime can in Map 2.
        target = DamageTarget(
            pygame.Rect(player.rect.left - 4, player.rect.bottom - 16, 18, 16)
        )
        kick = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k)

        self.assertTrue(player.handle_event(kick))
        self.assertTrue(player.take_damage(10))
        self.assertTrue(player.is_kicking)

        player._update_kick(KICK_DURATION, [target])

        self.assertEqual(target.damage_taken, player.attack_damage)
        self.assertFalse(player.is_kicking)


if __name__ == "__main__":
    unittest.main()
