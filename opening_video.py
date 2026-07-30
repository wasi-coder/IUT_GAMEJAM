"""Opening cinematic playback for the game."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pygame


VIDEO_PATH = Path(__file__).parent / "openingvid" / "opening_vid.mp4"
SLIME_VIDEO_PATH = Path(__file__).parent / "openingvid" / "slime_map.mp4"
TOAD_VIDEO_PATH = Path(__file__).parent / "openingvid" / "toad_map.mp4"
FLYING_VIDEO_PATH = Path(__file__).parent / "openingvid" / "flying_map.mp4"


def _extract_video_audio(video_path):
    """Extract an MP4 audio track to a temporary WAV file."""
    ffmpeg_executable = shutil.which("ffmpeg")
    if ffmpeg_executable is None:
        try:
            import imageio_ffmpeg

            ffmpeg_executable = imageio_ffmpeg.get_ffmpeg_exe()
        except (ImportError, RuntimeError):
            ffmpeg_executable = None

    if ffmpeg_executable is None:
        print(
            "Video audio skipped: install dependencies with "
            "'python -m pip install -r requirements.txt'."
        )
        return None

    temporary_audio = tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
    )
    audio_path = Path(temporary_audio.name)
    temporary_audio.close()

    command = [
        ffmpeg_executable,
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        str(audio_path),
    ]
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            startupinfo=startupinfo,
            check=False,
        )
    except OSError as error:
        print(f"Video audio extraction failed: {error}")
        audio_path.unlink(missing_ok=True)
        return None
    if result.returncode != 0 or audio_path.stat().st_size == 0:
        error_message = result.stderr.decode(errors="replace").strip()
        if error_message:
            print(f"Video audio extraction failed: {error_message}")
        audio_path.unlink(missing_ok=True)
        return None
    return audio_path


def _start_video_audio(video_path):
    """Start a video's audio and return its temporary file, if present."""
    audio_path = _extract_video_audio(video_path)
    if audio_path is None:
        return None
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
    except (OSError, pygame.error) as error:
        print(f"Video audio skipped: {error}")
        audio_path.unlink(missing_ok=True)
        return None
    return audio_path


def _stop_video_audio(audio_path):
    if audio_path is None:
        return
    pygame.mixer.music.stop()
    if hasattr(pygame.mixer.music, "unload"):
        pygame.mixer.music.unload()
    audio_path.unlink(missing_ok=True)


def play_video(video_path, screen_size=(600, 320)):
    """Play an MP4. SPACE/ENTER skips and ESC quits playback."""
    try:
        import cv2
    except ImportError:
        print(
            "Opening video skipped: install OpenCV with "
            "'python -m pip install opencv-python'."
        )
        return True

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Video not found: {video_path}")
        return True

    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("The Broken Rite")
    clock = pygame.time.Clock()
    video = cv2.VideoCapture(str(video_path))
    fps = video.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30
    audio_path = _start_video_audio(video_path)

    keep_playing = True
    continue_game = True
    while keep_playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_playing = False
                continue_game = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    keep_playing = False
                    continue_game = False
                elif event.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
                ):
                    keep_playing = False

        if not keep_playing:
            break

        success, frame = video.read()
        if not success:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width = frame.shape[:2]
        frame_surface = pygame.image.frombuffer(
            frame.tobytes(), (frame_width, frame_height), "RGB"
        )

        screen_width, screen_height = screen_size
        scale = min(
            screen_width / frame_width,
            screen_height / frame_height,
        )
        target_size = (
            max(1, round(frame_width * scale)),
            max(1, round(frame_height * scale)),
        )
        frame_surface = pygame.transform.smoothscale(
            frame_surface, target_size
        )
        frame_rect = frame_surface.get_rect(
            center=(screen_width // 2, screen_height // 2)
        )

        screen.fill((0, 0, 0))
        screen.blit(frame_surface, frame_rect)
        skip_font = pygame.font.Font(None, 18)
        skip_text = skip_font.render(
            "SPACE: Skip", True, (235, 235, 235)
        )
        screen.blit(skip_text, (screen_width - skip_text.get_width() - 10, 8))
        pygame.display.flip()
        clock.tick(round(fps))

    video.release()
    _stop_video_audio(audio_path)
    return continue_game


def play_opening_video(screen_size=(600, 320)):
    return play_video(VIDEO_PATH, screen_size)
