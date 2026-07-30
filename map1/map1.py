from pathlib import Path

import pygame
from dialogue import DialogueBox, MapSelectionBox
from music_manager import play_background_music
from npc1 import HealingNPC
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
PLAYER_SPAWN = (80, 180)
MAP2_RETURN_SPAWN = (MAP_WIDTH - 80, 180)
NPC_CENTER_X = 480
FINAL_RETURN_SPAWN = (NPC_CENTER_X - 70, 180)

MAP_PATH = Path(__file__).parent / "maps2.png"
MUSIC_PATH = Path(__file__).parent / "music.mp3"

INTRO_DIALOGUE = [
    {
        "speaker": "Headmaster",
        "text": "The Rite of Initiation is over. Every apprentice awakened their magic... except you.",
    },
    {
        "speaker": "Girl",
        "text": "I tried everything, Headmaster. Does this mean I have to leave the academy?",
    },
    {
        "speaker": "Headmaster",
        "text": "No. Your magic isn't missing. It's sleeping.",
    },
    {
        "speaker": "Girl",
        "text": "Then how do I wake it?",
    },
    {
        "speaker": "Headmaster",
        "text": "Find the Ancient Shrines beyond these portals. Each lies in a different realm and guards a forgotten branch of magic.",
    },
    {
        "speaker": "Girl",
        "text": "Ember Forest, the Toad Realm, the skies beyond... You want me to cross them without a single spell?",
    },
    {
        "speaker": "Headmaster",
        "text": "Take this wooden staff. Gather the relics guarded in each realm; near their shrine, your sleeping magic will begin to stir.",
    },
    {
        "speaker": "Girl",
        "text": "Then I will awaken every shrine and return as a true mage.",
    },
    {
        "speaker": "Objective",
        "text": "Begin the Shrine Quest. Reach the portal with A/D, jump with W, strike with SPACE, and kick with K.",
    },
]

FINAL_VICTORY_DIALOGUE = [
    {
        "speaker": "Headmaster",
        "text": (
            "You have returned, and the final monster has fallen. "
            "The realms are safe because of your courage."
        ),
    },
    {
        "speaker": "Girl",
        "text": "I only followed the path you showed me, Headmaster.",
    },
    {
        "speaker": "Headmaster",
        "text": (
            "You crossed every realm, mastered the ancient magic, and "
            "defeated the Ogre. You have surpassed every expectation."
        ),
    },
    {
        "speaker": "Headmaster",
        "text": (
            "Today the academy welcomes you home as a true mage and a "
            "hero. I am proud of you."
        ),
    },
]


def create_story_dialogue(player, arrived_from, portraits):
    """Create the one-time opening or final Headmaster conversation."""
    if (
        arrived_from == "map8"
        and player.map8_cleared
        and not player.final_praise_seen
    ):
        return DialogueBox(
            FINAL_VICTORY_DIALOGUE, portraits=portraits
        ), "final"
    if not player.intro_dialogue_seen and arrived_from is None:
        return DialogueBox(INTRO_DIALOGUE, portraits=portraits), "intro"
    return None, None


def load_map():
    """Load map.png and make sure it has the required dimensions."""
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


