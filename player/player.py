from pathlib import Path

import pygame

from music_manager import play_sound_effect


PLAYER_SPEED = 180
GRAVITY = 1000
JUMP_SPEED = 300
IDLE_ANIMATION_SPEED = 8
ATTACK_ANIMATION_SPEED = 12
ATTACK_FRAME_COUNT = 5
KICK_ANIMATION_SPEED = 12
KICK_FRAME_COUNT = 4
FIRE_ANIMATION_SPEED = 12
FIRE_FRAME_COUNT = 9
DAMAGE_ANIMATION_SPEED = 12
DAMAGE_FRAME_COUNT = 3
DEATH_ANIMATION_SPEED = 10
DEATH_FRAME_COUNT = 11
STARTING_HEALTH = 50
STARTING_ATTACK_DAMAGE = 20
POINTS_PER_LEVEL = 50
MAX_LEVEL = 10
HEALTH_PER_LEVEL = 10
ATTACK_DAMAGE_PER_LEVEL = 5
DEATH_POINT_PENALTY = 10
ATTACK_RANGE = 20
FIRE_RANGE = 100
FIRE_DAMAGE = 25
KICK_RANGE = 44
KICK_KNOCKBACK = 115
KICK_DURATION = KICK_FRAME_COUNT / KICK_ANIMATION_SPEED
KICK_IMPACT_TIME = (KICK_FRAME_COUNT - 2) / KICK_ANIMATION_SPEED
KICK_COOLDOWN = 0.55
FLIGHT_DURATION = 30.0
FLIGHT_SPEED = 180
FLIGHT_IDLE_ANIMATION_SPEED = 3
FLIGHT_DASH_SPEED = 520
FLIGHT_DASH_DURATION = 0.16
FLIGHT_DASH_COOLDOWN = 0.75
ATTACK_DURATION = ATTACK_FRAME_COUNT / ATTACK_ANIMATION_SPEED
ATTACK_COOLDOWN = 0.5
FIRE_DURATION = FIRE_FRAME_COUNT / FIRE_ANIMATION_SPEED
FIRE_COOLDOWN = 1.0
COMBAT_MESSAGE_DURATION = 2.0
HEALTH_POTION_HEAL = 15
DAMAGE_DURATION = DAMAGE_FRAME_COUNT / DAMAGE_ANIMATION_SPEED
DEATH_DURATION = DEATH_FRAME_COUNT / DEATH_ANIMATION_SPEED

IDLE_PATH = Path(__file__).parent / "idle"
ATTACK_PATH = Path(__file__).parent / "attack"
KICK_PATH = Path(__file__).parent / "kick"
FIRE_PATH = Path(__file__).parent / "fire"
DAMAGE_PATH = Path(__file__).parent / "damage"
DEATH_PATH = Path(__file__).parent / "death"
FLYING_PATH = Path(__file__).parent / "flying"
FIRE_SOUND_PATH = Path(__file__).parent / "fire.mp3"

SHIELD_HEALTH_CAPS = {
    1: 60,
    2: 80,
    3: 100,
    4: 120,
    5: 140,
    6: 160,
    7: 180,
    8: 200,
    9: 220,
    10: 240,
}
SHIELD_HEALTH_INCREASE = 10
SHIELD_EMBERSTONE_COST = 1

# Add future magic recipes to this array.
MAGIC_RECIPES = [
    {
        "name": "Fire Magic",
        "required_level": 2,
        "emberstone_cost": 2,
        "uses_per_craft": 3,
    },
    {
        "name": "Fly Magic",
        "required_level": 3,
        "wind_crystal_cost": 2,
        "uses_per_craft": 1,
    },
]


