"""Shared interface for player and AI controllers."""
from abc import ABC, abstractmethod


class Controller(ABC):
    def __init__(self, entity):
        self.entity = entity

    @abstractmethod
    def update(self, dt):
        """Apply control decisions to the entity for this frame."""
