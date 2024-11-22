import sys
from dataclasses import dataclass, field
from random import choice, randint

from typing import List, Set, Union

import logging

from game.types import Player, GameState
from game.callbacks import Callbacks
from game.states import PlayerState, JOINING, MOVING, SHOOTING, ENDING

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@dataclass
class GameLobby:
    gamestate: GameState = JOINING
    player_ids: Set[str] = field(default_factory=set)
    players: Set[Player] = field(default_factory=set)
    players_remaining: List[Player] = field(default_factory=list)
    players_max: int = 1
    no_shoot_penalty: float = 0.33

    callbacks: Callbacks = None

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
            return

        player = self.get_player(player_id, create=True)
        player.ready_meeple = True
        await self.state_check()

    async def add_base(self, player_id: str):
        if not self.gamestate == JOINING:
            return
        player = self.get_player(player_id, create=True)
        player.ready_base = True
        await self.state_check()

    def get_random_player(self):
        return choice(self.players_remaining)

    def reset(self):
        for player in self.players:
            player.has_moved = False
            player.state = PlayerState.IDLE
        self.players_remaining = self.players.copy()

    async def player_die(self, player_id: str):
        if not self.gamestate == SHOOTING:
            return

        player = self.get_player(player_id)
        if not player:
            return

        player.state = PlayerState.DEAD
        self.players_remaining.remove(player)
        await self.state_check()

    async def player_move(self, player_id: str):
        if not self.gamestate == MOVING:
            logging.error(
                f"Player {player_id} tried to move in gamestate {self.gamestate}"
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
            return

        player = self.get_player(player_id)
        if not player:
            return

        player.state = PlayerState.IDLE
        if not is_shoot:
            die = False
            if randint(0, 100) > self.no_shoot_penalty * 100:
                self.players_remaining.remove(player)
                die = True

            self.callbacks.notify_player_has_died(player.id, die)

        await self.state_check()
