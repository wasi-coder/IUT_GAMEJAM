from pathlib import Path
import random

import pygame
from music_manager import play_background_music
from player import Player
from npc2 import MissionNPC
from portal import Portal
from start_menu import open_in_game_menu
from toads import Toad
from .object import object as object_layer
from .platform import platform
from .wind_crystal import WindCrystal


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 1120
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
TOAD_ZONE_MARKER = 113
PLAYER_SPAWN = (80, 100)
MAP4_RETURN_SPAWN = (1040, 100)
WIND_CRYSTAL_DROP_CHANCE = 0.70
BOSS_ZONE_WIDTH = 288
PLAYER_LIGHT_RADIUS = 165

MAP_PATH = Path(__file__).parent / "map3.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"


def create_night_overlay(light_center):
    """Create a dark blue night layer with soft light around the player."""
    overlay = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
    )
    overlay.fill((4, 8, 24, 242))
    rings = (
        (PLAYER_LIGHT_RADIUS, 205),
        (145, 170),
        (125, 125),
        (105, 80),
        (85, 38),
        (62, 0),
    )
    for radius, alpha in rings:
        pygame.draw.circle(
            overlay,
            (7, 14, 32, alpha),
            light_center,
            radius,
        )
    return overlay


def draw_night_lighting(screen, player, camera_x):
    light_center = (
        player.rect.centerx - round(camera_x),
        player.rect.centery,
    )
    screen.blit(create_night_overlay(light_center), (0, 0))


def load_map():
    """Load map3.png and make sure it has the required dimensions."""
    map_surface = pygame.image.load(MAP_PATH).convert()

    if map_surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        map_surface = pygame.transform.scale(
            map_surface, (MAP_WIDTH, MAP_HEIGHT)
        )

    return map_surface


def create_platform_rects():
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


def create_object_rects():
    """Create solid collision rectangles for every 113 object tile."""
    object_rects = []

    for row_number, row in enumerate(object_layer):
        for column_number, tile_value in enumerate(row):
            if tile_value == TOAD_ZONE_MARKER:
                object_rects.append(
                    pygame.Rect(
                        column_number * TILE_SIZE,
                        row_number * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )
                )

    return object_rects


def create_toad_zones(platform_rects):
    """Create a zone between every two adjacent 113 markers."""
    zones = []

    for row_number, row in enumerate(object_layer):
        marker_columns = [
            column_number
            for column_number, value in enumerate(row)
            if value == TOAD_ZONE_MARKER
        ]

        for marker_index in range(len(marker_columns) - 1):
            first_column = marker_columns[marker_index]
            second_column = marker_columns[marker_index + 1]
            zone_left = first_column * TILE_SIZE
            zone_right = (second_column + 1) * TILE_SIZE
            zone_center = (zone_left + zone_right) // 2
            marker_y = row_number * TILE_SIZE

            ground_candidates = [
                rect.top
                for rect in platform_rects
                if rect.left <= zone_center < rect.right
                and rect.top >= marker_y
            ]
            ground_y = min(ground_candidates, default=MAP_HEIGHT)
            zones.append((zone_left, zone_right, ground_y))

    return zones


def create_boss_toad(platform_rects):
    marker_columns = [
        column_number
        for row in object_layer
        for column_number, value in enumerate(row)
        if value == TOAD_ZONE_MARKER
    ]
    last_marker_right = (max(marker_columns) + 1) * TILE_SIZE
    zone_right = min(MAP_WIDTH, last_marker_right + BOSS_ZONE_WIDTH)
    zone_center = (last_marker_right + zone_right) // 2
    ground_y = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= zone_center < rect.right
        ),
        default=MAP_HEIGHT,
    )
    return Toad(last_marker_right, zone_right, ground_y, is_boss=True)


def create_all_toads(platform_rects):
    toads = [
        Toad(zone_left, zone_right, ground_y)
        for zone_left, zone_right, ground_y in create_toad_zones(
            platform_rects
        )
    ]
    toads.append(create_boss_toad(platform_rects))
    return toads


def create_wind_crystals(toad):
    """Bosses guarantee five crystals; regular toads retain their 70% drop."""
    if toad.is_boss:
        offsets = (-24, -12, 0, 12, 24)
    elif random.random() < WIND_CRYSTAL_DROP_CHANCE:
        offsets = (0,)
    else:
        offsets = ()

    return [
        WindCrystal(toad.rect.centerx + offset, toad.rect.bottom)
        for offset in offsets
    ]


