from pathlib import Path

import pygame
from ghosts import Ghost, GhostWindow
from music_manager import play_background_music
from player import Player
from portal import Portal
from start_menu import open_in_game_menu
from .platform import platform
from .interactions import (
    InteractionWindow,
    create_interactables,
    CANDLE_SEQUENCE,
    draw_lit_candles,
    draw_interaction_prompt,
    light_candle,
    nearest_interactable,
)


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
PLAYER_SPAWN = (145, 248)
EXIT_PORTAL_X = MAP_WIDTH - 28
EXIT_PORTAL_BOTTOM = 288
PUZZLE_TIME_LIMIT = 90.0
MAP_PATH = Path(__file__).parent / "map7.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"
LADDER_PATH = Path(__file__).parent / "ladder.png"
LADDER_RECT = pygame.Rect(388, 128, 28, 160)
LADDER_UPPER_FLOOR_Y = 128
LADDER_LOWER_FLOOR_Y = 288
LADDER_CLIMB_SPEED = 120


def load_map():
    """Load Map 7 at its native world size."""
    image = pygame.image.load(MAP_PATH).convert()
    if image.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        image = pygame.transform.scale(
            image, (MAP_WIDTH, MAP_HEIGHT)
        )
    return image


def create_platform_rects():
    """Treat every non--1 value in platform.py as solid terrain."""
    return [
        pygame.Rect(
            column_number * TILE_SIZE,
            row_number * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        for row_number, row in enumerate(platform)
        for column_number, tile_value in enumerate(row)
        if tile_value != -1
    ]


def move_player_on_ladder(player, direction, delta_time):
    """Move the player between Map 7's lower and upper floors."""
    ladder_area = LADDER_RECT.inflate(18, 8)
    if direction == 0 or not player.rect.colliderect(ladder_area):
        return False

    player.position.x = LADDER_RECT.centerx - player.rect.width / 2
    player.position.y += direction * LADDER_CLIMB_SPEED * delta_time
    upper_y = LADDER_UPPER_FLOOR_Y - player.rect.height
    lower_y = LADDER_LOWER_FLOOR_Y - player.rect.height
    player.position.y = max(upper_y, min(lower_y, player.position.y))
    player.rect.topleft = (
        round(player.position.x),
        round(player.position.y),
    )
    player.velocity_y = 0.0
    player.on_ground = player.position.y in (upper_y, lower_y)
    player.animation_time += delta_time
    return True


def load_ladder():
    image = pygame.image.load(LADDER_PATH).convert_alpha()
    if image.get_size() != LADDER_RECT.size:
        image = pygame.transform.smoothscale(image, LADDER_RECT.size)
    return image


def draw_ladder(screen, camera_x, ladder_image):
    """Draw the ladder sprite beside the grandfather clock."""
    draw_rect = LADDER_RECT.move(-round(camera_x), 0)
    screen.blit(ladder_image, draw_rect)


def reset_timed_puzzle(player):
    player.map7_painting_angle = 0
    player.map7_painting_solved = False
    player.map7_clock_hour = 12
    player.map7_clock_minute = 0
    player.map7_clock_solved = False
    player.map7_candles_lit.clear()
    player.map7_candles_solved = False
    player.map7_mission_complete = False
    player.map7_puzzle_time_left = PUZZLE_TIME_LIMIT
    player.map7_puzzle_timer_started = True
    player.combat_message = "Time expired. The puzzles have reset!"
    player.combat_message_time_left = 3.0


def draw_puzzle_timer(screen, player):
    seconds_left = max(0, int(player.map7_puzzle_time_left + 0.99))
    minutes, seconds = divmod(seconds_left, 60)
    font = pygame.font.Font(None, 24)
    text = font.render(
        f"Time: {minutes}:{seconds:02d}", True, (255, 225, 135)
    )
    rect = text.get_rect(topright=(SCREEN_WIDTH - 14, 14))
    pygame.draw.rect(
        screen, (25, 23, 38), rect.inflate(12, 7), border_radius=5
    )
    screen.blit(text, rect)


def map7(player=None, arrived_from=None):
    """Display native Map 7 with player movement and a scrolling camera."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Hidden House")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)
    background = load_map()
    ladder_image = load_ladder()
    platform_rects = create_platform_rects()
    interactables = create_interactables()
    prompt_font = pygame.font.Font(None, 18)

    if player is None:
        player = Player(*PLAYER_SPAWN)
    else:
        player.set_position(*PLAYER_SPAWN)

    exit_portal = Portal(EXIT_PORTAL_X, EXIT_PORTAL_BOTTOM)
    ghost = Ghost(center_x=110, bottom_y=144)
    ghost_window = None
    if not player.map7_ghost_intro_seen:
        ghost_window = GhostWindow("intro")

    running = True
    next_map = None
    next_arrival_from = None
    camera_x = 0.0
    interaction_window = None

    while running:
        delta_time = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            event_consumed = False
            if ghost_window is not None:
                ghost_kind = ghost_window.kind
                event_consumed = ghost_window.handle_event(event)
                if ghost_window.closed:
                    ghost_window = None
                    if ghost_kind == "intro":
                        player.map7_ghost_intro_seen = True
                    else:
                        player.map7_ghost_reward_seen = True
                        player.map7_has_book = True
                        player.combat_message = "Book of Arcana received!"
                        player.combat_message_time_left = 3.0
            elif interaction_window is not None:
                event_consumed = interaction_window.handle_event(event)
                if interaction_window.closed:
                    interaction_window = None
            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_e
                and not player.ui_open
            ):
                nearby = nearest_interactable(player, interactables)
                if nearby is not None:
                    if nearby.object_type in CANDLE_SEQUENCE:
                        light_candle(player, nearby.object_type)
                    else:
                        interaction_window = InteractionWindow(nearby, player)
                    event_consumed = True

            if not event_consumed:
                event_consumed = player.handle_event(event)
            if (
                not event_consumed
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                if not open_in_game_menu(clock):
                    running = False

        modal_open = interaction_window is not None or ghost_window is not None
        if not player.ui_open and not modal_open:
            keys = pygame.key.get_pressed()
            ladder_direction = int(
                keys[pygame.K_s] or keys[pygame.K_DOWN]
            ) - int(keys[pygame.K_w] or keys[pygame.K_UP])
            climbing = move_player_on_ladder(
                player, ladder_direction, delta_time
            )
            if not climbing:
                player.update(
                    delta_time,
                    platform_rects,
                    MAP_WIDTH,
                    map_height=MAP_HEIGHT,
                )

        timed_challenge_active = (
            player.map7_quest_accepted
            and player.map7_ghost_intro_seen
            and not player.map7_mission_complete
            and not player.map7_has_book
        )
        if timed_challenge_active:
            if not player.map7_puzzle_timer_started:
                player.map7_puzzle_timer_started = True
                player.map7_puzzle_time_left = PUZZLE_TIME_LIMIT
            else:
                player.map7_puzzle_time_left = max(
                    0.0, player.map7_puzzle_time_left - delta_time
                )
                if player.map7_puzzle_time_left <= 0:
                    reset_timed_puzzle(player)
        elif player.map7_mission_complete:
            player.map7_puzzle_timer_started = False

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)
        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)

        if (
            player.map7_quest_accepted
            and player.map7_mission_complete
            and not player.map7_ghost_reward_seen
            and not player.map7_has_book
            and interaction_window is None
            and ghost_window is None
        ):
            ghost.set_position(
                max(35, min(MAP_WIDTH - 35, player.rect.centerx + 45)),
                min(MAP_HEIGHT - 16, player.rect.bottom),
            )
            ghost_window = GhostWindow("reward")

        ghost_visible = ghost_window is not None
        if ghost_visible:
            ghost.update(delta_time)
        if player.map7_has_book:
            exit_portal.update(delta_time)

        if (
            player.map7_has_book
            and not player.is_dead
            and not player.ui_open
            and interaction_window is None
            and ghost_window is None
            and player.rect.colliderect(exit_portal.rect)
        ):
            next_map = "map6"
            next_arrival_from = "map7"
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
        draw_ladder(screen, camera_x, ladder_image)
        draw_lit_candles(screen, camera_x, interactables, player)
        if player.map7_has_book:
            exit_portal.draw(screen, camera_x)
        if ghost_visible:
            ghost.draw(screen, camera_x)
        nearby = nearest_interactable(player, interactables)
        if nearby is not None and interaction_window is None:
            draw_interaction_prompt(
                screen, camera_x, nearby, prompt_font
            )
        if (
            LADDER_RECT.inflate(32, 12).colliderect(player.rect)
            and interaction_window is None
            and ghost_window is None
        ):
            ladder_hint = prompt_font.render(
                "W/S: Climb ladder", True, (255, 238, 155)
            )
            hint_rect = ladder_hint.get_rect(
                midbottom=(
                    LADDER_RECT.centerx - round(camera_x),
                    LADDER_RECT.top - 4,
                )
            )
            pygame.draw.rect(
                screen,
                (25, 28, 40),
                hint_rect.inflate(10, 6),
                border_radius=5,
            )
            screen.blit(ladder_hint, hint_rect)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        if timed_challenge_active:
            draw_puzzle_timer(screen, player)
        player.draw_active_screen(screen)
        if interaction_window is not None:
            interaction_window.draw(screen)
        if ghost_window is not None:
            ghost_window.draw(screen)
            if ghost_window.kind == "intro":
                ghost.draw(screen, camera_x)
        pygame.display.flip()

    return next_map, player, next_arrival_from
