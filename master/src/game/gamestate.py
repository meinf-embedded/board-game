from enum import Enum


class GameState(Enum):
    WAITING_FOR_PLAYERS = 0
    WAITING_FOR_READY = 1
    INGAME = 2
    MOVING = 3
    MAKING_DECISION = 4
