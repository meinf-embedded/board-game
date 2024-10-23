from dataclasses import dataclass, field
from typing import Set

from game.gamestate import GameState
from game.meeple import Meeple

from random import choice


@dataclass
class GameLobby:
    gamestate: GameState = GameState.WAITING_FOR_PLAYERS
    meeples: Set[Meeple] = field(default_factory=set)
    max_players: int = 1

    def add_meeple(self, meeple: Meeple) -> "GameLobby":
        self.meeples.add(meeple)
        return self

    def get_random_meeple(self):
        return choice(self.meeples)
