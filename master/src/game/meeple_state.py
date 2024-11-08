from enum import Enum


class MeepleState(Enum):
    IDLE = 0
    MOVING = 1
    WITH_BULLET = 2
    DEAD = 3
