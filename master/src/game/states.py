import logging
import asyncio

from typing import Union

from random import choice
from game.types import GameState, PlayerState


class JOINING(GameState):

    @classmethod
    def value(cls):
        return "joining"

    @classmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        # Check whether everyone that joined is ready
        if len(game_lobby.players) == game_lobby.players_max:
            game_lobby.players_remaining.append(*game_lobby.players)
            return MOVING

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        game_lobby.reset()


class MOVING(GameState):

    @classmethod
    def value(cls):
        return "moving"

    @classmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        # Check whether everyone has moved
        if all(player.has_moved for player in game_lobby.players_remaining):
            return SHOOTING
        await cls._notify_player_moving_turn(game_lobby)

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        for player in game_lobby.players_remaining:
            player.state = PlayerState.MOVING
        await cls._notify_player_moving_turn(game_lobby)

    @classmethod
    async def _notify_player_moving_turn(cls, game_lobby):
        moving_player = choice(
            [
                player
                for player in game_lobby.players_remaining
                if player.state == PlayerState.MOVING
            ]
        )
        logging.info(f"Player {moving_player.id} moving turn")
        for player in game_lobby.players_remaining:
            await game_lobby.callbacks.notify_player_moving_turn(
                player.id, player.id == moving_player.id
            )


class SHOOTING(GameState):

    @classmethod
    def value(cls):
        return "shooting"

    @classmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        if len(game_lobby.players_remaining) == 1:
            return ENDING
        return MOVING

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        for player in game_lobby.players_remaining:
            player.state = PlayerState.IDLE
        random_player = game_lobby.get_random_player()

        logging.info(f"Player {random_player.id} has bullet")

        random_player.state = PlayerState.WITH_BULLET
        await game_lobby.callbacks.notify_player_has_bullet(
            game_lobby.players_remaining, random_player.id
        )


class ENDING(GameState):

    @classmethod
    def value(cls):
        return "ending"

    @classmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        logging.info(f"Game ended, winner is {game_lobby.players_remaining.pop().id}")
        await cls._notify_winner(game_lobby)

        await asyncio.sleep(10)
        game_lobby.reset()
        return MOVING

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ): ...

    async def _notify_winner(cls, game_lobby):
        winner = game_lobby.players_remaining.pop()
        await game_lobby.callbacks.notify_player_won(winner.id, 1)
        logging.info(f"Player {winner.id} won")
