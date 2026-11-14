"""Load images, sounds, and fonts from the assets folder."""

from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
import json

import pygame

from game.settings import ASSETS, FONTS, IMAGES, SOUNDS


@dataclass(frozen=True)
class SpriteFrame:
    image: pygame.Surface
    anchor: tuple[int, int]


@lru_cache(maxsize=1)
def load_sprite_atlas() -> dict[str, tuple[SpriteFrame, ...]]:
    """Load the animation rows after creating a display."""
    atlas = json.loads((ASSETS / "sprites.json").read_text(encoding="utf-8"))
    animations = {}
    for path, spec in atlas.items():
        sheet = pygame.image.load(_require(ASSETS / path, "sprite sheet")).convert_alpha()
        width, height = sheet.get_size()
        columns = spec["columns"]
        rows = spec["rows"]
        anchor_x, anchor_y = spec["anchor"]
        for row, name in enumerate(rows):
            top = round(row * height / len(rows))
            bottom = round((row + 1) * height / len(rows))
            frames = []
            for column in range(columns):
                left = round(column * width / columns)
                right = round((column + 1) * width / columns)
                cell = sheet.subsurface((left, top, right - left, bottom - top))
                # Ignore low-alpha specks when measuring, while preserving the source alpha.
                bounds = cell.get_bounding_rect(min_alpha=32).inflate(8, 8)
                bounds = bounds.clip(cell.get_rect())
                anchor = (
                    round(cell.get_width() * anchor_x) - bounds.left,
                    round(cell.get_height() * anchor_y) - bounds.top,
                )
                frames.append(SpriteFrame(cell.subsurface(bounds).copy(), anchor))
            animations[name] = tuple(frames)
    return animations


def _require(path: Path, kind: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {kind} asset: {path}")
    return path


def load_image(name: str, *, convert_alpha: bool = True) -> pygame.Surface:
    """Load an image from assets/images. Call this after the display is created."""
    image = pygame.image.load(_require(IMAGES / name, "image"))
    if convert_alpha:
        return image.convert_alpha()
    return image.convert()


def load_sound(name: str) -> pygame.mixer.Sound:
    """Load a sound from assets/sounds. The mixer must already be initialized."""
    return pygame.mixer.Sound(_require(SOUNDS / name, "sound"))


def load_font(name: str | None, size: int) -> pygame.font.Font:
    """Load a font from assets/fonts, or the built-in font when name is None."""
    if name is None:
        return pygame.font.Font(None, size)
    return pygame.font.Font(_require(FONTS / name, "font"), size)
