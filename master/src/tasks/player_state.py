import aiomqtt
import logging
import json

from game.types import GameLobby

TOPIC = "lobby/#"  # placeholder
logger = logging.getLogger(__name__)


def _actions_ready_meeple(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received {player_id} join message {payload}")

    payload = json.loads(payload)
    game_lobby.add_player(payload)


def _actions_ready_base(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} join message {payload}")

    payload = json.loads(payload)
    game_lobby.add_player(payload)


def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    split_topic = message.topic.split("/")

    try:
        player_id = split_topic[1]
    except:
        logger.error(f"Invalid topic {message.topic}")
        return

    subtopic = "/".join(split_topic[2:])

    if subtopic == "actions/ready/meeple":
        _actions_ready_meeple(game_lobby, player_id, message.payload)
    elif subtopic == "actions/ready/base":
        _actions_ready_base(game_lobby, player_id, message.payload)
    elif subtopic == "actions/die":
        ...
    elif subtopic == "actions/shoot":
        ...
    elif subtopic == "actions/moved":
        ...
    elif subtopic == "state/moved":
        ...


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    while True:
        async with mqtt_client.messages() as messages:
            await mqtt_client.subscribe(TOPIC)

            logger.info(f"Subscribed to topic {TOPIC}")

            async for message in messages:
                _listen(game_lobby, message)
                # Inform game state to every player
                await mqtt_client.publish("state/stage", game_lobby.gamestate.value)