def map3(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Map 3")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)

    map_surface = load_map()
    platform_rects = create_platform_rects()
    object_rects = create_object_rects()
    spawn_position = (
        MAP4_RETURN_SPAWN if arrived_from == "map4" else PLAYER_SPAWN
    )
    if player is None:
        player = Player(*spawn_position)
    else:
        player.set_position(*spawn_position)

    left_edge_platforms = [
        rect for rect in platform_rects if rect.left == 0
    ]
    portal_bottom = min(
        (rect.top for rect in left_edge_platforms), default=MAP_HEIGHT
    )
    return_portal = Portal(center_x=24, bottom_y=portal_bottom)

    rightmost_platform_edge = max(rect.right for rect in platform_rects)
    end_portal_bottom = min(
        rect.top
        for rect in platform_rects
        if rect.right == rightmost_platform_edge
    )
    end_portal = Portal(
        center_x=rightmost_platform_edge - 24,
        bottom_y=end_portal_bottom,
    )

    boss_spawn = create_boss_toad(platform_rects)
    mission_npc = MissionNPC(
        center_x=boss_spawn.rect.centerx,
        bottom_y=boss_spawn.rect.bottom,
    )

    boss_defeated = player.map3_cleared
    if boss_defeated:
        toads = []
    else:
        toads = create_all_toads(platform_rects)
    wind_crystals_on_ground = []

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
                event_consumed = False
                npc_action = None
                if mission_npc.active:
                    event_consumed, npc_action = (
                        mission_npc.handle_event(event, player)
                    )
                elif (
                    boss_defeated
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_e
                    and mission_npc.can_talk(player)
                ):
                    mission_npc.open(player)
                    event_consumed = True
                else:
                    event_consumed = player.handle_event(
                        event, allow_flight_activation=True
                    )

                if npc_action == "restart":
                    player.map3_cleared = False
                    boss_defeated = False
                    toads = create_all_toads(platform_rects)
                    wind_crystals_on_ground.clear()
                    player.set_position(*PLAYER_SPAWN)
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    if not open_in_game_menu(clock):
                        running = False

        game_ui_open = player.ui_open or mission_npc.active
        if not game_ui_open:
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                toads,
                object_rects,
            )
        return_portal.update(delta_time)
        if boss_defeated:
            end_portal.update(delta_time)
            mission_npc.update(delta_time)

        # Keep defeated sprites visible until the attack animation completes.
        if (
            not player.is_attacking
            and not player.is_casting_fire
            and not player.is_kicking
        ):
            defeated_toads = [
                toad for toad in toads if not toad.alive
            ]
            boss_was_defeated = any(
                toad.is_boss for toad in defeated_toads
            )
            for toad in defeated_toads:
                wind_crystals_on_ground.extend(
                    create_wind_crystals(toad)
                )

            toads = [toad for toad in toads if toad.alive]
            if boss_was_defeated:
                boss_defeated = True
                player.map3_cleared = True
                toads.clear()
        if not game_ui_open and not player.is_dead:
            for toad in toads:
                toad.update(delta_time, player)

        collected_crystals = [
            crystal
            for crystal in wind_crystals_on_ground
            if player.rect.colliderect(crystal.rect)
        ]
        if collected_crystals:
            player.collect_wind_crystals(len(collected_crystals))
            wind_crystals_on_ground = [
                crystal
                for crystal in wind_crystals_on_ground
                if crystal not in collected_crystals
            ]

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not game_ui_open
            and player.rect.colliderect(return_portal.rect)
        ):
            next_map = "map2"
            next_arrival_from = "map3"
            running = False
        elif (
            boss_defeated
            and not player.is_dead
            and not game_ui_open
            and player.rect.colliderect(end_portal.rect)
        ):
            if player.is_flying:
                next_map = "map4"
                next_arrival_from = "map3"
                running = False
            else:
                mission_npc.warn_about_flight(player)

        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        return_portal.draw(screen, camera_x)
        if boss_defeated:
            end_portal.draw(screen, camera_x)
        for crystal in wind_crystals_on_ground:
            crystal.draw(screen, camera_x)
        for toad in toads:
            toad.draw(screen, camera_x)
        if boss_defeated and not mission_npc.active:
            mission_npc.draw(screen, camera_x, player)
        # Toads and scenery outside the player's light are hidden in night.
        draw_night_lighting(screen, player, camera_x)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)
        if boss_defeated and mission_npc.active:
            mission_npc.draw(screen, camera_x, player)

        pygame.display.flip()

    return next_map, player, next_arrival_from
