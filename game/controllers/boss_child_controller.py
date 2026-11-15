"""A minion follows the player until it gets close enough to strike."""
from game.controllers.controller import Controller


class BossChildController(Controller):
    def __init__(self, entity, player):
        super().__init__(entity)
        self.player = player

    def update(self, dt):
        offset = self.player.position - self.entity.position
        if offset.length_squared() > 1:
            self.entity.velocity = offset.normalize() * 95
            self.entity.facing_left = offset.x < 0
        else:
            self.entity.velocity.update(0, 0)
