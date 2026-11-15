"""Window size, paths, and colors shared by the game."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IMAGES = ASSETS / "images"
SOUNDS = ASSETS / "sounds"
FONTS = ASSETS / "fonts"

WIDTH = 960
HEIGHT = 540
FPS = 60
TITLE = "AJ Jack"

BG_COLOR = (18, 22, 33)
TEXT_COLOR = (226, 232, 240)
ACCENT_COLOR = (56, 189, 248)

GROUND_HEIGHT = 495