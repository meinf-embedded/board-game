from dataclasses import dataclass
from typing import Union

from abc import ABC, abstractmethod
from enum import Enum


class PlayerState(Enum):
    IDLE = 0
    MOVING = 1
    WITH_BULLET = 2
    DEAD = 3


@dataclass
class Player:
    id: str
    state: PlayerState = PlayerState.IDLE
    ready_meeple: bool = False
    ready_base: bool = False
    has_moved: bool = False

    def is_ready(self):
        return self.ready_meeple and self.ready_base

    def __hash__(self) -> int:
        return hash(self.id)


class GameState(ABC):

    def value(cls) -> str:
        return ""

    @classmethod
    @abstractmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        raise NotImplementedError
