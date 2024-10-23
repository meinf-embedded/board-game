import aiomqtt
from game.lobby import GameLobby

import logging

TOPIC = "lobby/"  # placeholder
logger = logging.getLogger(__name__)


def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    logger.info("Received message", message)


async def listen(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    while True:
        async with mqtt_client.messages() as messages:
            await mqtt_client.subscribe(TOPIC)

            print(
                "Subscribed to topic", TOPIC
            )  # Use logger instead of print and make logging work on docker

            async for message in messages:
                _listen(game_lobby, message)
