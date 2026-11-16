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


class ShadowRenderer:
    """วาดเงากลมใต้ตัวละคร ขนาดและความเข้มขึ้นกับความสูงจากพื้น"""

    def __init__(self, base_width=64, base_height=20, max_height=220,
                 min_scale=0.45, max_alpha=150, min_alpha=50):
        self.base_width = base_width    # ความกว้างเงาตอนอยู่บนพื้น
        self.base_height = base_height  # ความสูงเงา (แบนๆ ให้ดูเป็นวงรี)
        self.max_height = max_height    # ความสูงที่เงาเล็ก/จางสุด
        self.min_scale = min_scale      # สัดส่วนขนาดต่ำสุดตอนอยู่สูงสุด
        self.max_alpha = max_alpha      # ความเข้มตอนอยู่บนพื้น
        self.min_alpha = min_alpha      # ความเข้มตอนอยู่สูงสุด
        self._cache = {}

    def _get_surface(self, width, height, alpha):
        key = (width, height, alpha)
        surface = self._cache.get(key)
        if surface is None:
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.ellipse(surface, (0, 0, 0, alpha), surface.get_rect())
            self._cache[key] = surface
        return surface

    def draw(self, screen, x, ground_y, height_above_ground):
        t = max(0.0, min(1.0, height_above_ground / self.max_height))
        scale = 1.0 - (1.0 - self.min_scale) * t
        alpha = round(self.max_alpha + (self.min_alpha - self.max_alpha) * t)

        # ปัดค่าเป็นขั้นๆ เพื่อไม่ให้ cache โตเรื่อยๆ
        width = max(2, round(self.base_width * scale / 2) * 2)
        height = max(2, round(self.base_height * scale / 2) * 2)
        alpha = alpha // 5 * 5

        surface = self._get_surface(width, height, alpha)
        screen.blit(surface, surface.get_rect(center=(round(x), round(ground_y))))