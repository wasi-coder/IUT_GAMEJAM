from pathlib import Path
import random

import pygame
from crow import Crow
from Dragon import DragonBoss
from music_manager import play_background_music
from player import Player
from portal import Portal
from start_menu import open_in_game_menu
from .falling_stone import FallingStone, STONE_DAMAGE
from .potion import HealthPotion


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
PLAYER_SPAWN = (90, 100)
MAP6_RETURN_SPAWN = (840, 100)
PORTAL_BOTTOM = 176
ENTRANCE_PORTAL_X = 24
OUTGOING_PORTAL_X = MAP_WIDTH - 24
STONE_SPAWN_INTERVAL = 1.0
MAP_PATH = Path(__file__).parent / "map4.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"

CROW_ZONES = [
    (100, 250, 90),
    (230, 380, 205),
    (360, 510, 105),
    (490, 640, 215),
    (620, 770, 115),
]


def load_map():
    map_surface = pygame.image.load(MAP_PATH).convert()
    if map_surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        map_surface = pygame.transform.scale(
            map_surface, (MAP_WIDTH, MAP_HEIGHT)
        )
    return map_surface


def create_enemies():
    crows = [
        Crow(zone_left, zone_right, center_y)
        for zone_left, zone_right, center_y in CROW_ZONES
    ]
    dragon = DragonBoss(
        center_x=840,
        center_y=145,
        zone_left=700,
        zone_right=MAP_WIDTH,
    )
    return crows, dragon


def map4(player=None, arrived_from=None):
    """Run the bottomless flying map."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Bottomless Flight")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)
    map_surface = load_map()

    spawn_position = (
        MAP6_RETURN_SPAWN if arrived_from == "map6" else PLAYER_SPAWN
    )
    if player is None:
        player = Player(*spawn_position)
    else:
        # set_position deliberately preserves an active flight timer.
        player.set_position(*spawn_position)
    if arrived_from == "map6":
        # The return portal provides enough lift to cross the bottomless map.
        player.flight_time_left = max(player.flight_time_left, 30.0)

    entrance_portal = Portal(
        center_x=ENTRANCE_PORTAL_X,
        bottom_y=PORTAL_BOTTOM,
    )
    outgoing_portal = Portal(
        center_x=OUTGOING_PORTAL_X,
        bottom_y=PORTAL_BOTTOM,
    )
    boss_defeated = player.map4_cleared
    if boss_defeated:
        crows = []
        dragon = None
    else:
        crows, dragon = create_enemies()
    falling_stones = []
    potions = []
    stone_spawn_timer = 0.0

    font = pygame.font.Font(None, 22)
    camera_x = 0.0
    running = True
    next_map = None
    next_arrival_from = None

    while running:
        delta_time = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                # Extra spells extend flight but cannot restart it here.
                event_consumed = player.handle_event(
                    event,
                    allow_flight_activation=True,
                    require_active_flight=True,
                    allow_flight_dash=True,
                )
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    if not open_in_game_menu(clock):
                        running = False

        game_ui_open = player.ui_open
        if not game_ui_open:
            damage_targets = list(crows)
            if dragon is not None:
                damage_targets.append(dragon)
            player.update(
                delta_time,
                (),
                MAP_WIDTH,
                damage_targets,
                map_height=MAP_HEIGHT,
                use_flying_sprites=True,
            )

            stone_spawn_timer += delta_time
            while stone_spawn_timer >= STONE_SPAWN_INTERVAL:
                stone_spawn_timer -= STONE_SPAWN_INTERVAL
                falling_stones.append(
                    FallingStone(random.randint(12, MAP_WIDTH - 12))
                )

            for stone in falling_stones:
                stone.update(delta_time)

            hit_stones = [
                stone
                for stone in falling_stones
                if stone.rect.colliderect(player.rect)
            ]
            for stone in hit_stones:
                player.take_damage(STONE_DAMAGE)
            falling_stones = [
                stone
                for stone in falling_stones
                if stone not in hit_stones
                and not stone.has_left_map(MAP_HEIGHT)
            ]

        entrance_portal.update(delta_time)
        if boss_defeated:
            outgoing_portal.update(delta_time)

        # Match Map 3: keep a defeated enemy visible until the player's
        # attack animation has finished.
        if (
            not player.is_attacking
            and not player.is_casting_fire
            and not player.is_kicking
        ):
            defeated_crows = [crow for crow in crows if not crow.alive]
            potions.extend(
                HealthPotion(crow.rect.centerx, crow.rect.centery)
                for crow in defeated_crows
            )
            crows = [crow for crow in crows if crow.alive]
            if dragon is not None and not dragon.alive:
                potions.extend(
                    HealthPotion(
                        dragon.rect.centerx + offset,
                        dragon.rect.centery,
                    )
                    for offset in (-28, 0, 28)
                )
                dragon = None
                crows.clear()
                boss_defeated = True
                player.map4_cleared = True

        if not game_ui_open and not player.is_dead:
            for crow in crows:
                crow.update(delta_time, player)
            if dragon is not None:
                dragon.update(delta_time, player)

        collected_potions = [
            potion
            for potion in potions
            if player.rect.colliderect(potion.rect)
        ]
        if collected_potions:
            player.collect_health_potions(len(collected_potions))
        potions = [
            potion
            for potion in potions
            if potion not in collected_potions
        ]

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not game_ui_open
            and player.rect.colliderect(entrance_portal.rect)
        ):
            next_map = "map1" if arrived_from == "map1" else "map3"
            next_arrival_from = "map4"
            running = False
        elif (
            boss_defeated
            and not player.is_dead
            and not game_ui_open
            and player.rect.colliderect(outgoing_portal.rect)
        ):
            next_map = "map6"
            next_arrival_from = "map4"
            running = False

        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        entrance_portal.draw(screen, camera_x)
        if boss_defeated:
            outgoing_portal.draw(screen, camera_x)
        for crow in crows:
            crow.draw(screen, camera_x)
        if dragon is not None:
            dragon.draw(screen, camera_x)
        for stone in falling_stones:
            stone.draw(screen, camera_x)
        for potion in potions:
            potion.draw(screen, camera_x)
        player.draw(screen, camera_x, use_flying_sprites=True)
        player.draw_health_bar(screen)

        if not player.is_flying and not player.is_dead:
            warning = font.render(
                "Flight expired - you are falling!",
                True,
                (255, 135, 105),
            )
            warning_rect = warning.get_rect(
                midtop=(SCREEN_WIDTH // 2, 18)
            )
            screen.blit(warning, warning_rect)
        elif not player.is_dead:
            dash_hint = font.render(
                "SHIFT: Air Dash",
                True,
                (185, 225, 255),
            )
            screen.blit(
                dash_hint,
                dash_hint.get_rect(topright=(SCREEN_WIDTH - 16, 18)),
            )

        player.draw_active_screen(screen)
        pygame.display.flip()

    return next_map, player, next_arrival_from
