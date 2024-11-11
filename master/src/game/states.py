import logging

from abc import ABC, abstractmethod
from typing import Union
from enum import Enum

from random import choice


class PlayerState(Enum):
    IDLE = 0
    MOVING = 1
    WITH_BULLET = 2
    DEAD = 3


class GameState(ABC):
    @classmethod
    @abstractmethod
    def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def init_state(
        cls,
        game_lobby,
    ):
        raise NotImplementedError


class JOINING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        # Check whether everyone that joined is ready
        if len(game_lobby.players) == game_lobby.players_max:
            game_lobby.players_remaining.update(game_lobby.players)
            return SHOOTING

    @classmethod
    def init_state(
        cls,
        game_lobby,
    ):
        game_lobby.reset()


class MOVING(GameState):

    @classmethod
    def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        # Check whether everyone has moved
        if all(player.has_moved() for player in game_lobby.players_remaining):
            return SHOOTING
        cls._notify_player_moving_turn(game_lobby)

    @classmethod
    def init_state(
        cls,
        game_lobby,
    ):
        for player in game_lobby.players_remaining:
            player.state = PlayerState.MOVING
        cls._notify_player_moving_turn(game_lobby)

    @classmethod
    def _notify_player_moving_turn(cls, game_lobby):
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
        game_lobby,
    ) -> Union["GameState", None]:
        if len(game_lobby.players_remaining) == 1:
            return ENDING

    @classmethod
    def init_state(
        cls,
        game_lobby,
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
        game_lobby,
    ) -> Union["GameState", None]:
        logging.info(f"Game ended, winner is {game_lobby.players_remaining.pop().id}")
        game_lobby.reset()
        return MOVING

    @classmethod
    def init_state(
        cls,
        game_lobby,
    ): ...
