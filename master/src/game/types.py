import sys
from dataclasses import dataclass, field
from random import choice, randint

from typing import Set, Union

import logging

from game.callbacks import Callbacks
from game.states import GameState, PlayerState

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@dataclass
class Player:
    id: str
    state: PlayerState = PlayerState.IDLE
    ready_meeple: bool = False
    ready_base: bool = False
    has_moved: bool = False

    def is_ready(self):
        return self.ready_meeple and self.ready_base


@dataclass
class GameLobby:
    gamestate: GameState = GameState.JOINING
    player_ids: Set[str] = field(default_factory=set)
    players: Set[Player] = field(default_factory=set)
    players_remaining: Set[Player] = field(default_factory=set)
    players_max: int = 1
    no_shoot_penalty: float = 0.5

    callbacks: Callbacks

    def state_check(self):
        new_state = self.gamestate.check_state(self)

        if new_state:
            self.gamestate = new_state
            self.callbacks.notify_game_state(new_state.value)

    def get_player(self, player_id: str, create=False) -> Union[Player, None]:
        for player in self.players:
            if player.id == player_id:
                return player
        if create:
            player = Player(player_id)
            self.players.add(player)
            self.player_ids.add(player_id)
            return player
        return None

    def add_meeple(self, player_id: str):
        player = self.get_player(player_id, create=True)
        player.ready_meeple = True
        self.state_check()

    def add_base(self, player_id: str):
        player = self.get_player(player_id, create=True)
        player.ready_base = True
        self.state_check()

    def get_random_player(self):
        return choice(self.players_remaining)

    def reset(self):
        self.players_remaining = self.players.copy()
        for player in self.players:
            player.has_moved = False
            player.state = PlayerState.IDLE

    def player_die(self, player_id: str):
        player = self.get_player(player_id)
        if not player:
            return

        player.state = PlayerState.DEAD
        self.players_remaining.remove(player)
        self.state_check()

    def player_move(self, player_id: str):
        player = self.get_player(player_id)
        if not player:
            return

        player.has_moved = True
        self.state_check()

    def player_shoot(self, player_id: str, is_shoot: bool):
        player = self.get_player(player_id)
        if not player:
            return

        player.state = PlayerState.IDLE
        if not is_shoot:
            if randint(0, 100) > self.no_shoot_penalty * 100:
                self.players_remaining.remove(player)
                self.callbacks.notify_player_has_died(player.id)

        self.state_check()
