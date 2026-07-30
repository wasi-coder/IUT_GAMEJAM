import pygame

from map1.map1 import map1
from map2.map2 import map2
from map3.map3 import map3
from opening_video import (
    FLYING_VIDEO_PATH,
    SLIME_VIDEO_PATH,
    TOAD_VIDEO_PATH,
    play_opening_video,
    play_video,
)
from map4.map4 import map4
from map6.map6 import map6
from map7.map7 import map7
from map8.map8 import map8
from start_menu import show_start_menu


def main():
    pygame.init()

    if not show_start_menu():
        pygame.quit()
        return

    if not play_opening_video():
        pygame.quit()
        return

    maps = {
        "map1": map1,
        "map2": map2,
        "map3": map3,
        "map4": map4,
        "map6": map6,
        "map7": map7,
        "map8": map8,
    }
    current_map = "map1"
    player = None
    arrived_from = None

    while current_map in maps:
        next_map, player, arrived_from = maps[current_map](
            player, arrived_from
        )
        if (
            next_map == "map2"
            and player is not None
            and not player.slime_video_seen
        ):
            if not play_video(SLIME_VIDEO_PATH):
                break
            player.slime_video_seen = True
        elif (
            next_map == "map3"
            and player is not None
            and not player.toad_video_seen
        ):
            if not play_video(TOAD_VIDEO_PATH):
                break
            player.toad_video_seen = True
        elif (
            next_map == "map4"
            and player is not None
            and not player.flying_video_seen
        ):
            if not play_video(FLYING_VIDEO_PATH):
                break
            player.flying_video_seen = True
        current_map = next_map

    pygame.quit()


if __name__ == "__main__":
    main()