def map1(player=None, arrived_from=None):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Broken Rite - Map 1")
    clock = pygame.time.Clock()
    play_background_music(MUSIC_PATH)

    map_surface = load_map()
    platform_rects = create_platform_rects()
    entry_spawn = (
        MAP2_RETURN_SPAWN
        if arrived_from == "map2"
        else FINAL_RETURN_SPAWN
        if arrived_from == "map8"
        else PLAYER_SPAWN
    )
    if player is None:
        player = Player(*entry_spawn)
    else:
        player.set_position(*entry_spawn)

    # Decorative portal showing where the player enters Map 1.
    spawn_ground = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= PLAYER_SPAWN[0] + 12 < rect.right
        ),
        default=MAP_HEIGHT,
    )
    spawn_portal = Portal(
        center_x=PLAYER_SPAWN[0] + 12,
        bottom_y=spawn_ground,
    )

    # Place the Map 2 portal at the end of Map 1.
    right_edge_platforms = [
        rect for rect in platform_rects if rect.right == MAP_WIDTH
    ]
    portal_bottom = min(
        (rect.top for rect in right_edge_platforms), default=MAP_HEIGHT
    )
    exit_portal = Portal(center_x=MAP_WIDTH - 24, bottom_y=portal_bottom)

    npc_ground = min(
        (
            rect.top
            for rect in platform_rects
            if rect.left <= NPC_CENTER_X < rect.right
        ),
        default=MAP_HEIGHT,
    )
    healing_npc = HealingNPC(NPC_CENTER_X, npc_ground)
    dialogue_portraits = {
        "Girl": player.idle_right[0],
        "Headmaster": healing_npc.portrait,
    }
    intro_dialogue, dialogue_kind = create_story_dialogue(
        player, arrived_from, dialogue_portraits
    )

    # Add future enemies here. Each needs a rect and take_damage(amount).
    damage_targets = []
    camera_x = 0.0
    running = True
    next_map = None
    next_arrival_from = None
    map_selection = None
    portal_ready = True

    while running:
        delta_time = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                event_consumed = False
                if intro_dialogue is not None and not intro_dialogue.finished:
                    event_consumed = intro_dialogue.handle_event(event)
                elif map_selection is not None:
                    event_consumed = map_selection.handle_event(event)
                    if map_selection.closed:
                        if map_selection.choice is not None:
                            next_map = map_selection.choice
                            next_arrival_from = "map1"
                            running = False
                        else:
                            portal_ready = False
                        map_selection = None
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_e
                    and not player.ui_open
                ):
                    event_consumed = healing_npc.talk(player)

                if not event_consumed:
                    event_consumed = player.handle_event(event)
                if (
                    not event_consumed
                    and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    if not open_in_game_menu(clock):
                        running = False

        dialogue_open = (
            intro_dialogue is not None and not intro_dialogue.finished
        )
        map_selection_open = map_selection is not None
        if intro_dialogue is not None:
            intro_dialogue.update(delta_time)
            if intro_dialogue.finished:
                if dialogue_kind == "final":
                    player.final_praise_seen = True
                else:
                    player.intro_dialogue_seen = True

        if (
            not player.ui_open
            and not dialogue_open
            and not map_selection_open
        ):
            player.update(
                delta_time, platform_rects, MAP_WIDTH, damage_targets
            )
        spawn_portal.update(delta_time)
        exit_portal.update(delta_time)
        healing_npc.update(delta_time)

        if player.death_animation_finished:
            player.respawn(*PLAYER_SPAWN)
            next_map = "map1"
            next_arrival_from = None
            running = False
        elif (
            running
            and not player.is_dead
            and not player.ui_open
            and not dialogue_open
            and map_selection is None
            and portal_ready
            and player.rect.colliderect(exit_portal.rect)
        ):
            map_selection = MapSelectionBox(
                map2_cleared=player.map2_cleared,
                map3_cleared=player.map3_cleared,
                map4_cleared=player.map4_cleared,
                map6_cleared=player.map6_cleared,
                map7_cleared=player.map7_mission_complete,
            )

        if not player.rect.colliderect(exit_portal.rect):
            portal_ready = True

        # Follow the player while keeping the camera inside the map.
        camera_x = player.rect.centerx - SCREEN_WIDTH / 2
        camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))

        # Draw only the 600x320 camera section of the 960x320 map.
        camera_area = pygame.Rect(
            round(camera_x), 0, SCREEN_WIDTH, SCREEN_HEIGHT
        )
        screen.blit(map_surface, (0, 0), camera_area)
        spawn_portal.draw(screen, camera_x)
        exit_portal.draw(screen, camera_x)
        healing_npc.draw(screen, camera_x, player)
        player.draw(screen, camera_x)
        player.draw_health_bar(screen)
        player.draw_active_screen(screen)
        if intro_dialogue is not None:
            intro_dialogue.draw(screen)
        if map_selection is not None:
            map_selection.draw(screen)

        pygame.display.flip()

    return next_map, player, next_arrival_from
