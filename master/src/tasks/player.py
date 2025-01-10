import aiomqtt
import logging

from game.lobby import GameLobby, PlayerState

logger = logging.getLogger(__name__)

TOPIC = "players/+/actions/#"


async def _actions_moved(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} moved message {payload}")

    if game_lobby.get_player(player_id).state != PlayerState.MOVING:
        logger.info(f"Player {player_id} is not in MOVING state")
        return

    await game_lobby.player_move(player_id)


async def _actions_ready_meeple(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} ready meeple message {payload}")

    if payload:
        await game_lobby.add_meeple(player_id)
    else:
        player = game_lobby.get_player(player_id)
        if player:
            player.ready_meeple = False


async def _actions_ready_base(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} ready base message {payload}")

    if payload:
        await game_lobby.add_base(player_id)
    else:
        player = game_lobby.get_player(player_id)
        if player:
            player.ready_base = False


async def _listen(game_lobby: GameLobby, message: aiomqtt.Message):
    split_topic = str(message.topic).split("/")

    try:
        player_id = split_topic[1]
    except:
        logger.error(f"Player missing: {message.topic}")
        return

    subtopic = "/".join(split_topic[2:])

    if subtopic == "actions/move":
        await _actions_moved(game_lobby, player_id, message.payload)
    elif subtopic == "actions/ready/meeple":
        await _actions_ready_meeple(game_lobby, player_id, message.payload)
    elif subtopic == "actions/ready/base":
        await _actions_ready_base(game_lobby, player_id, message.payload)
    elif subtopic == "actions/die" or subtopic == "actions/shoot":
        logger.info(f"Player {player_id} tried to die or shoot")
    else:
        logger.error(f"Invalid topic {message.topic}")


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    while True:
        async with mqtt_client.messages() as messages:
            await mqtt_client.subscribe(TOPIC)

            logger.info(f"Subscribed to topic {TOPIC}")

            async for message in messages:
                await _listen(game_lobby, message)
