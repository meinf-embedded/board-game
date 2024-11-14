import aiomqtt

from typing import Set
from game.lobby import Player


class Callbacks:

    def __init__(self, mqtt_client: aiomqtt.Client):
        self.mqtt_client = mqtt_client

    async def notify_game_state(self, new_state: str):
        await self.mqtt_client.publish("state/stage", new_state)

    async def notify_player_moving_turn(self, player_id: str):
        await self.mqtt_client.publish(f"player/{player_id}/actions/move", 1)

    async def notify_player_has_bullet(
        self,
        remaining_players: Set[Player],
        has_bullet_player_id: str,
    ):
        async for player in remaining_players:
            await self.mqtt_client.publish(
                f"player/{player.id}/state/has_bullet",
                has_bullet_player_id == player.id,
            )

    async def notify_player_has_died(self, player_id: str):
        # TODO: Notify player has died topic
        await self.mqtt_client.publish(f"player/{player_id}/state/dead", 1)
