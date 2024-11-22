import aiomqtt
import logging

from typing import Set
from game.lobby import Player

logger = logging.getLogger(__name__)


class Callbacks:

    def __init__(self, mqtt_client: aiomqtt.Client):
        self.mqtt_client = mqtt_client

    async def _publish(self, topic: str, payload):
        logger.info(f"Publishing to {topic}: {payload}")
        await self.mqtt_client.publish(topic, payload)

    async def notify_game_state(self, new_state: str):
        await self._publish("state/stage", new_state)

    async def notify_player_moving_turn(self, player_id: str, payload):
        await self._publish(
            f"players/{player_id}/state/can_move",
            payload,
        )

    async def notify_player_won(self, player_id: str, payload):
        await self._publish(f"players/{player_id}/state/has_won", payload)

    async def notify_player_has_bullet(
        self,
        remaining_players: Set[Player],
        has_bullet_player_id: str,
    ):
        for player in remaining_players:
            await self._publish(
                f"players/{player.id}/state/has_bullet",
                has_bullet_player_id == player.id,
            )

    async def notify_player_has_died(self, player_id: str, payload):
        await self._publish(f"player/{player_id}/state/has_died", payload)
