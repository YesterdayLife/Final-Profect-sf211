"""Frame selection and scaling for the player prototype."""
import pygame

from game.assets import SpriteFrame


class Animator:
    def __init__(self, atlas):
        self.animations = {}
        for name, scale in (("move", 0.28), ("idle", 0.14),
                            ("player_jump", 0.38), ("player_double_jump", 0.38),
                            ("player_hurt", 0.30), ("player_defeat", 0.30),
                            ("light_attack", 0.38), ("heavy_attack", 0.38),
                            ("keyboard_swing", 0.38),
                            ("swing_1", 0.38), ("swing_2", 0.45)):
            self.animations[name] = tuple(
                SpriteFrame(
                    pygame.transform.scale(frame.image, tuple(round(n * scale) for n in frame.image.get_size())),
                    tuple(round(n * scale) for n in frame.anchor),
                )
                for frame in atlas[name]
            )
        self.name = "idle"
        self.elapsed = 0.0

    def update(self, name, dt):
        if name != self.name:
            self.name = name
            self.elapsed = 0.0
        else:
            self.elapsed += dt

    def current_frame(self):
        frames = self.animations[self.name]
        fps = {"move": 12, "idle": 4, "player_jump": 7,
               "player_double_jump": 10, "light_attack": 12, "heavy_attack": 6,
               "keyboard_swing": 10, "player_hurt": 10, "player_defeat": 5}[self.name]
        index = int(self.elapsed * fps)
        if self.name in ("move", "idle"):
            index %= len(frames)
        else:
            index = min(index, len(frames) - 1)
        return frames[index]