class Player:
    def __init__(self, x, y):
        self.idle_right = self._load_idle_frames()
        self.idle_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.idle_right
        ]
        self.attack_right = self._load_attack_frames()
        self.attack_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.attack_right
        ]
        self.kick_right = self._load_frames(KICK_PATH, KICK_FRAME_COUNT)
        self.kick_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.kick_right
        ]
        self.fire_right = self._load_frames(FIRE_PATH, FIRE_FRAME_COUNT)
        self.fire_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.fire_right
        ]
        self.damage_right = self._load_frames(
            DAMAGE_PATH, DAMAGE_FRAME_COUNT
        )
        self.damage_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.damage_right
        ]
        self.death_right = self._load_frames(
            DEATH_PATH, DEATH_FRAME_COUNT
        )
        self.death_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.death_right
        ]
        self.flying_right = self._load_frames(FLYING_PATH, 6)
        self.flying_left = [
            pygame.transform.flip(frame, True, False)
            for frame in self.flying_right
        ]

        # The collision box is slightly narrower than the sprite.
        self.rect = pygame.Rect(x, y, 24, 40)
        self.position = pygame.Vector2(self.rect.topleft)
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.animation_time = 0.0

        # Combat stats. level_up() can increase both values later.
        self.level = 1
        self.max_health = STARTING_HEALTH
        self.health = self.max_health
        self.attack_damage = STARTING_ATTACK_DAMAGE
        self.points = 0
        self.next_level_points = POINTS_PER_LEVEL
        self.emberstones = 0
        self.total_emberstones_collected = 0
        self.wind_crystals = 0
        self.health_potions = 0
        self.held_magic = []
        self.magic_uses = {
            "Fire Magic": 0,
            "Fly Magic": 0,
        }
        self.flight_time_left = 0.0
        self.flight_dash_time_left = 0.0
        self.flight_dash_cooldown_left = 0.0
        self.flight_horizontal_direction = 0
        self.flight_vertical_direction = 0
        self.money = 0
        self.map3_cleared = False
        self.map2_cleared = False
        self.intro_dialogue_seen = False
        self.slime_video_seen = False
        self.toad_video_seen = False
        self.flying_video_seen = False
        self.map4_cleared = False
        self.map6_cleared = False
        self.map7_painting_angle = 0
        self.map7_painting_solved = False
        self.map7_clock_hour = 12
        self.map7_clock_minute = 0
        self.map7_clock_solved = False
        self.map7_candles_lit = []
        self.map7_candles_solved = False
        self.map7_mission_complete = False
        self.map7_quest_accepted = False
        self.map7_ghost_intro_seen = False
        self.map7_ghost_reward_seen = False
        self.map7_has_book = False
        self.map7_book_delivered = False
        self.arcana_magic_mastered = False
        self.map8_cleared = False
        self.final_praise_seen = False
        self.map7_puzzle_time_left = 90.0
        self.map7_puzzle_timer_started = False
        self.active_screen = None
        self.craft_message = ""

        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.attack_has_dealt_damage = False
        self.kick_time_left = 0.0
        self.kick_cooldown_left = 0.0
        self.kick_has_dealt_damage = False
        self.fire_time_left = 0.0
        self.fire_cooldown_left = 0.0
        self.fire_has_dealt_damage = False
        self.combat_message = ""
        self.combat_message_time_left = 0.0
        self.damage_time_left = 0.0
        self.death_animation_time = 0.0
        self.death_animation_finished = False
        self.ui_font = pygame.font.Font(None, 20)
        self.menu_font = pygame.font.Font(None, 24)
        self.menu_title_font = pygame.font.Font(None, 34)

    def _load_idle_frames(self):
        frames = []

        for frame_number in range(6):
            path = IDLE_PATH / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def _load_attack_frames(self):
        frames = []

        for frame_number in range(ATTACK_FRAME_COUNT):
            path = ATTACK_PATH / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def _load_frames(self, folder, frame_count):
        frames = []

        for frame_number in range(frame_count):
            path = folder / f"{frame_number}.png"
            frames.append(pygame.image.load(path).convert_alpha())

        return frames

    def handle_event(
        self,
        event,
        allow_flight_activation=False,
        require_active_flight=False,
        allow_flight_dash=False,
    ):
        """Handle player controls and return True when an event is consumed."""
        if event.type != pygame.KEYDOWN:
            return False

        if self.is_dead or self.is_taking_damage:
            return False

        if event.key == pygame.K_c:
            self.active_screen = (
                None if self.active_screen == "craft" else "craft"
            )
            self.craft_message = ""
            return True

        if event.key == pygame.K_m:
            self.active_screen = (
                None if self.active_screen == "menu" else "menu"
            )
            return True

        if event.key == pygame.K_ESCAPE and self.active_screen is not None:
            self.active_screen = None
            return True

        if self.active_screen == "craft":
            if event.key in (pygame.K_1, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.craft_magic("Fire Magic")
            elif event.key == pygame.K_2:
                self.craft_magic("Fly Magic")
            return True

        if self.active_screen is not None:
            return True

        if event.key == pygame.K_h:
            self.use_health_potion()
            return True

        if (
            allow_flight_dash
            and self.is_flying
            and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT)
            and self.flight_dash_cooldown_left <= 0
            and not self.is_casting_fire
        ):
            self.flight_dash_time_left = FLIGHT_DASH_DURATION
            self.flight_dash_cooldown_left = FLIGHT_DASH_COOLDOWN
            return True

        if event.key in (pygame.K_w, pygame.K_UP) and self.on_ground:
            self.velocity_y = -JUMP_SPEED
            self.on_ground = False
            return True

        if (
            event.key == pygame.K_g
            and allow_flight_activation
            and (self.is_flying or not require_active_flight)
        ):
            if (
                not self.arcana_magic_mastered
                and self.magic_uses.get("Fly Magic", 0) <= 0
            ):
                self.combat_message = (
                    "No Fly Magic spells remaining! Craft one at level 3."
                )
                self.combat_message_time_left = COMBAT_MESSAGE_DURATION
                return True

            self.flight_time_left += FLIGHT_DURATION
            self.velocity_y = 0.0
            self.on_ground = False
            if not self.arcana_magic_mastered:
                self._consume_magic_use("Fly Magic")
            return True

        if (
            event.key == pygame.K_f
            and not self.arcana_magic_mastered
            and self.magic_uses.get("Fire Magic", 0) <= 0
        ):
            self.combat_message = "No Fire Magic attacks remaining!"
            self.combat_message_time_left = COMBAT_MESSAGE_DURATION
            return True

        if (
            event.key == pygame.K_f
            and (
                self.arcana_magic_mastered
                or self.magic_uses.get("Fire Magic", 0) > 0
            )
            and self.fire_cooldown_left <= 0
            and not self.is_attacking
            and not self.is_casting_fire
        ):
            self.fire_time_left = FIRE_DURATION
            self.fire_cooldown_left = FIRE_COOLDOWN
            self.fire_has_dealt_damage = False
            play_sound_effect(FIRE_SOUND_PATH, volume=0.50)
            if not self.arcana_magic_mastered:
                self._consume_magic_use("Fire Magic")
            return True

        if (
            event.key == pygame.K_k
            and self.kick_cooldown_left <= 0
            and not self.is_attacking
            and not self.is_casting_fire
            and not self.is_kicking
        ):
            self.kick_time_left = KICK_DURATION
            self.kick_cooldown_left = KICK_COOLDOWN
            self.kick_has_dealt_damage = False
            return True

        if (
            event.key == pygame.K_SPACE
            and self.attack_cooldown_left <= 0
            and not self.is_casting_fire
            and not self.is_kicking
        ):
            self.attack_time_left = ATTACK_DURATION
            self.attack_cooldown_left = ATTACK_COOLDOWN
            self.attack_has_dealt_damage = False
            return True

        return False

    @property
    def ui_open(self):
        return self.active_screen is not None

    @property
    def craftable_magic(self):
        return [
            recipe["name"]
            for recipe in MAGIC_RECIPES
            if self.level >= recipe["required_level"]
        ]

    @property
    def collected_drops(self):
        """Compatibility alias; Map 2 drops are now Emberstones."""
        return self.emberstones

    def craft_magic(self, magic_name):
        if self.arcana_magic_mastered and magic_name in (
            "Fire Magic",
            "Fly Magic",
        ):
            self.craft_message = (
                f"{magic_name} is permanently mastered. No stones needed."
            )
            return True

        recipe = next(
            (
                item
                for item in MAGIC_RECIPES
                if item["name"] == magic_name
            ),
            None,
        )

        if recipe is None:
            self.craft_message = "Unknown magic."
            return False
        if self.level < recipe["required_level"]:
            self.craft_message = (
                f"Unlocks at level {recipe['required_level']}."
            )
            return False
        emberstone_cost = recipe.get("emberstone_cost", 0)
        wind_crystal_cost = recipe.get("wind_crystal_cost", 0)
        if self.emberstones < emberstone_cost:
            self.craft_message = (
                f"Need {emberstone_cost} Emberstones."
            )
            return False
        if self.wind_crystals < wind_crystal_cost:
            self.craft_message = (
                f"Need {wind_crystal_cost} Wind Crystals."
            )
            return False

        self.emberstones -= emberstone_cost
        self.wind_crystals -= wind_crystal_cost
        self.held_magic.append(magic_name)
        uses_added = recipe.get("uses_per_craft", 1)
        self.magic_uses[magic_name] = (
            self.magic_uses.get(magic_name, 0) + uses_added
        )
        self.craft_message = (
            f"Crafted {magic_name}! +{uses_added} uses"
        )
        return True

    @property
    def shield_health_cap(self):
        return SHIELD_HEALTH_CAPS[min(self.level, MAX_LEVEL)]

    def craft_shield_upgrade(self):
        """Improve maximum health without exceeding the level cap."""
        if self.max_health >= self.shield_health_cap:
            self.craft_message = (
                f"Level {self.level} health is capped at "
                f"{self.shield_health_cap}."
            )
            return False
        if self.emberstones < SHIELD_EMBERSTONE_COST:
            self.craft_message = "Need 1 Emberstone for a shield upgrade."
            return False

        self.emberstones -= SHIELD_EMBERSTONE_COST
        increase = min(
            SHIELD_HEALTH_INCREASE,
            self.shield_health_cap - self.max_health,
        )
        self.max_health += increase
        self.health += increase
        self.craft_message = (
            f"Shield improved! Maximum health is now {self.max_health}."
        )
        return True

    def _consume_magic_use(self, magic_name):
        remaining_uses = max(0, self.magic_uses.get(magic_name, 0) - 1)
        self.magic_uses[magic_name] = remaining_uses

        recipe = next(
            (
                item
                for item in MAGIC_RECIPES
                if item["name"] == magic_name
            ),
            None,
        )
        uses_per_craft = recipe.get("uses_per_craft", 1) if recipe else 1
        copies_needed = (
            remaining_uses + uses_per_craft - 1
        ) // uses_per_craft

        while self.held_magic.count(magic_name) > copies_needed:
            self.held_magic.remove(magic_name)

    def sell_magic(self, magic_name, amount, price_per_spell):
        """Sell complete crafted spells and remove their remaining uses."""
        amount = max(0, int(amount))
        price_per_spell = max(0, int(price_per_spell))
        if amount == 0 or self.held_magic.count(magic_name) < amount:
            return False

        recipe = next(
            (
                item
                for item in MAGIC_RECIPES
                if item["name"] == magic_name
            ),
            None,
        )
        uses_per_craft = recipe.get("uses_per_craft", 1) if recipe else 1

        for _ in range(amount):
            self.held_magic.remove(magic_name)
        self.magic_uses[magic_name] = max(
            0,
            self.magic_uses.get(magic_name, 0) - amount * uses_per_craft,
        )
        self.money += amount * price_per_spell
        return True

    def get_attack_rect(self):
        """Return the attack area in world coordinates."""
        if self.facing_right:
            return pygame.Rect(
                self.rect.left,
                self.rect.top,
                self.rect.width + ATTACK_RANGE,
                self.rect.height,
            )

        return pygame.Rect(
            self.rect.left - ATTACK_RANGE,
            self.rect.top,
            self.rect.width + ATTACK_RANGE,
            self.rect.height,
        )

    def get_fire_attack_rect(self):
        """Return the 80-pixel Fire Magic area in world coordinates."""
        if self.facing_right:
            return pygame.Rect(
                self.rect.left,
                self.rect.top,
                self.rect.width + FIRE_RANGE,
                self.rect.height,
            )

        return pygame.Rect(
            self.rect.left - FIRE_RANGE,
            self.rect.top,
            self.rect.width + FIRE_RANGE,
            self.rect.height,
        )

    def get_kick_rect(self):
        """Return the kick area, including enemies overlapping the player."""
        if self.facing_right:
            return pygame.Rect(
                self.rect.left,
                self.rect.top,
                self.rect.width + KICK_RANGE,
                self.rect.height,
            )

        return pygame.Rect(
            self.rect.left - KICK_RANGE,
            self.rect.top,
            self.rect.width + KICK_RANGE,
            self.rect.height,
        )

    @property
    def is_attacking(self):
        return self.attack_time_left > 0

    @property
    def is_casting_fire(self):
        return self.fire_time_left > 0

    @property
    def is_kicking(self):
        return self.kick_time_left > 0

    @property
    def is_flying(self):
        return self.flight_time_left > 0

    @property
    def is_taking_damage(self):
        return self.damage_time_left > 0 and not self.is_dead

    @property
    def is_dead(self):
        return self.health <= 0

    def _update_attack(self, delta_time, damage_targets):
        self.attack_cooldown_left = max(
            0, self.attack_cooldown_left - delta_time
        )

        if not self.is_attacking:
            return

        if not self.attack_has_dealt_damage:
            attack_rect = self.get_attack_rect()

            for target in damage_targets:
                take_damage = getattr(target, "take_damage", None)
                target_rect = getattr(target, "rect", None)

                if (
                    target_rect is not None
                    and callable(take_damage)
                    and attack_rect.colliderect(target_rect)
                ):
                    take_damage(self.attack_damage)

            # Each target can only be damaged once per attack press.
            self.attack_has_dealt_damage = True

        self.attack_time_left = max(0, self.attack_time_left - delta_time)

    def _update_fire_attack(self, delta_time, damage_targets):
        self.fire_cooldown_left = max(
            0, self.fire_cooldown_left - delta_time
        )

        if not self.is_casting_fire:
            return

        if not self.fire_has_dealt_damage:
            fire_rect = self.get_fire_attack_rect()

            for target in damage_targets:
                take_damage = getattr(target, "take_damage", None)
                take_fire_damage = getattr(
                    target, "take_fire_damage", None
                )
                target_rect = getattr(target, "rect", None)

                if (
                    target_rect is not None
                    and fire_rect.colliderect(target_rect)
                ):
                    if callable(take_fire_damage):
                        take_fire_damage(FIRE_DAMAGE)
                    elif callable(take_damage):
                        take_damage(FIRE_DAMAGE)

            self.fire_has_dealt_damage = True

        self.fire_time_left = max(0, self.fire_time_left - delta_time)

    def _update_kick(self, delta_time, damage_targets):
        self.kick_cooldown_left = max(
            0, self.kick_cooldown_left - delta_time
        )

        if not self.is_kicking:
            return

        remaining_time = self.kick_time_left - delta_time
        animation_finished = remaining_time <= 0.000001
        self.kick_time_left = 0 if animation_finished else remaining_time
        elapsed_time = KICK_DURATION - max(0.0, remaining_time)

        if (
            not self.kick_has_dealt_damage
            and elapsed_time >= KICK_IMPACT_TIME
        ):
            kick_rect = self.get_kick_rect()

            for target in damage_targets:
                target_rect = getattr(target, "rect", None)
                take_damage = getattr(target, "take_damage", None)
                if (
                    target_rect is not None
                    and callable(take_damage)
                    and kick_rect.colliderect(target_rect)
                ):
                    # A kick uses the same level-scaled damage as SPACE.
                    take_damage(self.attack_damage)
                    apply_knockback = getattr(target, "apply_knockback", None)
                    if callable(apply_knockback):
                        # Always launch the enemy away from the player. This
                        # also handles enemies overlapping the player's body.
                        if target_rect.centerx > self.rect.centerx:
                            direction = 1
                        elif target_rect.centerx < self.rect.centerx:
                            direction = -1
                        else:
                            direction = 1 if self.facing_right else -1
                        apply_knockback(direction * KICK_KNOCKBACK)

            self.kick_has_dealt_damage = True

    def take_damage(self, amount):
        """Reduce player health without allowing it to go below zero."""
        if self.is_dead or self.is_taking_damage:
            return False

        damage = max(0, amount)
        if damage == 0:
            return False

        kick_was_active = self.is_kicking
        self.health = max(0, self.health - damage)
        self.attack_time_left = 0.0
        self.attack_has_dealt_damage = False
        self.fire_time_left = 0.0
        self.fire_has_dealt_damage = False
        self.combat_message = ""
        self.combat_message_time_left = 0.0

        if self.is_dead:
            self.kick_time_left = 0.0
            self.kick_has_dealt_damage = False
            self.damage_time_left = 0.0
            self.death_animation_time = 0.0
            self.death_animation_finished = False
            self.active_screen = None
        else:
            # Contact damage must not cancel a kick before its final-frame hit.
            if not kick_was_active:
                self.kick_time_left = 0.0
                self.kick_has_dealt_damage = False
            self.damage_time_left = DAMAGE_DURATION

        return True

    def level_up(self, health_increase, attack_damage_increase):
        """Increase level and apply progression values chosen by the game."""
        health_increase = max(0, health_increase)
        attack_damage_increase = max(0, attack_damage_increase)

        self.level += 1
        self.max_health += health_increase
        self.health += health_increase
        self.attack_damage += attack_damage_increase

    def add_points(self, amount):
        """Add score and process every reached level threshold."""
        self.points += max(0, amount)

        while (
            self.level < MAX_LEVEL
            and self.points >= self.next_level_points
        ):
            self.level_up(HEALTH_PER_LEVEL, ATTACK_DAMAGE_PER_LEVEL)
            self.next_level_points += POINTS_PER_LEVEL

    def lose_points(self, amount):
        self.points = max(0, self.points - max(0, amount))

    def collect_emberstones(self, amount=1):
        amount = max(0, amount)
        self.emberstones += amount
        self.total_emberstones_collected += amount

    def collect_wind_crystals(self, amount=1):
        self.wind_crystals += max(0, amount)

    def collect_drops(self, amount=1):
        """Compatibility method for existing Map 2 code."""
        self.collect_emberstones(amount)

    def heal(self, amount):
        """Restore health without exceeding the player's maximum health."""
        old_health = self.health
        self.health = min(self.max_health, self.health + max(0, amount))
        return self.health - old_health

    def collect_health_potions(self, amount=1):
        amount = max(0, amount)
        self.health_potions += amount
        if amount > 0:
            self.combat_message = "Potion collected - press H to use"
            self.combat_message_time_left = COMBAT_MESSAGE_DURATION

    def use_health_potion(self):
        if self.health_potions <= 0:
            self.combat_message = "No Health Potions remaining!"
            self.combat_message_time_left = COMBAT_MESSAGE_DURATION
            return False
        if self.health >= self.max_health:
            self.combat_message = "Health is already full."
            self.combat_message_time_left = COMBAT_MESSAGE_DURATION
            return False

        healed = self.heal(HEALTH_POTION_HEAL)
        self.health_potions -= 1
        self.combat_message = f"Health Potion used: +{healed} HP"
        self.combat_message_time_left = COMBAT_MESSAGE_DURATION
        return True

    def set_position(self, x, y):
        """Move to a map spawn without resetting player stats."""
        self.rect.topleft = (x, y)
        self.position.update(self.rect.topleft)
        self.velocity_y = 0.0
        self.on_ground = False
        self.attack_time_left = 0.0
        self.attack_cooldown_left = 0.0
        self.fire_time_left = 0.0
        self.fire_cooldown_left = 0.0
        self.fire_has_dealt_damage = False
        self.kick_time_left = 0.0
        self.kick_cooldown_left = 0.0
        self.kick_has_dealt_damage = False
        self.damage_time_left = 0.0
        self.flight_dash_time_left = 0.0
        self.flight_dash_cooldown_left = 0.0
        self.flight_horizontal_direction = 0
        self.flight_vertical_direction = 0
        self.death_animation_time = 0.0
        self.death_animation_finished = False
        self.active_screen = None
        self.craft_message = ""

    def respawn(self, x, y):
        """Restore health while preserving level, points, and drops."""
        self.lose_points(DEATH_POINT_PENALTY)
        self.health = self.max_health
        self.flight_time_left = 0.0
        self.set_position(x, y)

    def update(
        self,
        delta_time,
        platform_rects,
        map_width,
        damage_targets=(),
        solid_rects=(),
        map_height=320,
        use_flying_sprites=False,
    ):
        if self.is_dead:
            self.death_animation_time = min(
                DEATH_DURATION,
                self.death_animation_time + delta_time,
            )
            self.death_animation_finished = (
                self.death_animation_time >= DEATH_DURATION
            )
            return

        self.flight_time_left = max(
            0.0, self.flight_time_left - delta_time
        )
        self.combat_message_time_left = max(
            0.0, self.combat_message_time_left - delta_time
        )
        self.flight_dash_cooldown_left = max(
            0.0, self.flight_dash_cooldown_left - delta_time
        )

        keys = pygame.key.get_pressed()
        direction = 0

        if (
            not self.is_taking_damage
            and not self.is_casting_fire
            and not self.is_kicking
        ):
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                direction -= 1
                self.facing_right = False

            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                direction += 1
                self.facing_right = True

        # Horizontal player movement.
        self.position.x += direction * PLAYER_SPEED * delta_time
        self.position.x = max(
            0, min(self.position.x, map_width - self.rect.width)
        )
        self.rect.x = round(self.position.x)

        # Solid object sides block walking but can be cleared by jumping.
        if direction != 0:
            ordered_solids = sorted(
                solid_rects,
                key=lambda rect: rect.x,
                reverse=direction < 0,
            )
            for solid_rect in ordered_solids:
                if not self.rect.colliderect(solid_rect):
                    continue

                if direction > 0:
                    self.rect.right = solid_rect.left
                else:
                    self.rect.left = solid_rect.right
                self.position.x = self.rect.x

        if self.is_flying:
            vertical_direction = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                vertical_direction -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                vertical_direction += 1

            self.flight_horizontal_direction = direction
            self.flight_vertical_direction = vertical_direction

            if use_flying_sprites and self.flight_dash_time_left > 0:
                dash_direction = 1 if self.facing_right else -1
                self.position.x += (
                    dash_direction * FLIGHT_DASH_SPEED * delta_time
                )
                self.position.x = max(
                    0, min(self.position.x, map_width - self.rect.width)
                )
                self.rect.x = round(self.position.x)
                self.flight_dash_time_left = max(
                    0.0, self.flight_dash_time_left - delta_time
                )

            self.velocity_y = 0.0
            self.position.y += (
                vertical_direction * FLIGHT_SPEED * delta_time
            )
            self.position.y = max(
                0, min(self.position.y, map_height - self.rect.height)
            )
            self.rect.y = round(self.position.y)
            self.on_ground = False

            self.animation_time += delta_time
            self._update_fire_attack(delta_time, damage_targets)
            self._update_kick(delta_time, damage_targets)
            if self.is_taking_damage:
                self.damage_time_left = max(
                    0, self.damage_time_left - delta_time
                )
            elif not self.is_casting_fire and not self.is_kicking:
                self._update_attack(delta_time, damage_targets)
            return

        self.flight_dash_time_left = 0.0
        self.flight_horizontal_direction = 0
        self.flight_vertical_direction = 0

        # Gravity and landing collision for platforms and solid objects.
        old_bottom = self.rect.bottom
        self.velocity_y += GRAVITY * delta_time
        self.position.y += self.velocity_y * delta_time
        self.rect.y = round(self.position.y)
        self.on_ground = False

        if self.velocity_y >= 0:
            for platform_rect in (*platform_rects, *solid_rects):
                horizontally_overlapping = (
                    self.rect.right > platform_rect.left
                    and self.rect.left < platform_rect.right
                )
                crossed_platform_top = (
                    old_bottom <= platform_rect.top
                    and self.rect.bottom >= platform_rect.top
                )

                if horizontally_overlapping and crossed_platform_top:
                    self.rect.bottom = platform_rect.top
                    self.position.y = self.rect.y
                    self.velocity_y = 0
                    self.on_ground = True
                    break

        self.animation_time += delta_time
        self._update_fire_attack(delta_time, damage_targets)
        self._update_kick(delta_time, damage_targets)
        if self.is_taking_damage:
            self.damage_time_left = max(
                0, self.damage_time_left - delta_time
            )
        elif not self.is_casting_fire and not self.is_kicking:
            self._update_attack(delta_time, damage_targets)

    def draw(self, screen, camera_x, use_flying_sprites=False):
        drawing_fire = False

        if self.is_dead:
            frames = (
                self.death_right if self.facing_right else self.death_left
            )
            frame_index = min(
                int(self.death_animation_time * DEATH_ANIMATION_SPEED),
                len(frames) - 1,
            )
        elif self.is_kicking:
            frames = (
                self.kick_right if self.facing_right else self.kick_left
            )
            kick_elapsed = KICK_DURATION - self.kick_time_left
            frame_index = min(
                int(kick_elapsed * KICK_ANIMATION_SPEED),
                len(frames) - 1,
            )
        elif self.is_taking_damage:
            frames = (
                self.damage_right
                if self.facing_right
                else self.damage_left
            )
            damage_elapsed = DAMAGE_DURATION - self.damage_time_left
            frame_index = min(
                int(damage_elapsed * DAMAGE_ANIMATION_SPEED),
                len(frames) - 1,
            )
        elif self.is_casting_fire:
            drawing_fire = True
            frames = (
                self.fire_right if self.facing_right else self.fire_left
            )
            fire_elapsed = FIRE_DURATION - self.fire_time_left
            frame_index = min(
                int(fire_elapsed * FIRE_ANIMATION_SPEED),
                len(frames) - 1,
            )
        elif self.is_attacking:
            frames = (
                self.attack_right if self.facing_right else self.attack_left
            )
            attack_elapsed = ATTACK_DURATION - self.attack_time_left
            frame_index = min(
                int(attack_elapsed * ATTACK_ANIMATION_SPEED),
                len(frames) - 1,
            )
        elif use_flying_sprites and self.is_flying:
            frames = (
                self.flying_right if self.facing_right else self.flying_left
            )
            if self.flight_dash_time_left > 0:
                frame_index = 3
            elif self.flight_vertical_direction < 0:
                frame_index = 4
            elif self.flight_horizontal_direction != 0:
                frame_index = 5
            else:
                # Frame 0 hovers; frames 1 and 2 add the idle/reading motion.
                hover_cycle = (0, 1, 0, 2)
                frame_index = hover_cycle[
                    int(
                        self.animation_time * FLIGHT_IDLE_ANIMATION_SPEED
                    ) % len(hover_cycle)
                ]
        else:
            frames = self.idle_right if self.facing_right else self.idle_left
            frame_index = int(
                self.animation_time * IDLE_ANIMATION_SPEED
            ) % len(frames)

        image = frames[frame_index]

        # Keep differently sized animation frames aligned at the feet.
        player_screen_x = self.rect.centerx - round(camera_x)
        if drawing_fire and self.facing_right:
            draw_rect = image.get_rect(
                bottomleft=(player_screen_x - 16, self.rect.bottom)
            )
        elif drawing_fire:
            draw_rect = image.get_rect(
                bottomright=(player_screen_x + 16, self.rect.bottom)
            )
        else:
            draw_rect = image.get_rect(
                midbottom=(player_screen_x, self.rect.bottom)
            )
        screen.blit(image, draw_rect)

    def draw_health_bar(self, screen):
        """Draw player health in screen coordinates, independent of camera."""
        bar_x = 16
        bar_y = 16
        bar_width = 180
        bar_height = 16
        health_ratio = self.health / self.max_health

        if health_ratio < 0.25:
            health_color = (215, 55, 55)
        elif health_ratio <= 0.50:
            health_color = (235, 200, 55)
        else:
            health_color = (45, 190, 75)

        pygame.draw.rect(
            screen, (35, 35, 35), (bar_x, bar_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            screen,
            health_color,
            (bar_x, bar_y, round(bar_width * health_ratio), bar_height),
        )
        pygame.draw.rect(
            screen, (245, 245, 245), (bar_x, bar_y, bar_width, bar_height), 2
        )

        label = self.ui_font.render(
            f"HP {self.health}/{self.max_health}   LV {self.level}",
            True,
            (255, 255, 255),
        )
        screen.blit(label, (bar_x + 4, bar_y - 1))

        points_text = (
            f"Points: {self.points} (MAX LEVEL)"
            if self.level >= MAX_LEVEL
            else f"Points: {self.points}/{self.next_level_points}"
        )
        points_label = self.ui_font.render(
            points_text,
            True,
            (255, 235, 120),
        )
        screen.blit(points_label, (bar_x, bar_y + bar_height + 3))

        if self.is_flying:
            flight_label = self.ui_font.render(
                f"Flight: {self.flight_time_left:.1f}s",
                True,
                (135, 220, 255),
            )
            screen.blit(
                flight_label,
                (bar_x, bar_y + bar_height + 21),
            )

        if self.combat_message_time_left > 0:
            message_y = bar_y + bar_height + (39 if self.is_flying else 21)
            combat_message = self.ui_font.render(
                self.combat_message,
                True,
                (255, 145, 105),
            )
            screen.blit(combat_message, (bar_x, message_y))

    def draw_active_screen(self, screen):
        if self.active_screen is None:
            return

        screen_width, screen_height = screen.get_size()
        overlay = pygame.Surface(
            (screen_width, screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(70, 20, screen_width - 140, screen_height - 40)
        pygame.draw.rect(screen, (28, 31, 48), panel, border_radius=10)
        pygame.draw.rect(
            screen, (225, 190, 90), panel, 2, border_radius=10
        )

        if self.active_screen == "craft":
            self._draw_crafting_screen(screen, panel)
        else:
            self._draw_player_menu(screen, panel)

    def _draw_crafting_screen(self, screen, panel):
        title = self.menu_title_font.render(
            "Magic Crafting", True, (255, 220, 110)
        )
        screen.blit(title, (panel.x + 24, panel.y + 18))

        unlocked_recipes = [
            recipe
            for recipe in MAGIC_RECIPES
            if self.level >= recipe["required_level"]
        ]
        recipe_y = panel.y + 64
        if not unlocked_recipes:
            no_magic = self.menu_font.render(
                "No magic can be crafted yet.",
                True,
                (160, 160, 170),
            )
            screen.blit(no_magic, (panel.x + 24, recipe_y))
        else:
            for recipe_number, recipe in enumerate(
                unlocked_recipes, start=1
            ):
                if (
                    self.arcana_magic_mastered
                    and recipe["name"] in ("Fire Magic", "Fly Magic")
                ):
                    recipe_line = (
                        f"{recipe_number}. {recipe['name']} - "
                        "MASTERED (UNLIMITED)"
                    )
                elif recipe.get("emberstone_cost"):
                    cost_text = (
                        f"{recipe['emberstone_cost']} Emberstones"
                    )
                    recipe_line = (
                        f"{recipe_number}. {recipe['name']} - "
                        f"{cost_text} "
                        f"(+{recipe.get('uses_per_craft', 1)} uses)"
                    )
                else:
                    cost_text = (
                        f"{recipe.get('wind_crystal_cost', 0)} "
                        "Wind Crystals"
                    )
                    recipe_line = (
                        f"{recipe_number}. {recipe['name']} - "
                        f"{cost_text} "
                        f"(+{recipe.get('uses_per_craft', 1)} uses)"
                    )
                recipe_text = self.menu_font.render(
                    recipe_line, True, (255, 145, 80)
                )
                screen.blit(recipe_text, (panel.x + 24, recipe_y))
                recipe_y += 27

        if self.arcana_magic_mastered:
            instruction = "Book mastery active: Fire and Fly are unlimited."
        elif self.level >= 2:
            instruction = "Press 1 or ENTER for Fire Magic."
        else:
            instruction = "Reach level 2 to unlock Fire Magic."

        instruction_text = self.ui_font.render(
            instruction, True, (220, 220, 225)
        )
        screen.blit(instruction_text, (panel.x + 24, panel.y + 153))

        if self.craft_message:
            message = self.ui_font.render(
                self.craft_message, True, (255, 235, 120)
            )
            screen.blit(message, (panel.x + 24, panel.y + 176))

        close_text = self.ui_font.render(
            "Press C or ESC to close", True, (175, 180, 195)
        )
        screen.blit(close_text, (panel.x + 24, panel.bottom - 28))

    def _draw_player_menu(self, screen, panel):
        title = self.menu_title_font.render(
            "Player Menu", True, (150, 210, 255)
        )
        screen.blit(title, (panel.x + 24, panel.y + 18))

        details = [
            f"Level: {self.level}",
            f"Points: {self.points} / {self.next_level_points}",
            f"Money: {self.money}",
            f"Emberstones: {self.emberstones}",
            f"Wind Crystals: {self.wind_crystals}",
            f"Health Potions: {self.health_potions} (press H to use)",
            "Magic held:",
        ]
        y = panel.y + 54
        for detail in details:
            text = self.menu_font.render(detail, True, (235, 235, 240))
            screen.blit(text, (panel.x + 24, y))
            y += 23

        magic_names = list(dict.fromkeys(self.held_magic))
        if self.arcana_magic_mastered:
            magic_names = list(
                dict.fromkeys(magic_names + ["Fire Magic", "Fly Magic"])
            )
        if not magic_names:
            magic_names = ["None"]

        for magic_name in magic_names:
            if magic_name == "None":
                magic_line = "- None"
            elif self.arcana_magic_mastered and magic_name in (
                "Fire Magic",
                "Fly Magic",
            ):
                magic_line = f"- {magic_name} (UNLIMITED)"
            else:
                copies = self.held_magic.count(magic_name)
                uses = self.magic_uses.get(magic_name, 0)
                magic_line = (
                    f"- {magic_name} x{copies} ({uses} uses left)"
                )
            text = self.ui_font.render(
                magic_line, True, (255, 170, 100)
            )
            screen.blit(text, (panel.x + 42, y))
            y += 20

        close_text = self.ui_font.render(
            "Press M or ESC to close", True, (175, 180, 195)
        )
        screen.blit(close_text, (panel.x + 24, panel.bottom - 28))
