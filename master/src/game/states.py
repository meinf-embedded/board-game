import logging
import asyncio

from typing import Union

from random import choice, randint
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
        ready_players = [p.is_ready() for p in game_lobby.players]

        logging.info(f"Ready Players: {ready_players}")

        if len(ready_players) >= game_lobby.players_max and all(ready_players):
            game_lobby.players_remaining.extend(game_lobby.players)
            return MOVING
        # else:
        #     await game_lobby.callbacks.notify_game_state(cls.value())

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
        logging.info(f"Checking if all players have moved, {game_lobby}")
        if (
            all(player.has_moved for player in game_lobby.players_remaining)
            or len(game_lobby.players_remaining) == 0
        ):
            return SHOOTING
        await cls._notify_player_moving_turn(game_lobby)

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        player_names = [player.id for player in game_lobby.players_remaining]
        logging.info(f"Initializing moving state with players: {player_names}")
        for player in game_lobby.players_remaining:
            player.state = PlayerState.MOVING
            player.has_moved = False
        if len(game_lobby.players_remaining) > 0:
            await cls._notify_player_moving_turn(game_lobby)

    @classmethod
    async def _notify_player_moving_turn(cls, game_lobby):
        non_moved = [
            player
            for player in game_lobby.players_remaining
            if player.state == PlayerState.MOVING and not player.has_moved
        ]

        if not non_moved:
            logging.info("No players to move")
            return

        moving_player = choice(non_moved)
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
        if len(game_lobby.players_remaining) <= 1:
            return ENDING
        return MOVING

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        await game_lobby.decision.decided.acquire()

        for player in game_lobby.players_remaining:
            player.state = PlayerState.IDLE
        random_player = game_lobby.get_random_player()

        random_player.state = PlayerState.WITH_BULLET
        await game_lobby.callbacks.notify_player_has_bullet(
            game_lobby.players_remaining, random_player.id
        )

        logging.info(
            f"Player {random_player.id} has bullet, state: {random_player.state}"
        )

        await asyncio.create_task(cls.wait_decision(game_lobby, random_player))

    async def wait_decision(game_lobby, player):

        logging.info(
            f"Waiting for player {player.id} decision for {game_lobby.decision.timeout} seconds"
        )

        try:
            await asyncio.wait_for(
                game_lobby.decision.decided.acquire(), game_lobby.decision.timeout
            )
        except:
            ...

        try:
            if game_lobby.decision.decision:
                # Wait for deaths
                logging.info(f"Player {player.id} shot... WAITING FOR DEATHS")

                try:
                    await asyncio.sleep(game_lobby.death_wait_time)
                    try:
                        await game_lobby.any_died.acquire(timeout=0)
                    except:
                        ...

                    if game_lobby.any_died._value > 0:
                        logging.info(f"Player {player.id} shot and someone died")
                        while game_lobby.any_died._value > 0:
                            await game_lobby.any_died.acquire()
                    else:
                        logging.info(f"Player {player.id} shot and no one died")
                        game_lobby.player_die(player.id, force_death=True)
                        await game_lobby.callbacks.notify_player_has_died(
                            player.id, True
                        )
                except:
                    ...

            else:
                # Randomize player death
                if randint(0, 100) > game_lobby.decision.negative_penalty * 100:
                    game_lobby.player_die(player.id, force_death=True)
                    await game_lobby.callbacks.notify_player_has_died(player.id, True)

                    logging.info(f"Player {player.id} didn't shoot and died")
                else:
                    logging.info(f"Player {player.id} didn't shoot and survived")

        finally:
            game_lobby.decision.decided.release()
            game_lobby.decision.decision = False
            player.state = PlayerState.IDLE

            await game_lobby.state_check()


class ENDING(GameState):

    @classmethod
    def value(cls):
        return "ending"

    @classmethod
    async def check_state(
        cls,
        game_lobby,
    ) -> Union["GameState", None]:
        return JOINING

    @classmethod
    async def init_state(
        cls,
        game_lobby,
    ):
        if len(game_lobby.players_remaining) == 1:
            logging.info(f"Game ended, winner is {game_lobby.players_remaining[0].id}")
            await cls._notify_winner(cls, game_lobby)
        else:
            logging.info("Game ended, no winner")

        logging.info("Resetting game in 10 seconds ...")
        await asyncio.sleep(10)
        await game_lobby.state_check()

    async def _notify_winner(cls, game_lobby):
        winner = game_lobby.players_remaining.pop()
        await game_lobby.callbacks.notify_player_won(winner.id)
        logging.info(f"Player {winner.id} won")
