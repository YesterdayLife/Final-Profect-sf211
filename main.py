"""Run the AJ Jack Pygame window."""

import sys

import pygame

from game.assets import load_font, load_sound, load_sprite_atlas
from game.settings import ACCENT_COLOR, BG_COLOR, FPS, HEIGHT, TEXT_COLOR, TITLE, WIDTH

SPEED = 280


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    walk = load_sprite_atlas()["move"]
    sprites = []
    for frame in walk:
        scale = 0.28
        size = tuple(round(axis * scale) for axis in frame.image.get_size())
        anchor = tuple(round(axis * scale) for axis in frame.anchor)
        sprite = pygame.transform.scale(frame.image, size)
        sprites.append((sprite, anchor))
    position = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    velocity = pygame.Vector2()
    elapsed = 0.0
    facing_left = False

    font = load_font(None, 28)
    hint = font.render("WASD or arrow keys to move    Esc to quit", True, TEXT_COLOR)
    hint_rect = hint.get_rect(midbottom=(WIDTH // 2, HEIGHT - 24))

    blip = None
    if pygame.mixer.get_init():
        try:
            blip = load_sound("blip.wav")
            blip.play()
        except (FileNotFoundError, pygame.error):
            blip = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        velocity.xy = (
            float((keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])),
            float((keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])),
        )
        if velocity.length_squared() > 0:
            velocity.scale_to_length(SPEED)
        if velocity.x:
            facing_left = velocity.x < 0
        elapsed = elapsed + dt if velocity else 0.0
        player, (anchor_x, anchor_y) = sprites[int(elapsed * 12) % len(sprites)]
        if facing_left:
            player = pygame.transform.flip(player, True, False)
            anchor_x = player.get_width() - 1 - anchor_x
        position += velocity * dt
        rect = player.get_rect(topleft=(round(position.x) - anchor_x, round(position.y) - anchor_y))
        clamped = rect.clamp(screen.get_rect())
        position += pygame.Vector2(clamped.x - rect.x, clamped.y - rect.y)
        rect = clamped

        screen.fill(BG_COLOR)
        pygame.draw.circle(screen, ACCENT_COLOR, rect.center, 54, width=2)
        screen.blit(player, rect)
        screen.blit(hint, hint_rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
