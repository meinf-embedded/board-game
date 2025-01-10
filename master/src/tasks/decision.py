import logging
import aiomqtt

from game.lobby import GameLobby

logger = logging.getLogger(__name__)

TOPIC = "players/+/actions/#"


async def _actions_die(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} die message {payload}")

    if bool(payload):
        await game_lobby.player_die(player_id)


async def _actions_shoot(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} shoot message {payload}")

    is_shoot = payload.decode("UTF-8") == "True"

    game_lobby.decision.decision = is_shoot
    await game_lobby.player_shoot(player_id, is_shoot)


async def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    split_topic = str(message.topic).split("/")

    if split_topic[-1] not in ["shoot", "die"]:
        return

    try:
        player_id = split_topic[1]
    except:
        logger.error(f"Player missing: {message.topic}")
        return

    if split_topic[-1] == "die":
        await _actions_die(game_lobby, player_id, message.payload)
    elif split_topic[-1] == "shoot":
        await _actions_shoot(game_lobby, player_id, message.payload)


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    while True:
        async with mqtt_client.messages() as messages:
            await mqtt_client.subscribe(TOPIC)

            logger.info(f"Subscribed to topic {TOPIC}")

            async for message in messages:
                await _listen(game_lobby, message)
