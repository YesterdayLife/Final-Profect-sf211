"""Game objects and their combat state."""
import pygame
from game.settings import GROUND_HEIGHT


class Entity:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2()
        self.facing_left = False

    def update(self, dt):
        self.position += self.velocity * dt


class Player(Entity):
    SKILL_COOLDOWNS = {"key": 1.1, "beam": 4.0}

    def __init__(self, position, animator, bounds):
        super().__init__(position)
        self.animator, self.bounds = animator, bounds
        self.gravity, self.jump_speed, self.ground_y = 1800, -650, GROUND_HEIGHT
        self.on_ground, self.jumps_used = True, 0
        self.attack_name, self.attack_time = None, 0.0
        self.attack_targets = set()
        self.max_hp = self.hp = 100
        self.invulnerable = 0.0
        self.hurt_remaining = 0.0
        self.parry_remaining = 0.0
        self.parry_cooldown = 0.0
        self.heals = 3
        self.dash_remaining = self.dash_cooldown = 0.0
        self.dash_direction = 1
        self.skill_timers = {name: 0.0 for name in self.SKILL_COOLDOWNS}
        self.casting_skill = None
        self.cast_time = 0.0
        self.cast_released = False
        self.cast_direction = 1

    @property
    def hitbox(self):
        return pygame.Rect(round(self.position.x - 18), round(self.position.y - 75), 36, 75)

    def update(self, dt):
        self.invulnerable = max(0, self.invulnerable - dt)
        self.hurt_remaining = max(0, self.hurt_remaining - dt)
        self.parry_remaining = max(0, self.parry_remaining - dt)
        self.parry_cooldown = max(0, self.parry_cooldown - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        for name in self.skill_timers:
            self.skill_timers[name] = max(0, self.skill_timers[name] - dt)
        if self.dash_remaining > 0:
            self.velocity.x = self.dash_direction * 800
            self.dash_remaining = max(0, self.dash_remaining - dt)
        if self.velocity.x and not self.casting_skill and self.hurt_remaining <= 0:
            self.facing_left = self.velocity.x < 0
        self.velocity.y += self.gravity * dt
        super().update(dt)
        if self.position.y >= self.ground_y:
            self.position.y, self.velocity.y, self.on_ground, self.jumps_used = self.ground_y, 0, True, 0
        if self.attack_name:
            self.attack_time += dt
            if self.attack_time >= 4 / (12 if self.attack_name == "light_attack" else 6):
                self.attack_name = None
        if self.casting_skill:
            self.cast_time += dt
        if self.hurt_remaining > 0:
            animation = "player_hurt"
        elif self.casting_skill:
            animation = "keyboard_swing"
        elif self.attack_name:
            animation = self.attack_name
        elif not self.on_ground:
            animation = "player_double_jump" if self.jumps_used == 2 else "player_jump"
        else:
            animation = "move" if self.velocity.x else "idle"
        self.animator.update(animation, dt)
        frame = self.animator.current_frame()
        anchor_x, anchor_y = frame.anchor
        if self.facing_left:
            anchor_x = frame.image.get_width() - 1 - anchor_x
        rect = frame.image.get_rect(topleft=(round(self.position.x) - anchor_x, round(self.position.y) - anchor_y))
        clamped = rect.clamp(self.bounds)
        self.position.x += clamped.x - rect.x

    def jump(self):
        if self.jumps_used < 2 and self.hurt_remaining <= 0 and self.parry_remaining <= 0:
            self.velocity.y, self.on_ground = self.jump_speed, False
            self.jumps_used += 1

    def attack(self, name):
        if not self.attack_name and not self.casting_skill and self.hurt_remaining <= 0 and self.parry_remaining <= 0:
            self.attack_name, self.attack_time = name, 0.0
            self.attack_targets.clear()

    def dash(self, direction=0):
        if self.dash_cooldown > 0 or self.casting_skill or self.hurt_remaining > 0 or self.parry_remaining > 0:
            return
        self.dash_direction = direction or (-1 if self.facing_left else 1)
        self.facing_left = self.dash_direction < 0
        self.dash_remaining, self.dash_cooldown = 0.18, 0.8
        self.invulnerable = max(self.invulnerable, self.dash_remaining)

    def cast(self, name):
        if self.skill_timers[name] > 0 or self.casting_skill or self.attack_name or self.dash_remaining > 0 or self.hurt_remaining > 0 or self.parry_remaining > 0:
            return False
        self.skill_timers[name] = self.SKILL_COOLDOWNS[name]
        self.casting_skill = name
        self.cast_time = 0.0
        self.cast_released = False
        self.cast_direction = -1 if self.facing_left else 1
        return True

    def consume_cast(self):
        """Release the projectile once, as the firing animation reaches frame 2."""
        if self.casting_skill and not self.cast_released and self.cast_time >= 0.1:
            self.cast_released = True
            return self.casting_skill, self.cast_direction
        return None

    def finish_cast(self):
        if self.casting_skill and self.cast_time >= 0.4:
            self.casting_skill = None

    def parry(self):
        if (self.parry_cooldown > 0 or self.hurt_remaining > 0 or self.casting_skill
                or self.attack_name or self.dash_remaining > 0):
            return False
        self.parry_remaining = 0.25
        self.parry_cooldown = 0.8
        return True

    def take_damage(self, amount):
        if self.hp > 0 and self.invulnerable <= 0:
            self.hp = max(0, self.hp - amount)
            self.invulnerable = 0.8
            self.hurt_remaining = 0.4
            self.velocity.x = 0
            self.dash_remaining = 0
            self.parry_remaining = 0
            self.attack_name = None
            self.casting_skill = None
            self.animator.update("player_hurt" if self.hp else "player_defeat", 0)

    def update_defeat(self, dt):
        self.velocity.x = 0
        self.velocity.y += self.gravity * dt
        self.position.y = min(self.ground_y, self.position.y + self.velocity.y * dt)
        self.animator.update("player_defeat", dt)

    def heal(self):
        if self.heals and self.hp < self.max_hp and self.hurt_remaining <= 0:
            self.heals -= 1
            self.hp = min(self.max_hp, self.hp + 35)


class Boss(Entity):
    def __init__(self, position, phase=1):
        super().__init__(position)
        self.phase = phase
        self.max_hp = self.hp = 210 if phase == 1 else 300
        self.hurt_remaining = 0.0
        self.hurt_elapsed = 0.0
        self.transform_remaining = 0.0

    def take_damage(self, amount):
        if self.hp <= 0 or self.transform_remaining > 0:
            return
        self.hp = max(0, self.hp - amount)

    @property
    def hitbox(self):
        return pygame.Rect(round(self.position.x - 40), round(self.position.y - 125), 80, 125)


class BossChild(Entity):
    def __init__(self, position):
        super().__init__(position)
        self.hp = 32
        self.life = 14.0

    @property
    def hitbox(self):
        return pygame.Rect(round(self.position.x - 20), round(self.position.y - 20), 40, 40)

    def update(self, dt):
        super().update(dt)
        self.life -= dt


class Projectile(Entity):
    def __init__(self, position, velocity, owner="boss", damage=15, sprite="midterm_paper_trail", size=24, life=6.0):
        super().__init__(position)
        self.velocity = pygame.Vector2(velocity)
        self.owner, self.damage, self.sprite, self.size = owner, damage, sprite, size
        self.life = life

    @property
    def hitbox(self):
        return pygame.Rect(round(self.position.x - self.size / 2), round(self.position.y - self.size / 2), self.size, self.size)

    def update(self, dt):
        super().update(dt)
        self.life -= dt
