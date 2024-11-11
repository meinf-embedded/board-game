from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from random import choice

from enum import Enum
from typing import Set, Union
from game.callbacks import Callbacks
from random import randint

import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class GameState(ABC):
    @classmethod
    @abstractmethod
    def check_state(
        cls,
        game_lobby: "GameLobby",
    ) -> Union["GameState", None]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def init_state(
        cls,
        game_lobby: "GameLobby",
    ):
        raise NotImplementedError


class JOINING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby: "GameLobby",
    ) -> Union["GameState", None]:
        # Check whether everyone that joined is ready
        if len(game_lobby.players) == game_lobby.players_max:
            game_lobby.players_remaining.update(game_lobby.players)
            return SHOOTING

    @classmethod
    def init_state(
        cls,
        game_lobby: "GameLobby",
    ):
        game_lobby.reset()


class MOVING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby: "GameLobby",
    ) -> Union["GameState", None]:
        # Check whether everyone has moved
        if all(player.has_moved() for player in game_lobby.players_remaining):
            return SHOOTING
        cls._notify_player_moving_turn(game_lobby)

    @classmethod
    def init_state(
        cls,
        game_lobby: "GameLobby",
    ):
        for player in game_lobby.players_remaining:
            player.state = PlayerState.MOVING
        cls._notify_player_moving_turn(game_lobby)

    @classmethod
    def _notify_player_moving_turn(cls, game_lobby: "GameLobby"):
        player = choice(
            [
                player
                for player in game_lobby.players_remaining
                if player.state == PlayerState.MOVING
            ]
        )
        logging.info(f"Player {player.id} moving turn")
        game_lobby.callbacks.notify_player_moving_turn(player.id)


class SHOOTING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby: "GameLobby",
    ) -> Union["GameState", None]:
        if len(game_lobby.players_remaining) == 1:
            return ENDING

    @classmethod
    def init_state(
        cls,
        game_lobby: "GameLobby",
    ):
        for player in game_lobby.players_remaining:
            player.state = PlayerState.SHOOTING
        random_player = game_lobby.get_random_player()

        logging.info(f"Player {random_player.id} has bullet")

        random_player.state = PlayerState.WITH_BULLET
        game_lobby.callbacks.notify_player_has_bullet(
            game_lobby.players_remaining, random_player.id
        )
        return SHOOTING


class ENDING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby: "GameLobby",
    ) -> Union["GameState", None]:
        logging.info(f"Game ended, winner is {game_lobby.players_remaining.pop().id}")
        game_lobby.reset()
        return MOVING

    @classmethod
    def init_state(
        cls,
        game_lobby: "GameLobby",
    ): ...


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
