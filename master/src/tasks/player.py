import aiomqtt
import logging
import asyncio

from game.lobby import GameLobby, PlayerState

logger = logging.getLogger(__name__)

TOPICS = [
    f"players/+/actions/{action}" for action in ["move", "ready/meeple", "ready/base"]
]


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
    try:
        player_id = str(message.topic).split("/")[1]
    except:
        logger.error(f"Player missing: {message.topic}")
        return

    if message.topic.matches("players/+/actions/move"):
        await asyncio.create_task(
            _actions_moved(game_lobby, player_id, message.payload)
        )
    elif message.topic.matches("players/+/actions/ready/meeple"):
        await asyncio.create_task(
            _actions_ready_meeple(game_lobby, player_id, message.payload)
        )
    elif message.topic.matches("players/+/actions/ready/base"):
        await asyncio.create_task(
            _actions_ready_base(game_lobby, player_id, message.payload)
        )
    else:
        logger.error(f"Unknown subtopic {message.topic}")


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    async with mqtt_client.messages() as messages:
        for topic in TOPICS:
            await mqtt_client.subscribe(topic)

        logger.info(f"Subscribed to topics: {TOPICS}")

        async for message in messages:
            asyncio.ensure_future(_listen(game_lobby, message))
