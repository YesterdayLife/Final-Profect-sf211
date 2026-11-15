"""Keyboard input for the player."""
import pygame
from game.controllers.controller import Controller


class PlayerController(Controller):
    def __init__(self, entity, speed=280):
        super().__init__(entity)
        self.speed = speed

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if self.entity.hurt_remaining > 0 or self.entity.parry_remaining > 0:
            self.entity.velocity.x = 0
            return
        self.entity.velocity.x = self.speed * ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a]))

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or getattr(event, "repeat", False):
            return None
        if event.key in (pygame.K_w, pygame.K_SPACE):
            self.entity.jump()
        elif event.key == pygame.K_j:
            self.entity.attack("light_attack")
        elif event.key == pygame.K_k:
            self.entity.attack("heavy_attack")
        elif event.key == pygame.K_l:
            self.entity.parry()
        elif event.key == pygame.K_h:
            self.entity.heal()
        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            keys = pygame.key.get_pressed()
            direction = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.entity.dash(direction)
        elif event.key == pygame.K_u:
            return "key"
        elif event.key == pygame.K_i:
            return "beam"
        return None
