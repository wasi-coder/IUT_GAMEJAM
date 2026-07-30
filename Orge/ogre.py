from pathlib import Path

import pygame

from music_manager import play_sound_effect


OGRE_MAX_HEALTH = 200
OGRE_ATTACK_DAMAGE = (20, 30, 40)
OGRE_SPEED = (62, 88, 112)
OGRE_ATTACK_RANGE = (72, 92, 112)
OGRE_ATTACK_COOLDOWN = 8.0
OGRE_ANIMATION_SPEED = {
    "idle": 6,
    "walk": 9,
    "attack": 11,
}
OGRE_FRAME_COUNTS = {"idle": 4, "walk": 6, "attack": 7}
OGRE_FRAME_SIZE = (216, 120)
OGRE_ATTACK_DURATION = (
    OGRE_FRAME_COUNTS["attack"] / OGRE_ANIMATION_SPEED["attack"]
)
OGRE_PATH = Path(__file__).parent
OGRE_LAUGH_SOUND_PATH = OGRE_PATH / "Orge laugh.mp3"


class OgreBoss:
    """Three-stage final boss that becomes faster and deadlier when hurt."""

    _animations = None

    def __init__(self, center_x, bottom_y, zone_left, zone_right):
        self._load_animations()
        self.zone_left = zone_left
        self.zone_right = zone_right
        self.rect = pygame.Rect(0, 0, 62, 72)
        self.rect.midbottom = (center_x, bottom_y)
        self.position_x = float(self.rect.x)
        self.max_health = OGRE_MAX_HEALTH
        self.health = self.max_health
        self.facing_right = False
        self.state = "idle"
        self.animation_time = 0.0
        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.attack_has_dealt_damage = False
        play_sound_effect(OGRE_LAUGH_SOUND_PATH, volume=0.75)

    @classmethod
    def _load_animations(cls):
        if cls._animations is not None:
            return

        folders = {"idle": "Idle", "walk": "walk", "attack": "Attack"}
        prefixes = {"idle": "ogre-idle", "walk": "ogre-walk", "attack": "ogre-attack"}
        left = {}
        for state, folder in folders.items():
            left[state] = []
            for number in range(1, OGRE_FRAME_COUNTS[state] + 1):
                image = pygame.image.load(
                    OGRE_PATH / folder / f"{prefixes[state]}{number}.png"
                ).convert_alpha()
                left[state].append(
                    pygame.transform.smoothscale(image, OGRE_FRAME_SIZE)
                )
        right = {
            state: [pygame.transform.flip(frame, True, False) for frame in frames]
            for state, frames in left.items()
        }
        cls._animations = {"left": left, "right": right}

    @property
    def alive(self):
        return self.health > 0

    @property
    def rage_stage(self):
        ratio = self.health / self.max_health
        if ratio <= 0.25:
            return 2
        if ratio <= 0.55:
            return 1
        return 0

    def take_damage(self, amount):
        self.health = max(0, self.health - max(0, amount))

    def apply_knockback(self, _distance):
        """The final boss is too heavy to be displaced by a kick."""

    def _start_attack(self):
        self.state = "attack"
        self.animation_time = 0.0
        self.attack_time_left = OGRE_ATTACK_DURATION
        self.attack_has_dealt_damage = False

    def _attack_rect(self):
        stage = self.rage_stage
        horizontal_reach = 74 + stage * 22
        vertical_reach = 56 + stage * 20
        return self.rect.inflate(horizontal_reach * 2, vertical_reach * 2)

    def update(self, delta_time, player):
        if not self.alive:
            return

        self.attack_cooldown_left = max(
            0.0, self.attack_cooldown_left - delta_time
        )
        if self.attack_cooldown_left <= 0.000001:
            self.attack_cooldown_left = 0.0
        offset_x = player.rect.centerx - self.rect.centerx
        self.facing_right = offset_x > 0

        if self.attack_time_left > 0:
            self.state = "attack"
            self.animation_time += delta_time
            elapsed = OGRE_ATTACK_DURATION - self.attack_time_left
            impact_time = 4 / OGRE_ANIMATION_SPEED["attack"]
            if not self.attack_has_dealt_damage and elapsed >= impact_time:
                if self._attack_rect().colliderect(player.rect):
                    player.take_damage(OGRE_ATTACK_DAMAGE[self.rage_stage])
                self.attack_has_dealt_damage = True
            self.attack_time_left = max(0.0, self.attack_time_left - delta_time)
            if self.attack_time_left <= 0:
                # Start the full cooldown only after the swing finishes.
                self.attack_cooldown_left = OGRE_ATTACK_COOLDOWN
            return

        self.animation_time += delta_time
        if player.rect.centerx < self.zone_left:
            self.state = "idle"
            return

        stage = self.rage_stage
        horizontal_distance = abs(offset_x)
        vertical_distance = abs(player.rect.centery - self.rect.centery)
        if (
            horizontal_distance <= OGRE_ATTACK_RANGE[stage]
            and vertical_distance <= 145
        ):
            self.state = "idle"
            if self.attack_cooldown_left <= 0:
                self._start_attack()
            return

        self.state = "walk"
        direction = 1 if offset_x > 0 else -1
        self.position_x += direction * OGRE_SPEED[stage] * delta_time
        self.position_x = max(
            self.zone_left,
            min(self.position_x, self.zone_right - self.rect.width),
        )
        self.rect.x = round(self.position_x)

    def draw(self, screen, camera_x):
        direction = "right" if self.facing_right else "left"
        frames = self._animations[direction][self.state]
        speed = OGRE_ANIMATION_SPEED[self.state]
        frame_index = int(self.animation_time * speed) % len(frames)
        image = frames[frame_index]
        draw_rect = image.get_rect(
            midbottom=(self.rect.centerx - round(camera_x), self.rect.bottom)
        )
        screen.blit(image, draw_rect)

        bar = pygame.Rect(145, 14, 310, 14)
        pygame.draw.rect(screen, (42, 15, 18), bar, border_radius=5)
        width = round(bar.width * self.health / self.max_health)
        color = ((175, 65, 45), (225, 85, 35), (255, 40, 35))[self.rage_stage]
        pygame.draw.rect(
            screen, color, (bar.x, bar.y, width, bar.height), border_radius=5
        )
        pygame.draw.rect(screen, (245, 220, 180), bar, 2, border_radius=5)
        label = pygame.font.Font(None, 22).render(
            f"FINAL BOSS - OGRE  {self.health}/{self.max_health}",
            True,
            (255, 235, 205),
        )
        screen.blit(label, label.get_rect(midtop=(bar.centerx, bar.bottom + 3)))
