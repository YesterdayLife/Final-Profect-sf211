"""Draw the arena, combat effects and game screens."""
import math
import pygame
from game.animation import ShadowRenderer  # [เงา]
from game.settings import ASSETS, TEXT_COLOR


class Renderer:
    BOSS_ANIMATIONS = {
        1: {None: "midterm_idle", "papers": "midterm_paper_attack", "slash": "midterm_red_slash", "summon": "midterm_papers", "energy": "midterm_red_energy"},
        2: {None: "final_hover", "volley": "final_papers", "dash": "final_dash", "summon": "final_cast", "vortex": "final_energy"},
    }

    def __init__(self, screen, font, atlas):
        self.screen, self.font, self.atlas = screen, font, atlas
        self.elapsed = 0.0
        self.hint = font.render("A/D move  W/Space jump  Shift dash  J/K hit  L parry  U/I skills  H heal  P pause", True, TEXT_COLOR)
        original = pygame.image.load(str(ASSETS / "map" / "Gumgueng.png")).convert()
        self.background = pygame.transform.scale(original, (round(original.get_width() * screen.get_height() / original.get_height()), screen.get_height()))
        self.cached = {}
        self.world = pygame.Surface(screen.get_size()).convert()
        self.shake_remaining = 0.0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.shake_clock = 0.0
        self.shadow = ShadowRenderer()  # [เงา] เงาผู้เล่น
        self.boss_shadow = ShadowRenderer(base_width=70, base_height=18, max_alpha=170)  # [เงา] เงาบอส Midterm

    def shake(self, strength, duration):
        # Preserve an already stronger shake if several impacts land at once.
        if self.shake_remaining <= 0 or strength >= self.shake_strength:
            self.shake_strength = strength
            self.shake_duration = duration
            self.shake_remaining = duration
            self.shake_clock = 0.0

    def clear_shake(self):
        self.shake_remaining = 0.0
        self.shake_strength = 0.0

    def draw_atlas(self, name, position, size, index, camera_x, flip=False, anchor=True):
        key = (name, size)
        if key not in self.cached:
            frames = []
            for frame in self.atlas[name]:
                width, height = frame.image.get_size()
                scale = min(size / max(width, 1), size / max(height, 1))
                image = pygame.transform.scale(frame.image, (max(1, round(width * scale)), max(1, round(height * scale))))
                frames.append((image, (round(frame.anchor[0] * scale), round(frame.anchor[1] * scale))))
            self.cached[key] = frames
        frames = self.cached[key]
        image, pivot = frames[index % len(frames)]
        if flip:
            image = pygame.transform.flip(image, True, False)
            pivot = (image.get_width() - 1 - pivot[0], pivot[1])
        if not anchor:
            pivot = (image.get_width() // 2, image.get_height() // 2)
        self.screen.blit(image, (round(position[0] - camera_x - pivot[0]), round(position[1] - pivot[1])))

    def draw(self, player, boss, controller, projectiles, children, effects, state, dt):
        self.elapsed += dt
        if dt > 0 and self.shake_remaining > 0:
            self.shake_remaining = max(0.0, self.shake_remaining - dt)
            self.shake_clock += dt
        intensity = (self.shake_remaining / self.shake_duration * self.shake_strength
                     if self.shake_remaining > 0 else 0.0)
        shake_x = round(math.sin(self.shake_clock * 95) * intensity)
        shake_y = round(math.sin(self.shake_clock * 131 + 1) * intensity * 0.65)
        display = self.screen
        self.screen = self.world
        camera_x = max(0, min(player.position.x - self.screen.get_width() // 2, max(0, self.background.get_width() - self.screen.get_width())))
        self.screen.blit(self.background, (-round(camera_x), 0))

        # [เงา] เงาผู้เล่น: ติดพื้นเสมอ ย่อและจางลงตามความสูงที่กระโดด
        ground_y = player.ground_y
        self.shadow.draw(self.screen, player.position.x - camera_x, ground_y - 2,
                         ground_y - player.position.y)

        frame = player.animator.current_frame()
        image = frame.image
        anchor_x, anchor_y = frame.anchor
        if player.facing_left:
            image = pygame.transform.flip(image, True, False)
            anchor_x = image.get_width() - 1 - anchor_x
        rect = image.get_rect(topleft=(round(player.position.x - camera_x) - anchor_x, round(player.position.y) - anchor_y))
        if player.dash_remaining > 0:
            self.draw_atlas("dust_1", (player.position.x, player.position.y - 15), 75, int(self.elapsed * 12), camera_x, anchor=False)
        if player.hurt_remaining > 0 or player.invulnerable <= 0 or int(player.invulnerable * 12) % 2 == 0:
            self.screen.blit(image, rect)
        if player.attack_name:
            fps = 12 if player.attack_name == "light_attack" else 6
            index = int(player.attack_time * fps)
            if 1 <= index < 4:
                effect = player.animator.animations["swing_1" if player.attack_name == "light_attack" else "swing_2"][index].image
                if player.facing_left:
                    effect = pygame.transform.flip(effect, True, False)
                direction = -1 if player.facing_left else 1
                self.screen.blit(effect, effect.get_rect(center=(round(player.position.x - camera_x + direction * 48), round(player.position.y - 55))))
        if player.parry_remaining > 0:
            direction = -1 if player.facing_left else 1
            self.draw_atlas("parry_flash", (player.position.x + direction * 25, player.position.y - 50), 80, 0, camera_x, anchor=False)
        if boss.transform_remaining > 0:
            name = "final_transform"
            boss_index = min(3, int((1.2 - boss.transform_remaining) / 1.2 * 4))
        elif boss.hurt_remaining > 0:
            name = "midterm_react" if boss.phase == 1 else "final_react"
            boss_index = min(3, int(boss.hurt_elapsed * 10))
        elif controller.state == "waiting" and abs(boss.velocity.x) > 0 and boss.phase == 1:
            name = "midterm_walk"
            boss_index = int(self.elapsed * 6)
        else:
            name = self.BOSS_ANIMATIONS[boss.phase][controller.skill if controller.state == "charging" else None]
            boss_index = int(self.elapsed * 6)
        boss_y = boss.position.y if boss.phase == 1 else boss.position.y - 65

        # [เงา] เงาบอส: วาดเฉพาะร่าง Midterm (ร่าง Final มีเงาในภาพแอนิเมชันอยู่แล้ว)
        if boss.phase == 1:
            self.boss_shadow.draw(self.screen, boss.position.x - camera_x,
                                  boss.position.y - 8, 0)

        # Idle art faces left; walking, attacks and Final art face right.
        sprite_faces_left = name == "midterm_idle"
        self.draw_atlas(name, (boss.position.x, boss_y), 170, boss_index, camera_x,
                        flip=(boss.facing_left != sprite_faces_left))
        for child, _ in children:
            self.draw_atlas("wraith_fly", child.position, 60, int(self.elapsed * 8), camera_x, flip=not child.facing_left, anchor=False)
        for projectile in projectiles:
            self.draw_atlas(projectile.sprite, projectile.position, max(45, projectile.size * 2), int(self.elapsed * 10), camera_x, flip=projectile.velocity.x < 0, anchor=False)
        for effect in effects:
            index = min(3, int(effect["time"] / effect["duration"] * 4))
            self.draw_atlas(effect["name"], effect["position"], effect["size"], index, camera_x, anchor=False)
        self.screen = display
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.world, (shake_x, shake_y))
        self.bar(20, 35, 220, player.hp / player.max_hp, (76, 204, 133))
        self.bar(self.screen.get_width() - 240, 35, 220, boss.hp / boss.max_hp, (222, 67, 88))
        self.screen.blit(self.font.render("HP  |  Heals: " + str(player.heals), True, TEXT_COLOR), (20, 10))
        label = ("MIDTERM" if boss.phase == 1 else "FINAL")
        if controller.state == "charging":
            label += " - " + controller.skill.upper() + "!"
        title = self.font.render(label, True, TEXT_COLOR)
        self.screen.blit(title, (self.screen.get_width() - 20 - title.get_width(), 10))
        skill_label = "U key: " + ("READY" if player.skill_timers["key"] <= 0 else f'{player.skill_timers["key"]:.1f}s')
        skill_label += "   I beam: " + ("READY" if player.skill_timers["beam"] <= 0 else f'{player.skill_timers["beam"]:.1f}s')
        skill_label += "   L parry: " + ("READY" if player.parry_cooldown <= 0 else f'{player.parry_cooldown:.1f}s')
        skill_label += "   Shift dash: " + ("READY" if player.dash_cooldown <= 0 else f'{player.dash_cooldown:.1f}s')
        self.screen.blit(self.font.render(skill_label, True, TEXT_COLOR), (20, 58))
        self.screen.blit(self.hint, self.hint.get_rect(midbottom=(self.screen.get_width() // 2, self.screen.get_height() - 8)))
        if state not in ("playing", "dying"):
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            self.screen.blit(overlay, (0, 0))
            texts = {
                "start": ("AJ JACK", "Press Enter or Space to start", "A/D move | W/Space double jump | Shift dash", "J/K attack | L parry | U/I skills | H heal", "P or Esc pauses the game"),
                "paused": ("PAUSED", "Enter, P or Esc: resume", "Q: quit"),
                "won": ("VICTORY!", "R: play again | Esc: quit"),
                "lost": ("DEFEATED", "R: try again | Esc: quit"),
            }[state]
            for index, text in enumerate(texts):
                line = self.font.render(text, True, TEXT_COLOR)
                self.screen.blit(line, line.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + (index - (len(texts) - 1) / 2) * 34)))
        pygame.display.flip()

    def bar(self, x, y, width, ratio, color):
        pygame.draw.rect(self.screen, (35, 35, 45), (x, y, width, 16))
        pygame.draw.rect(self.screen, color, (x, y, round(width * max(0, min(1, ratio))), 16))
        pygame.draw.rect(self.screen, (235, 235, 235), (x, y, width, 16), 1)