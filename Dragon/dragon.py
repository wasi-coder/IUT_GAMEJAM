from pathlib import Path

import pygame

from music_manager import play_sound_effect


DRAGON_MAX_HEALTH = 200
DRAGON_ATTACK_DAMAGE = 40
DRAGON_SPEED = 42
DRAGON_ATTACK_RANGE = 88
DRAGON_ATTACK_COOLDOWN = 1.4
DRAGON_KNOCKBACK_STRENGTH = 2.2
DRAGON_KNOCKBACK_DECELERATION = 700
DRAGON_IDLE_SPEED = 6
DRAGON_ATTACK_SPEED = 12
DRAGON_ATTACK_FRAME_COUNT = 18
DRAGON_ATTACK_DURATION = (
    DRAGON_ATTACK_FRAME_COUNT / DRAGON_ATTACK_SPEED
)
DRAGON_IDLE_SIZE = (154, 106)
DRAGON_ATTACK_SIZE = (187, 132)
DRAGON_PATH = Path(__file__).parent
DRAGON_DEATH_SOUND_PATH = DRAGON_PATH / "death.mp3"


class DragonBoss:
    """Large flying Map 4 boss with a full attack animation."""

    _animations = None

    def __init__(self, center_x, center_y, zone_left, zone_right):
        self._load_animations()
        self.zone_left = zone_left
        self.zone_right = zone_right
        self.rect = pygame.Rect(0, 0, 72, 68)
        self.rect.center = (center_x, center_y)
        self.position = pygame.Vector2(self.rect.topleft)
        self.max_health = DRAGON_MAX_HEALTH
        self.health = self.max_health
        self.facing_right = False
        self.state = "idle"
        self.animation_time = 0.0
        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.attack_has_dealt_damage = False
        self.knockback_velocity = 0.0

    @classmethod
    def _load_animations(cls):
        if cls._animations is not None:
            return

        idle_left = [
            cls._load_frame(
                DRAGON_PATH / "Idle" / f"idle{number}.png",
                DRAGON_IDLE_SIZE,
            )
            for number in range(1, 7)
        ]
        attack_left = [
            cls._load_frame(
                DRAGON_PATH / "Attack" / f"frame{number}.png",
                DRAGON_ATTACK_SIZE,
            )
            for number in range(1, DRAGON_ATTACK_FRAME_COUNT + 1)
        ]
        left = {"idle": idle_left, "attack": attack_left}
        right = {
            state: [
                pygame.transform.flip(frame, True, False)
                for frame in frames
            ]
            for state, frames in left.items()
        }
        cls._animations = {"left": left, "right": right}

    @staticmethod
    def _load_frame(path, size):
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(image, size)

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        was_alive = self.alive
        self.health = max(0, self.health - max(0, amount))
        if was_alive and not self.alive:
            play_sound_effect(
                DRAGON_DEATH_SOUND_PATH,
                volume=0.75,
                max_duration_ms=1000,
            )

    def apply_knockback(self, distance):
        """Push the flying boss backward, with resistance from its weight."""
        self.knockback_velocity = distance * DRAGON_KNOCKBACK_STRENGTH
        self.attack_time_left = 0.0
        self.attack_has_dealt_damage = False

    def _distance_to_player(self, player):
        return pygame.Vector2(player.rect.center).distance_to(
            self.rect.center
        )

    def _start_attack(self):
        self.state = "attack"
        self.animation_time = 0.0
        self.attack_time_left = DRAGON_ATTACK_DURATION
        self.attack_cooldown_left = DRAGON_ATTACK_COOLDOWN
        self.attack_has_dealt_damage = False

    def update(self, delta_time, player):
        if not self.alive:
            return

        self.attack_cooldown_left = max(
            0.0, self.attack_cooldown_left - delta_time
        )
        offset = pygame.Vector2(player.rect.center) - pygame.Vector2(
            self.rect.center
        )
        if offset.x != 0:
            self.facing_right = offset.x > 0

        if abs(self.knockback_velocity) > 1:
            self.state = "idle"
            self.animation_time += delta_time
            self.position.x += self.knockback_velocity * delta_time
            self.position.x = max(
                self.zone_left,
                min(self.position.x, self.zone_right - self.rect.width),
            )
            self.rect.topleft = (
                round(self.position.x),
                round(self.position.y),
            )
            deceleration = DRAGON_KNOCKBACK_DECELERATION * delta_time
            if self.knockback_velocity > 0:
                self.knockback_velocity = max(
                    0.0, self.knockback_velocity - deceleration
                )
            else:
                self.knockback_velocity = min(
                    0.0, self.knockback_velocity + deceleration
                )
            return
        self.knockback_velocity = 0.0

        if self.attack_time_left > 0:
            self.state = "attack"
            self.animation_time += delta_time
            attack_elapsed = DRAGON_ATTACK_DURATION - self.attack_time_left
            if (
                not self.attack_has_dealt_damage
                and attack_elapsed >= 8 / DRAGON_ATTACK_SPEED
            ):
                if self._distance_to_player(player) <= DRAGON_ATTACK_RANGE + 25:
                    player.take_damage(DRAGON_ATTACK_DAMAGE)
                self.attack_has_dealt_damage = True
            self.attack_time_left = max(
                0.0, self.attack_time_left - delta_time
            )
            return

        self.state = "idle"
        self.animation_time += delta_time
        if player.rect.centerx < self.zone_left:
            return

        distance = offset.length()
        if distance <= DRAGON_ATTACK_RANGE:
            if self.attack_cooldown_left <= 0:
                self._start_attack()
            return

        if distance > 0:
            self.position += offset.normalize() * DRAGON_SPEED * delta_time
            self.position.x = max(
                self.zone_left,
                min(self.position.x, self.zone_right - self.rect.width),
            )
            self.position.y = max(
                18, min(self.position.y, 270 - self.rect.height)
            )
            self.rect.topleft = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera_x):
        direction = "right" if self.facing_right else "left"
        frames = self._animations[direction][self.state]
        speed = (
            DRAGON_ATTACK_SPEED
            if self.state == "attack"
            else DRAGON_IDLE_SPEED
        )
        frame_index = min(
            int(self.animation_time * speed) % len(frames),
            len(frames) - 1,
        )
        image = frames[frame_index]
        draw_rect = image.get_rect(
            center=(
                self.rect.centerx - round(camera_x),
                self.rect.centery,
            )
        )
        screen.blit(image, draw_rect)

        bar_width = 110
        bar_rect = pygame.Rect(
            self.rect.centerx - round(camera_x) - bar_width // 2,
            draw_rect.top - 8,
            bar_width,
            7,
        )
        pygame.draw.rect(screen, (45, 20, 20), bar_rect)
        health_width = round(bar_width * self.health / self.max_health)
        pygame.draw.rect(
            screen,
            (215, 60, 60),
            (bar_rect.x, bar_rect.y, health_width, bar_rect.height),
        )
        pygame.draw.rect(screen, (245, 220, 190), bar_rect, 1)
