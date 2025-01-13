import asyncio
import sys
from dataclasses import dataclass, field
from random import choice

from typing import List, Set, Union

import logging

from game.types import Player, GameState
from game.callbacks import Callbacks
from game.states import PlayerState, JOINING, MOVING, SHOOTING

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@dataclass
class Decision:
    decided: asyncio.Semaphore = field(default_factory=asyncio.Semaphore)
    decision: bool = False
    timeout: int = 60
    negative_penalty: float = 0.33


@dataclass
class GameLobby:
    gamestate: GameState = JOINING
    player_ids: Set[str] = field(default_factory=set)
    players: Set[Player] = field(default_factory=set)
    players_remaining: List[Player] = field(default_factory=list)
    players_max: int = 1
    no_shoot_penalty: float = 0.33

    decision: Decision = field(default_factory=Decision)

    any_died: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(0))
    death_wait_time: int = 10

    callbacks: Callbacks = None

    def __str__(self) -> str:
        return f"GameLobby(gamestate={self.gamestate}, players_max={self.players_max}, players={self.players}, no_shoot_penalty={self.no_shoot_penalty}, decision={self.decision}, any_died={self.any_died})"

    async def state_check(self):
        new_state = await self.gamestate.check_state(self)

        if new_state:
            self.gamestate = new_state
            await self.callbacks.notify_game_state(new_state.value())
            await self.gamestate.init_state(self)

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

    async def add_meeple(self, player_id: str):
        if not self.gamestate == JOINING:
            logging.error(
                f"Player {player_id} tried to add meeple in gamestate {self.gamestate.value()}"
            )
            return

        player = self.get_player(player_id, create=True)
        player.ready_meeple = True
        await self.state_check()

    async def add_base(self, player_id: str):
        if not self.gamestate == JOINING:
            logging.error(
                f"Player {player_id} tried to add base in gamestate {self.gamestate.value()}"
            )
            return
        player = self.get_player(player_id, create=True)
        player.ready_base = True
        await self.state_check()

    def get_random_player(self):
        return choice(self.players_remaining)

    def reset(self):
        for player in self.players:
            player.has_moved = False
            player.ready_meeple = False
            player.ready_base = False
            player.state = PlayerState.IDLE
        self.players_remaining = list()
        self.players = set()
        self.player_ids = set()
        self.any_died = asyncio.Semaphore(0)

    def player_die(self, player_id: str, force_death=False):
        if not self.gamestate == SHOOTING:
            logging.error(
                f"Player {player_id} tried to die in gamestate {self.gamestate.value()}"
            )
            return

        player = self.get_player(player_id)
        if not player:
            return

        # In case that the shooter mistakenly sends die when he is shooting
        if not force_death and player.state == PlayerState.WITH_BULLET:
            logging.warning(f"Player {player_id} tried to die with bullet. IGNORING")
            return

        if not self.decision.decision:
            logging.warning(
                f"Player {player_id} tried to die without shot being shot. IGNORING"
            )
            return

        logging.info(f"Player {player_id} died!")

        player.state = PlayerState.DEAD
        self.players_remaining.remove(player)
        if self.any_died._value == 0:
            self.any_died.release()

    async def player_move(self, player_id: str):
        if not self.gamestate == MOVING:
            logging.error(
                f"Player {player_id} tried to move in gamestate {self.gamestate.value()}"
            )
            return

        player = self.get_player(player_id)
        if not player:
            logging.error(f"Player {player_id} not found")
            return

        player.has_moved = True
        await self.state_check()

    async def player_shoot(self, player_id: str, is_shoot: bool):
        if not self.gamestate == SHOOTING:
            logging.error(
                f"Player {player_id} tried to shoot in gamestate {self.gamestate}"
            )
            return

        player = self.get_player(player_id)
        if not player:
            logging.error(f"Player {player_id} not found")
            return
        if not player.state == PlayerState.WITH_BULLET:
            logging.error(f"Player {player_id} tried to shoot in state {player.state}")
            return

        self.decision.decision = is_shoot
        self.decision.decided.release()
