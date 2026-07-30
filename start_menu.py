"""Keyboard and mouse controlled menu shown before the opening cinematic."""

from pathlib import Path

import pygame
from music_manager import get_master_volume, set_master_volume


SCREEN_SIZE = (600, 320)
MENU_ITEMS = ("Start Game", "Controls", "Options (Sound)", "Exit")
BACKGROUND_PATH = Path(__file__).parent / "map1" / "maps2.png"
VOLUME_STEP = 0.10

CONTROLS = (
    ("A / LEFT", "Move left"),
    ("D / RIGHT", "Move right"),
    ("W / UP", "Jump or fly up"),
    ("S / DOWN", "Fly down"),
    ("C", "Open crafting"),
    ("M", "Open status menu"),
    ("SPACE", "Normal attack"),
    ("F", "Fire attack"),
    ("K", "Kick"),
    ("G", "Activate Fly Magic"),
    ("H", "Use healing potion"),
)


def _load_background():
    try:
        image = pygame.image.load(BACKGROUND_PATH).convert()
        image = pygame.transform.smoothscale(image, SCREEN_SIZE)
    except (OSError, pygame.error):
        image = pygame.Surface(SCREEN_SIZE)
        image.fill((18, 25, 45))

    shade = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    shade.fill((8, 12, 28, 145))
    image.blit(shade, (0, 0))
    return image


def _draw_title(screen, title_font):
    shadow = title_font.render("THE BROKEN RITE", True, (20, 13, 31))
    title = title_font.render("THE BROKEN RITE", True, (255, 221, 120))
    title_rect = title.get_rect(midtop=(SCREEN_SIZE[0] // 2, 18))
    screen.blit(shadow, title_rect.move(2, 2))
    screen.blit(title, title_rect)


def _draw_main(screen, selected, fonts):
    item_rects = []
    for index, label in enumerate(MENU_ITEMS):
        rect = pygame.Rect(170, 92 + index * 47, 260, 36)
        selected_item = index == selected
        color = (224, 165, 62) if selected_item else (34, 43, 68)
        border = (255, 231, 158) if selected_item else (120, 137, 174)
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        text = fonts["menu"].render(label, True, (252, 247, 229))
        screen.blit(text, text.get_rect(center=rect.center))
        item_rects.append(rect)

    hint = fonts["small"].render(
        "W/S or arrows: Select     ENTER: Confirm",
        True,
        (220, 226, 241),
    )
    screen.blit(hint, hint.get_rect(midbottom=(300, 314)))
    return item_rects


def _draw_controls(screen, fonts):
    panel = pygame.Rect(58, 70, 484, 226)
    pygame.draw.rect(screen, (18, 25, 45), panel, border_radius=10)
    pygame.draw.rect(screen, (225, 184, 85), panel, 2, border_radius=10)
    heading = fonts["heading"].render("CONTROLS", True, (255, 221, 120))
    screen.blit(heading, heading.get_rect(midtop=(300, 76)))

    for index, (key, action) in enumerate(CONTROLS):
        column = index // 6
        row = index % 6
        x = 78 + column * 245
        y = 112 + row * 27
        key_text = fonts["small"].render(key, True, (255, 213, 112))
        action_text = fonts["small"].render(action, True, (232, 237, 247))
        screen.blit(key_text, (x, y))
        screen.blit(action_text, (x + 78, y))

    hint = fonts["small"].render(
        "ESC or ENTER: Back", True, (205, 215, 235)
    )
    screen.blit(hint, hint.get_rect(midbottom=(300, 288)))


def _draw_options(screen, fonts):
    panel = pygame.Rect(105, 92, 390, 155)
    pygame.draw.rect(screen, (18, 25, 45), panel, border_radius=10)
    pygame.draw.rect(screen, (225, 184, 85), panel, 2, border_radius=10)
    heading = fonts["heading"].render(
        "SOUND OPTIONS", True, (255, 221, 120)
    )
    screen.blit(heading, heading.get_rect(midtop=(300, 104)))

    volume = get_master_volume()
    value = fonts["menu"].render(
        f"Master Sound: {round(volume * 100)}%",
        True,
        (240, 244, 252),
    )
    screen.blit(value, value.get_rect(center=(300, 157)))

    bar = pygame.Rect(160, 184, 280, 12)
    pygame.draw.rect(screen, (55, 65, 88), bar, border_radius=6)
    fill = bar.copy()
    fill.width = round(bar.width * volume)
    pygame.draw.rect(screen, (231, 168, 62), fill, border_radius=6)

    hint = fonts["small"].render(
        "LEFT/RIGHT: Volume    M: Mute    ESC/ENTER: Back",
        True,
        (205, 215, 235),
    )
    screen.blit(hint, hint.get_rect(midtop=(300, 214)))


def show_start_menu(escape_returns=False):
    """Return True for Start Game and False for Exit/window close."""
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("The Broken Rite")
    clock = pygame.time.Clock()
    background = _load_background()
    fonts = {
        "title": pygame.font.Font(None, 50),
        "heading": pygame.font.Font(None, 30),
        "menu": pygame.font.Font(None, 28),
        "small": pygame.font.Font(None, 18),
    }
    selected = 0
    active_screen = "main"
    item_rects = []
    previous_volume = max(get_master_volume(), VOLUME_STEP)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if active_screen == "main":
                if event.type == pygame.MOUSEMOTION:
                    for index, rect in enumerate(item_rects):
                        if rect.collidepoint(event.pos):
                            selected = index
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for index, rect in enumerate(item_rects):
                        if rect.collidepoint(event.pos):
                            selected = index
                            choice = MENU_ITEMS[selected]
                            if choice == "Start Game":
                                return True
                            if choice == "Exit":
                                return False
                            active_screen = choice.split()[0].lower()
                            break
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(MENU_ITEMS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(MENU_ITEMS)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        choice = MENU_ITEMS[selected]
                        if choice == "Start Game":
                            return True
                        if choice == "Exit":
                            return False
                        active_screen = choice.split()[0].lower()
                    elif event.key == pygame.K_ESCAPE:
                        return escape_returns
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    active_screen = "main"
                elif active_screen == "options":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        set_master_volume(get_master_volume() - VOLUME_STEP)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        set_master_volume(get_master_volume() + VOLUME_STEP)
                    elif event.key == pygame.K_m:
                        if get_master_volume() > 0:
                            previous_volume = get_master_volume()
                            set_master_volume(0)
                        else:
                            set_master_volume(previous_volume)

        screen.blit(background, (0, 0))
        _draw_title(screen, fonts["title"])
        if active_screen == "main":
            item_rects = _draw_main(screen, selected, fonts)
        elif active_screen == "controls":
            _draw_controls(screen, fonts)
        else:
            _draw_options(screen, fonts)
        pygame.display.flip()
        clock.tick(60)


def open_in_game_menu(game_clock):
    """Pause a running map and resume it from the startup menu."""
    previous_caption = pygame.display.get_caption()[0]
    resume_game = show_start_menu(escape_returns=True)
    pygame.display.set_caption(previous_caption)
    # Discard time spent in the menu so physics do not jump on resume.
    game_clock.tick()
    return resume_game
