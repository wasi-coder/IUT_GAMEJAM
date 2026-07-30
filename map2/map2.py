from pathlib import Path
import random

import pygame
from music_manager import play_background_music
from player import Player
from portal import Portal
from slime import Emberstone, Slime
from start_menu import open_in_game_menu
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
PLAYER_SPAWN = (80, 100)
MAP3_RETURN_SPAWN = (MAP_WIDTH - 80, 100)
SLIME_SPAWN_INTERVAL = 5.0
SLIME_POINTS = 5
SLIME_DROP_CHANCE = 0.70
INITIAL_SLIME_POSITIONS = (220, 360, 520, 700, 860)
REQUIRED_EMBERSTONES = 2
REQUIRED_LEVEL = 2

MAP_PATH = Path(__file__).parent / "maps2.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"


def load_map():
    """Load map2.png and make sure it has the required dimensions."""
    map_surface = pygame.image.load(MAP_PATH).convert()

    if map_surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        map_surface = pygame.transform.scale(
            map_surface, (MAP_WIDTH, MAP_HEIGHT)
        )

    return map_surface


def create_platform_rects():
    """Create collision rectangles for every walkable tile."""
    platform_rects = []

    for row_number, row in enumerate(platform):
        for column_number, tile_value in enumerate(row):
            if tile_value == WALKABLE_TILE:
                platform_rects.append(
                    pygame.Rect(
                        column_number * TILE_SIZE,
                        row_number * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                )

    return platform_rects


def create_emberstone(slime, ground_y):
    """Return an Emberstone based on the slime's 70% drop chance."""
    if random.random() < SLIME_DROP_CHANCE:
        return Emberstone(center_x=slime.rect.centerx, bottom_y=ground_y)

    return None


def map2(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Map 2")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)

    map_surface = load_map()
    platform_rects = create_platform_rects()
    entry_spawn = (
        MAP3_RETURN_SPAWN if arrived_from == "map3" else PLAYER_SPAWN
    )
    if player is None:
        player = Player(*entry_spawn)
    else:
        player.set_position(*entry_spawn)

    # Place the return portal above the leftmost platform.
    left_edge_platforms = [
        rect for rect in platform_rects if rect.left == 0
    ]
    portal_bottom = min(
        (rect.top for rect in left_edge_platforms), default=MAP_HEIGHT
    )
    return_portal = Portal(center_x=24, bottom_y=portal_bottom)

    right_edge_platforms = [
        rect for rect in platform_rects if rect.right == MAP_WIDTH
    ]
    exit_portal_bottom = min(
        (rect.top for rect in right_edge_platforms), default=MAP_HEIGHT
    )
    exit_portal = Portal(
        center_x=MAP_WIDTH - 24,
        bottom_y=exit_portal_bottom,
    )

    ground_y = min(
        (rect.top for rect in platform_rects), default=MAP_HEIGHT
    )
    slimes = [
        Slime(center_x=x, bottom_y=ground_y)
        for x in INITIAL_SLIME_POSITIONS
    ]
    emberstones_on_ground = []
    slime_spawn_timer = 0.0

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
                event_consumed = player.handle_event(event)
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    if not open_in_game_menu(clock):
                        running = False

        if not player.ui_open:
            player.update(delta_time, platform_rects, MAP_WIDTH, slimes)
        return_portal.update(delta_time)
        exit_portal.update(delta_time)

        # Keep defeated sprites visible until the attack animation completes.
        if (
            not player.is_attacking
            and not player.is_casting_fire
            and not player.is_kicking
        ):
            defeated_slimes = [
                slime
                for slime in slimes
                if not slime.alive and slime.knockback_air_time <= 0
            ]
            for slime in defeated_slimes:
                player.add_points(SLIME_POINTS)
                emberstone = create_emberstone(slime, ground_y)
                if emberstone is not None:
                    emberstones_on_ground.append(emberstone)

            slimes = [slime for slime in slimes if slime.alive]

        if not player.ui_open and not player.is_dead:
            for slime in slimes:
                slime.update(delta_time, player, MAP_WIDTH)

            slime_spawn_timer += delta_time
            while slime_spawn_timer >= SLIME_SPAWN_INTERVAL:
                slime_spawn_timer -= SLIME_SPAWN_INTERVAL
                random_x = random.randint(100, MAP_WIDTH - 30)
                slimes.append(Slime(center_x=random_x, bottom_y=ground_y))

        collected_emberstones = [
            emberstone
            for emberstone in emberstones_on_ground
            if player.rect.colliderect(emberstone.rect)
        ]
        if collected_emberstones:
            player.collect_emberstones(len(collected_emberstones))
            emberstones_on_ground = [
                emberstone
                for emberstone in emberstones_on_ground
                if emberstone not in collected_emberstones
            ]

        if (
            player.level >= REQUIRED_LEVEL
            and player.total_emberstones_collected >= REQUIRED_EMBERSTONES
        ):
            player.map2_cleared = True

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not player.ui_open
            and player.rect.colliderect(return_portal.rect)
        ):
            next_map = "map1"
            next_arrival_from = "map2"
            running = False
        elif (
            not player.is_dead
            and not player.ui_open
            and player.map2_cleared
            and player.rect.colliderect(exit_portal.rect)
        ):
            next_map = "map3"
            next_arrival_from = "map2"
            running = False

        # Follow the player while keeping the camera inside the map.
        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        # Draw only the 600x320 camera section of the 960x320 map.
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        return_portal.draw(screen, camera_x)
        exit_portal.draw(screen, camera_x)
        for emberstone in emberstones_on_ground:
            emberstone.draw(screen, camera_x)
        for slime in slimes:
            slime.draw(screen, camera_x)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)

        pygame.display.flip()

    return next_map, player, next_arrival_from
