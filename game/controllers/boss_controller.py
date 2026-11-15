"""Boss attacks use a warning, an execution, and a recovery window."""
from game.controllers.controller import Controller


class BossController(Controller):
    SKILLS = {1: ("papers", "slash", "summon", "energy"),
              2: ("volley", "dash", "summon", "vortex")}

    def __init__(self, entity, player):
        super().__init__(entity)
        self.player = player
        self.timer = 1.25
        self.state = "waiting"
        self.skill = None
        self.index = 0

    def interrupt(self):
        self.state = "waiting"
        self.skill = None
        self.timer = max(self.timer, 0.7)

    def update(self, dt):
        if self.entity.hurt_remaining > 0:
            self.entity.velocity.x = 0
            return None
        distance = self.player.position.x - self.entity.position.x
        if self.state == "waiting" and abs(distance) > 210:
            self.entity.velocity.x = (1 if distance > 0 else -1) * (100 if self.entity.phase == 1 else 140)
        else:
            self.entity.velocity.x = 0
        self.timer -= dt
        if self.timer > 0:
            return None
        if self.state == "waiting":
            skills = self.SKILLS[self.entity.phase]
            self.skill = skills[self.index % len(skills)]
            self.index += 1
            self.state = "charging"
            self.timer = 0.8 if self.entity.phase == 1 else 0.65
            return None
        action = self.skill
        self.state = "waiting"
        self.timer = 1.25 if self.entity.phase == 1 else 1.0
        return action
