from pathlib import Path

import pygame
from music_manager import play_background_music
from Orge import OgreBoss
from player import Player
from start_menu import open_in_game_menu
from .platform import platform


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 320
MAP_WIDTH = 960
MAP_HEIGHT = 320
TILE_SIZE = 16
PLAYER_SPAWN = (70, 100)
OGRE_SPAWN_X = 790
OGRE_TRIGGER_X = 250
MAP_PATH = Path(__file__).parent / "map8.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"


def load_map():
    image = pygame.image.load(MAP_PATH).convert()
    if image.get_size() != (MAP_WIDTH, MAP_HEIGHT):
        image = pygame.transform.scale(image, (MAP_WIDTH, MAP_HEIGHT))
    return image


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
        if tile_value != -1
    ]


def complete_final_boss(player):
    """Award the final victory and return to the Map 1 Headmaster."""
    if not player.map8_cleared:
        player.add_points(250)
    player.map8_cleared = True
    return "map1", "map8"


def map8(player=None, arrived_from=None):
    """Run the final Ogre boss arena."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Final Battle")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)
    background = load_map()
    platform_rects = create_platform_rects()
    ground_y = min(
        (rect.top for rect in platform_rects), default=MAP_HEIGHT
    )

    if player is None:
        player = Player(*PLAYER_SPAWN)
    else:
        player.set_position(*PLAYER_SPAWN)

    # Map 8 is only reachable after NPC3 teaches the book's final lesson.
    player.arcana_magic_mastered = True
    ogre = None if player.map8_cleared else OgreBoss(
        OGRE_SPAWN_X,
        ground_y,
        OGRE_TRIGGER_X,
        MAP_WIDTH - 10,
    )

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

            event_consumed = player.handle_event(
                event,
                allow_flight_activation=True,
                allow_flight_dash=True,
            )
            if (
                not event_consumed
                and event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                if not open_in_game_menu(clock):
                    running = False

        if not player.ui_open:
            targets = [ogre] if ogre is not None else []
            player.update(
                delta_time,
                platform_rects,
                MAP_WIDTH,
                targets,
                map_height=MAP_HEIGHT,
                use_flying_sprites=True,
            )
            if ogre is not None:
                ogre.update(delta_time, player)

        if (
            ogre is not None
            and not ogre.alive
            and not player.is_attacking
            and not player.is_casting_fire
            and not player.is_kicking
        ):
            ogre = None
            next_map, next_arrival_from = complete_final_boss(player)
            running = False

        if not player.is_dead and player.rect.top > MAP_HEIGHT:
            player.take_damage(player.health)
        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
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
        if ogre is not None:
            ogre.draw(screen, camera_x)
        player.draw(screen, camera_x, use_flying_sprites=True)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)

        if player.map8_cleared:
            font = pygame.font.Font(None, 30)
            victory = font.render(
                "FINAL BOSS DEFEATED", True, (255, 225, 125)
            )
            screen.blit(
                victory,
                victory.get_rect(midtop=(SCREEN_WIDTH // 2, 45)),
            )
        pygame.display.flip()

    return next_map, player, next_arrival_from
