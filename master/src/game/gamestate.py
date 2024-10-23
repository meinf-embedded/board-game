from enum import Enum


class GameState(Enum):
    WAITING_FOR_PLAYERS = 0
    FULL_LOBBY = 1
    INGAME = 2
