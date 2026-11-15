"""Game state, combat and boss-fight rules."""
import pygame
from game.assets import load_font, load_sound, load_sprite_atlas
from game.animation import Animator
from game.controllers.player_controller import PlayerController
from game.controllers.boss_controller import BossController
from game.controllers.boss_child_controller import BossChildController
from game.entity import Player, Boss, BossChild, Projectile
from game.renderer import Renderer
from game.settings import FPS, HEIGHT, TITLE, WIDTH, GROUND_HEIGHT


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.atlas = load_sprite_atlas()
        self.renderer = Renderer(self.screen, load_font(None, 25), self.atlas)
        self.reset("start")
        if pygame.mixer.get_init():
            try:
                load_sound("blip.wav").play()
            except (FileNotFoundError, pygame.error):
                pass

    def reset(self, state="playing"):
        self.renderer.clear_shake()
        self.player = Player((WIDTH // 2, GROUND_HEIGHT), Animator(self.atlas), self.renderer.background.get_rect())
        self.player_controller = PlayerController(self.player)
        self.boss = Boss((min(self.renderer.background.get_width() - 100, WIDTH + 150), GROUND_HEIGHT))
        self.boss_controller = BossController(self.boss, self.player)
        self.projectiles, self.children, self.effects = [], [], []
        self.boss_dash_time = 0.0
        self.defeat_time = 0.0
        self.state = state

    def add_effect(self, name, position, duration=0.55, size=100):
        self.effects.append({"name": name, "position": pygame.Vector2(position), "time": 0.0, "duration": duration, "size": size})

    def cast_player(self, name, direction):
        position = (self.player.position.x + direction * 30, self.player.position.y - 50)
        if name == "key":
            self.projectiles.append(Projectile(position, (direction * 570, 0), "player", 18, "key_projectile", 25, 2.5))
            self.add_effect("blue_sparks", position, 0.35, 60)
        elif name == "beam":
            self.projectiles.append(Projectile(position, (direction * 440, 0), "player", 38, "long_projectile", 45, 2.7))
            self.add_effect("swing_2", position, 0.4, 80)

    def hit_player(self, damage, source):
        # Only attacks arriving from the direction the player faces can be parried.
        facing = -1 if self.player.facing_left else 1
        if self.player.parry_remaining > 0 and (source.position.x - self.player.position.x) * facing >= 0:
            self.player.parry_remaining = 0
            # Protect against the same rushing boss hitting again immediately.
            self.player.invulnerable = max(self.player.invulnerable, 0.4)
            self.renderer.shake(5, 0.16)
            self.add_effect("parry_flash", (self.player.position.x + facing * 30, self.player.position.y - 48), 0.45, 110)
            return True
        previous_hp = self.player.hp
        self.player.take_damage(damage)
        if self.player.hp < previous_hp:
            self.renderer.shake(8, 0.22)
        return False

    def hit_target(self, target, damage):
        previous_hp = target.hp
        if target is self.boss:
            target.take_damage(damage)
        else:
            target.hp -= damage
        if target.hp < previous_hp:
            self.renderer.shake(6 if damage >= 25 else 3, 0.16)

    def boss_attack(self, skill):
        boss = self.boss
        direction = -1 if boss.facing_left else 1
        origin = pygame.Vector2(boss.position.x + direction * 45, boss.position.y - 55)
        phase = boss.phase
        if skill in ("papers", "volley"):
            sprite = "midterm_paper_trail" if phase == 1 else "final_projectile"
            velocities = [(direction * 350, 0)] if phase == 1 else [(direction * 360, -90), (direction * 400, 0), (direction * 360, 90)]
            for velocity in velocities:
                self.projectiles.append(Projectile(origin, velocity, "boss", 15 if phase == 1 else 18, sprite, 26))
            self.add_effect("midterm_loose_papers" if phase == 1 else "final_swirl_1", origin, 0.6, 100)
            self.add_effect("midterm_paper_trail" if phase == 1 else "final_swirl_2", origin, 0.45, 80)
        elif skill == "summon":
            self.add_effect("midterm_paper_swirl" if phase == 1 else "final_sigil", origin, 0.8, 130)
            for offset in (-45, 45):
                if len(self.children) < 4:
                    child = BossChild((boss.position.x + offset, boss.position.y - 150))
                    self.children.append((child, BossChildController(child, self.player)))
        elif skill in ("slash", "dash"):
            if skill == "dash":
                self.boss_dash_time = 0.38
                boss.velocity.x = direction * 560
            # A short-range hitbox is active when the attack is released.
            attack = pygame.Rect(0, 0, 150 if phase == 1 else 200, 110)
            attack.midleft = (round(boss.position.x if direction > 0 else boss.position.x - attack.width), round(boss.position.y - 55))
            if attack.colliderect(self.player.hitbox):
                self.hit_player(20 if phase == 1 else 25, boss)
            self.add_effect("midterm_slash_fx" if phase == 1 else "final_dash_fx", origin, 0.55, 170)
            self.add_effect("midterm_debris" if phase == 1 else "final_slash_fx", origin, 0.45, 120)
        else:
            # A ground-level wave makes both energy attacks jumpable.
            sprite = "midterm_red_sigil" if phase == 1 else "final_vortex"
            self.projectiles.append(Projectile(origin, (direction * (250 if phase == 1 else 300), 0), "boss", 20, sprite, 60, 4))
            self.add_effect("midterm_red_sigil" if phase == 1 else "final_burst", origin, 0.7, 120)

    def update(self, dt):
        if self.boss.transform_remaining > 0:
            self.boss.transform_remaining = max(0, self.boss.transform_remaining - dt)
            return
        if self.boss.hurt_remaining > 0:
            self.boss.hurt_remaining = max(0, self.boss.hurt_remaining - dt)
            self.boss.hurt_elapsed += dt
        self.player_controller.update(dt)
        self.player.update(dt)
        cast = self.player.consume_cast()
        if cast:
            self.cast_player(*cast)
        self.player.finish_cast()
        if self.boss_dash_time > 0:
            self.boss_dash_time = max(0, self.boss_dash_time - dt)
            self.boss.update(dt)
            self.boss.position.x = max(55, min(self.renderer.background.get_width() - 55, self.boss.position.x))
            if self.boss.hitbox.colliderect(self.player.hitbox):
                self.hit_player(25, self.boss)
        self.boss.facing_left = self.player.position.x < self.boss.position.x
        action = None if self.boss_dash_time > 0 else self.boss_controller.update(dt)
        if self.boss_dash_time <= 0 and self.boss.hurt_remaining <= 0:
            self.boss.update(dt)
            self.boss.position.x = max(55, min(self.renderer.background.get_width() - 55, self.boss.position.x))
        if action:
            self.boss_attack(action)
        targets = [self.boss] + [child for child, _ in self.children]
        if self.player.attack_name:
            duration = 4 / (12 if self.player.attack_name == "light_attack" else 6)
            if duration * 0.25 <= self.player.attack_time <= duration * 0.8:
                facing = -1 if self.player.facing_left else 1
                attack = pygame.Rect(0, 0, 100 if self.player.attack_name == "light_attack" else 135, 95)
                attack.midleft = (round(self.player.position.x if facing > 0 else self.player.position.x - attack.width), round(self.player.position.y - 48))
                for target in targets:
                    if target not in self.player.attack_targets and attack.colliderect(target.hitbox):
                        self.hit_target(target, 12 if self.player.attack_name == "light_attack" else 25)
                        self.player.attack_targets.add(target)
                        self.add_effect("impact_sparks", target.hitbox.center, 0.3, 70)
        for child, controller in self.children:
            controller.update(dt)
            child.update(dt)
            if child.hitbox.colliderect(self.player.hitbox):
                self.hit_player(12, child)
                child.hp = 0
                self.add_effect("key_fragments", child.position, 0.4, 65)
        self.children = [(child, controller) for child, controller in self.children if child.hp > 0 and child.life > 0]
        for projectile in self.projectiles:
            projectile.update(dt)
            if projectile.owner == "boss" and projectile.hitbox.colliderect(self.player.hitbox):
                self.hit_player(projectile.damage, projectile)
                projectile.life = 0
                self.add_effect("impact_sparks", projectile.position, 0.3, 60)
            elif projectile.owner == "player":
                for target in targets:
                    if target.hp > 0 and projectile.hitbox.colliderect(target.hitbox):
                        self.hit_target(target, projectile.damage)
                        projectile.life = 0
                        self.add_effect("impact_sparks", projectile.position, 0.3, 70)
                        break
        bounds = self.renderer.background.get_width()
        self.projectiles = [p for p in self.projectiles if p.life > 0 and -100 < p.position.x < bounds + 100 and -100 < p.position.y < HEIGHT + 100]
        for effect in self.effects:
            effect["time"] += dt
        self.effects = [e for e in self.effects if e["time"] < e["duration"]]
        if self.player.hp <= 0:
            self.state = "dying"
            self.player.invulnerable = 0
        elif self.boss.hp <= 0:
            if self.boss.phase == 1:
                self.renderer.shake(12, 0.5)
                self.add_effect("final_burst", (self.boss.position.x, self.boss.position.y - 80), 1.0, 180)
                self.boss = Boss(self.boss.position, 2)
                self.boss.transform_remaining = 1.2
                self.player.velocity.x = 0
                self.player.attack_name = None
                self.player.casting_skill = None
                self.boss_controller = BossController(self.boss, self.player)
                self.projectiles.clear()
                self.children.clear()
                self.boss_dash_time = 0
            else:
                self.renderer.shake(10, 0.4)
                self.state = "won"

    def run(self):
        running = True
        try:
            while running:
                dt = min(self.clock.tick(FPS) / 1000, 0.05)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                        if self.state == "start":
                            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                                self.state = "playing"
                            elif event.key == pygame.K_ESCAPE:
                                running = False
                        elif self.state == "playing":
                            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                                self.state = "paused"
                            elif self.boss.transform_remaining <= 0:
                                skill = self.player_controller.handle_event(event)
                                if skill:
                                    self.player.cast(skill)
                        elif self.state == "paused":
                            if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN):
                                self.state = "playing"
                            elif event.key == pygame.K_q:
                                running = False
                        elif self.state in ("won", "lost") and event.key == pygame.K_r:
                            self.reset()
                        elif self.state in ("won", "lost") and event.key == pygame.K_ESCAPE:
                            running = False
                if not running:
                    break
                if self.state == "playing":
                    self.update(dt)
                elif self.state == "dying":
                    self.player.update_defeat(dt)
                    self.defeat_time += dt
                    if self.defeat_time >= 1.0:
                        self.state = "lost"
                self.renderer.draw(self.player, self.boss, self.boss_controller, self.projectiles, self.children, self.effects, self.state, dt if self.state in ("playing", "dying", "won", "lost") else 0)
        finally:
            pygame.quit()

