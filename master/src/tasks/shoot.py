import logging
import aiomqtt
import asyncio

from game.lobby import GameLobby

logger = logging.getLogger(__name__)

TOPIC = "players/+/actions/shoot"


async def _actions_shoot(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} shoot message {payload}")

    is_shoot = payload.decode("UTF-8") == "True"

    game_lobby.decision.decision = is_shoot
    await game_lobby.player_shoot(player_id, is_shoot)


async def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    try:
        player_id = str(message.topic).split("/")[1]
    except:
        logger.error(f"Player missing: {message.topic}")
        return

    if message.topic.matches("players/+/actions/shoot"):
        await asyncio.create_task(
            _actions_shoot(game_lobby, player_id, message.payload)
        )


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    async with mqtt_client.messages() as messages:
        await mqtt_client.subscribe(TOPIC)

        logger.info(f"Subscribed to topics: {TOPIC}")

        async for message in messages:
            asyncio.ensure_future(_listen(game_lobby, message))
