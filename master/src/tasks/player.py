import aiomqtt
import logging
import json

from game.lobby import GameLobby, PlayerState, GameState

logger = logging.getLogger(__name__)

TOPIC = "players/#"


def _actions_die(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} die message {payload}")

    payload = json.loads(payload)
    game_lobby.player_die(payload)


def _actions_shoot(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} shoot message {payload}")

    if game_lobby.gamestate != GameState.SHOOTING:
        logger.info(f"Game is not in SHOOTING state")
        return

    if game_lobby.get_player(player_id).state != PlayerState.SHOOTING:
        logger.info(f"Player {player_id} is not in SHOOTING state")
        return

    game_lobby.player_shoot(player_id, bool(payload))


def _actions_moved(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} moved message {payload}")

    if game_lobby.get_player(player_id).state != PlayerState.MOVING:
        logger.info(f"Player {player_id} is not in MOVING state")
        return

    game_lobby.player_move(player_id)


def _actions_ready_meeple(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received {player_id} join message {payload}")

    if payload:
        game_lobby.add_meeple(player_id)
    else:
        player = game_lobby.get_player(player_id)
        if player:
            player.ready_meeple = False


def _actions_ready_base(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} join message {payload}")

    if payload:
        game_lobby.add_base(player_id)
    else:
        player = game_lobby.get_player(player_id)
        if player:
            player.ready_base = False


def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    split_topic = message.topic.split("/")

    try:
        player_id = split_topic[1]
    except:
        logger.error(f"Player missing: {message.topic}")
        return

    subtopic = "/".join(split_topic[2:])

    if subtopic == "actions/moved":
        _actions_moved(game_lobby, player_id, message.payload)
    elif subtopic == "actions/shoot":
        _actions_shoot(game_lobby, player_id, message.payload)
    elif subtopic == "actions/die":
        _actions_die(game_lobby, player_id, message.payload)
    elif subtopic == "actions/ready/meeple":
        _actions_ready_meeple(game_lobby, player_id, message.payload)
    elif subtopic == "actions/ready/base":
        _actions_ready_base(game_lobby, player_id, message.payload)
    else:
        logger.error(f"Invalid topic {message.topic}")


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    while True:
        async with mqtt_client.messages() as messages:
            await mqtt_client.subscribe(TOPIC)

            logger.info(f"Subscribed to topic {TOPIC}")

            async for message in messages:
                _listen(game_lobby, message)
