from pathlib import Path

import pygame


CROW_MAX_HEALTH = 20
CROW_ATTACK_DAMAGE = 10
CROW_SPEED = 70
CROW_ANIMATION_SPEED = 7
CROW_ATTACK_COOLDOWN = 1.0
CROW_KNOCKBACK_STRENGTH = 5.5
CROW_KNOCKBACK_DECELERATION = 1000
CROW_PATH = Path(__file__).parent


class Crow:
    """A flying zone enemy that chases and collides with the player."""

    _animations = None

    def __init__(self, zone_left, zone_right, center_y):
        self._load_animations()
        self.zone_left = zone_left
        self.zone_right = zone_right
        self.rect = pygame.Rect(0, 0, 26, 28)
        self.rect.center = (
            (zone_left + zone_right) // 2,
            center_y,
        )
        self.position = pygame.Vector2(self.rect.topleft)
        self.health = CROW_MAX_HEALTH
        self.max_health = CROW_MAX_HEALTH
        self.facing_right = False
        self.state = "idle"
        self.animation_time = 0.0
        self.attack_cooldown_left = 0.0
        self.knockback_velocity = 0.0

    @classmethod
    def _load_animations(cls):
        if cls._animations is not None:
            return

        left = {
            "idle": cls._load_folder("idle", 3),
            "fly": cls._load_folder("fly", 2),
        }
        right = {
            state: [
                pygame.transform.flip(frame, True, False)
                for frame in frames
            ]
            for state, frames in left.items()
        }
        cls._animations = {"left": left, "right": right}

    @classmethod
    def _load_folder(cls, folder_name, frame_count):
        return [
            pygame.image.load(
                CROW_PATH / folder_name / f"{frame_number}.png"
            ).convert_alpha()
            for frame_number in range(frame_count)
        ]

    @property
    def alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health = max(0, self.health - max(0, amount))

    def apply_knockback(self, distance):
        """Make a kicked crow visibly fly backward."""
        self.knockback_velocity = distance * CROW_KNOCKBACK_STRENGTH

    def update(self, delta_time, player):
        if not self.alive:
            return

        self.attack_cooldown_left = max(
            0.0, self.attack_cooldown_left - delta_time
        )
        self.animation_time += delta_time

        if abs(self.knockback_velocity) > 1:
            self.state = "fly"
            self.position.x += self.knockback_velocity * delta_time
            self.position.x = max(
                self.zone_left,
                min(self.position.x, self.zone_right - self.rect.width),
            )
            self.rect.topleft = (
                round(self.position.x),
                round(self.position.y),
            )
            deceleration = CROW_KNOCKBACK_DECELERATION * delta_time
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

        if not self.zone_left <= player.rect.centerx <= self.zone_right:
            self.state = "idle"
            return

        offset = pygame.Vector2(player.rect.center) - pygame.Vector2(
            self.rect.center
        )
        distance = offset.length()
        if offset.x != 0:
            self.facing_right = offset.x > 0

        if distance > 20:
            self.state = "fly"
            movement = offset.normalize() * CROW_SPEED * delta_time
            self.position += movement
            self.position.x = max(
                self.zone_left,
                min(self.position.x, self.zone_right - self.rect.width),
            )
            self.position.y = max(
                20, min(self.position.y, 275 - self.rect.height)
            )
            self.rect.topleft = (round(self.position.x), round(self.position.y))
        else:
            self.state = "idle"

        if (
            self.rect.colliderect(player.rect)
            and self.attack_cooldown_left <= 0
        ):
            if player.take_damage(CROW_ATTACK_DAMAGE):
                self.attack_cooldown_left = CROW_ATTACK_COOLDOWN

    def draw(self, screen, camera_x):
        direction = "right" if self.facing_right else "left"
        frames = self._animations[direction][self.state]
        frame_index = int(
            self.animation_time * CROW_ANIMATION_SPEED
        ) % len(frames)
        image = frames[frame_index]
        draw_rect = image.get_rect(
            center=(
                self.rect.centerx - round(camera_x),
                self.rect.centery,
            )
        )
        screen.blit(image, draw_rect)
