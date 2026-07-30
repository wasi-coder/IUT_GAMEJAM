from pathlib import Path

import pygame
from music_manager import play_background_music
from npc3 import QuestNPC
from player import Player
from portal import Portal
from start_menu import open_in_game_menu
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
WALKABLE_TILE = 142
PLAYER_SPAWN = (80, 100)
MAP7_RETURN_SPAWN = (700, 100)
PORTAL_X = 24
NPC3_X = 770
DOOR_X = 900
DOOR_SIZE = (72, 101)
GROUND_Y = 240
MAP_PATH = Path(__file__).parent / "map6.png"
DOOR_PATH = Path(__file__).parent / "door.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"


def load_map():
    image = pygame.image.load(MAP_PATH).convert()
    if image.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        image = pygame.transform.scale(image, (MAP_WIDTH, MAP_HEIGHT))
    return image


def load_door():
    image = pygame.image.load(DOOR_PATH).convert()
    return pygame.transform.smoothscale(image, DOOR_SIZE)


def door_is_open(player):
    """NPC3 opens the decorative door after receiving the hidden book."""
    return player.map7_book_delivered


def player_is_near_door(player, door_rect):
    return door_rect.inflate(36, 20).colliderect(player.rect)


def create_platform_rects():
    return [
        pygame.Rect(
            column_number * TILE_SIZE,
            row_number * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        for row_number, row in enumerate(platform)
        for column_number, tile_value in enumerate(row)
        if tile_value == WALKABLE_TILE
    ]


def stop_flight(player):
    """Force normal walking while the player is inside Map 6."""
    player.flight_time_left = 0.0
    player.flight_dash_time_left = 0.0
    player.flight_dash_cooldown_left = 0.0
    player.flight_horizontal_direction = 0
    player.flight_vertical_direction = 0


def map6(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - The Grieving Husband")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)
    background = load_map()
    door_image = load_door()
    door_rect = door_image.get_rect(midbottom=(DOOR_X, GROUND_Y))
    door_font = pygame.font.Font(None, 18)
    platform_rects = create_platform_rects()

    spawn = MAP7_RETURN_SPAWN if arrived_from == "map7" else PLAYER_SPAWN
    if player is None:
        player = Player(*spawn)
    else:
        player.set_position(*spawn)
    stop_flight(player)

    entrance_portal = Portal(PORTAL_X, GROUND_Y)
    quest_npc = QuestNPC(NPC3_X, GROUND_Y)
    if arrived_from == "map7" and player.map7_has_book:
        quest_npc.open(player)

    camera_x = 0.0
    running = True
    next_map = None
    next_arrival_from = None

    while running:
        delta_time = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            event_consumed = False
            npc_action = None
            if quest_npc.active:
                event_consumed, npc_action = quest_npc.handle_event(event)
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
                and not player.ui_open
                and quest_npc.is_near(player)
            ):
                quest_npc.open(player)
                event_consumed = True
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
                and door_is_open(player)
                and player_is_near_door(player, door_rect)
            ):
                next_map = "map8"
                next_arrival_from = "map6"
                running = False
                event_consumed = True
            else:
                # Carried flight is cancelled on entry, but a new spell works.
                event_consumed = player.handle_event(
                    event, allow_flight_activation=True
                )

            if npc_action == "travel_map7":
                next_map = "map7"
                next_arrival_from = "map6"
                running = False
            elif (
                not event_consumed
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                if not open_in_game_menu(clock):
                    running = False

        ui_open = player.ui_open or quest_npc.active
        if not ui_open:
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                map_height=MAP_HEIGHT,
            )
        entrance_portal.update(delta_time)
        quest_npc.update(delta_time)

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)
        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            not player.is_dead
            and not ui_open
            and player.rect.colliderect(entrance_portal.rect)
        ):
            next_map = "map4"
            next_arrival_from = "map6"
            running = False

        camera_x = max(
            0,
            min(
                player.rect.centerx - SCREEN_WIDTH / 2,
                MAP_WIDTH - SCREEN_WIDTH,
            ),
        )
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(background, (0, 0), camera_area)
        if door_is_open(player):
            screen.blit(
                door_image,
                door_rect.move(-round(camera_x), 0),
            )
            if player_is_near_door(player, door_rect):
                prompt = door_font.render(
                    "E: Enter the final arena", True, (255, 235, 150)
                )
                prompt_rect = prompt.get_rect(
                    midbottom=(
                        door_rect.centerx - round(camera_x),
                        door_rect.top - 5,
                    )
                )
                pygame.draw.rect(
                    screen,
                    (25, 22, 35),
                    prompt_rect.inflate(10, 6),
                    border_radius=5,
                )
                screen.blit(prompt, prompt_rect)
        entrance_portal.draw(screen, camera_x)
        quest_npc.draw(screen, camera_x, player)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)
        quest_npc.draw_window(screen)
        pygame.display.flip()

    return next_map, player, next_arrival_from
