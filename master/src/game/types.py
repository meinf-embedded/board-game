from dataclasses import dataclass, field
from random import choice

from enum import Enum
from typing import Set, Union


class GameState(Enum):
    JOINING = 0
    MOVING = 1
    SHOOTING = 2


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

    def is_ready(self):
        return self.ready_meeple and self.ready_base


@dataclass
class GameLobby:
    gamestate: GameState = GameState.JOINING
    player_ids: Set[str] = field(default_factory=set)
    players: Set[Player] = field(default_factory=set)
    players_remaining: Set[Player] = field(default_factory=set)
    players_max: int = 1

    def state_check(self):
        new_state = None
        if self.gamestate == GameState.JOINING:
            if len(self.players) == self.players_max:
                new_state = GameState.MOVING

        if new_state:
            self.gamestate = new_state

    def get_player(self, player_id: str) -> Union[Player, None]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def add_meeple(self, player_id: str) -> "GameLobby":
        player = self.get_player(player_id)
        if not player:
            player = Player(player_id)
            self.players.add(player)
            self.player_ids.add(player_id)
        player.ready_meeple = True
        self.state_check()
        return self

    def add_base(self, player_id: str) -> "GameLobby":
        player = self.get_player(player_id)
        if not player:
            player = Player(player_id)
            self.players.add(player)
            self.player_ids.add(player_id)
        player.ready_base = True
        self.state_check()
        return self

    def get_random_meeple(self):
        return choice(self.players)
