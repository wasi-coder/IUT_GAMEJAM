from pathlib import Path

import pygame

from music_manager import play_sound_effect


SLIME_FRAME_COUNT = 7
SLIME_ANIMATION_SPEED = 8
SLIME_SPEED = 55
SLIME_MAX_HEALTH = 20
SLIME_CONTACT_DAMAGE = 10
SLIME_DAMAGE_COOLDOWN = 1.0
SLIME_KNOCKBACK_DECELERATION = 900
SLIME_EDGE_MARGIN = 10
KNOCKBACK_AIR_TIME = 0.45
KNOCKBACK_ARC_HEIGHT = 22
SLIME_PATH = Path(__file__).parent
SLIME_DEATH_SOUND_PATH = SLIME_PATH / "death.mp3"


class Slime:
    _right_frames = None
    _left_frames = None

    def __init__(self, center_x, bottom_y):
        self._load_frames()

        self.rect = pygame.Rect(0, 0, 18, 18)
        self.rect.midbottom = (center_x, bottom_y)
        self.position_x = float(self.rect.x)

        self.health = SLIME_MAX_HEALTH
        self.max_health = SLIME_MAX_HEALTH
        self.facing_right = True
        self.animation_time = 0.0
        self.damage_cooldown_left = 0.0
        self.knockback_velocity = 0.0
        self.knockback_air_time = 0.0

    @classmethod
    def _load_frames(cls):
        if cls._right_frames is not None:
            return

        cls._right_frames = []
        for frame_number in range(SLIME_FRAME_COUNT):
            path = SLIME_PATH / f"{frame_number}.png"
            cls._right_frames.append(
                pygame.image.load(path).convert_alpha()
            )

        cls._left_frames = [
            pygame.transform.flip(frame, True, False)
            for frame in cls._right_frames
        ]

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        was_alive = self.alive
        self.health = max(0, self.health - max(0, amount))
        if was_alive and not self.alive:
            play_sound_effect(
                SLIME_DEATH_SOUND_PATH,
                volume=0.45,
                max_duration_ms=1000,
            )

    def apply_knockback(self, distance):
        """Launch the slime horizontally instead of teleporting it."""
        self.knockback_velocity = distance * 5.5
        self.knockback_air_time = KNOCKBACK_AIR_TIME

    def update(self, delta_time, player, map_width):
        self.knockback_air_time = max(
            0, self.knockback_air_time - delta_time
        )

        if abs(self.knockback_velocity) > 1:
            self.position_x += self.knockback_velocity * delta_time
            deceleration = SLIME_KNOCKBACK_DECELERATION * delta_time
            if self.knockback_velocity > 0:
                self.knockback_velocity = max(
                    0, self.knockback_velocity - deceleration
                )
            else:
                self.knockback_velocity = min(
                    0, self.knockback_velocity + deceleration
                )
        else:
            self.knockback_velocity = 0.0
            if not self.alive:
                return
            if player.rect.centerx < self.rect.centerx:
                direction = -1
                self.facing_right = False
            elif player.rect.centerx > self.rect.centerx:
                direction = 1
                self.facing_right = True
            else:
                direction = 0
            self.position_x += direction * SLIME_SPEED * delta_time

        left_boundary = SLIME_EDGE_MARGIN
        right_boundary = map_width - self.rect.width - SLIME_EDGE_MARGIN
        self.position_x = max(
            left_boundary, min(self.position_x, right_boundary)
        )
        if self.position_x in (left_boundary, right_boundary):
            self.knockback_velocity = 0.0
        self.rect.x = round(self.position_x)

        # A fatal kick still completes its visible launch, but a defeated
        # slime can no longer chase or hurt the player.
        if not self.alive:
            self.animation_time += delta_time
            return

        self.damage_cooldown_left = max(
            0, self.damage_cooldown_left - delta_time
        )
        if (
            self.rect.colliderect(player.rect)
            and self.damage_cooldown_left <= 0
        ):
            player.take_damage(SLIME_CONTACT_DAMAGE)
            self.damage_cooldown_left = SLIME_DAMAGE_COOLDOWN

        self.animation_time += delta_time

    def draw(self, screen, camera_x):
        frames = (
            self._right_frames if self.facing_right else self._left_frames
        )
        frame_index = int(
            self.animation_time * SLIME_ANIMATION_SPEED
        ) % len(frames)
        image = frames[frame_index]
        air_progress = self.knockback_air_time / KNOCKBACK_AIR_TIME
        arc_offset = round(
            4 * KNOCKBACK_ARC_HEIGHT * air_progress * (1 - air_progress)
        )
        draw_rect = image.get_rect(
            midbottom=(
                self.rect.centerx - round(camera_x),
                self.rect.bottom - arc_offset,
            )
        )
        screen.blit(image, draw_rect)
