import aiomqtt
import logging
import asyncio

from game.lobby import GameLobby, PlayerState

logger = logging.getLogger(__name__)


TOPIC = "players/+/actions/#"


async def _actions_shoot(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} shoot message {payload}")

    is_shoot = payload.decode("UTF-8") == "True"

    game_lobby.decision.decision = is_shoot
    await game_lobby.player_shoot(player_id, is_shoot)


async def _actions_die(game_lobby: GameLobby, player_id: str, payload):
    logger.info(
        f"Received player {player_id} die message {payload}, player state: {game_lobby.get_player(player_id).state}"
    )

    if payload:
        game_lobby.player_die(player_id)


async def _actions_moved(game_lobby: GameLobby, player_id: str, payload):
    logger.info(f"Received player {player_id} moved message {payload}")

    player = game_lobby.get_player(player_id)

    if not player:
        logger.error(f"Player {player_id} not found")
        return

    if player.state != PlayerState.MOVING:
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
        return asyncio.create_task(
            _actions_moved(game_lobby, player_id, message.payload)
        )
    elif message.topic.matches("players/+/actions/ready/meeple"):
        return asyncio.create_task(
            _actions_ready_meeple(game_lobby, player_id, message.payload)
        )
    elif message.topic.matches("players/+/actions/ready/base"):
        return asyncio.create_task(
            _actions_ready_base(game_lobby, player_id, message.payload)
        )
    elif message.topic.matches("players/+/actions/die"):
        return asyncio.create_task(_actions_die(game_lobby, player_id, message.payload))
    elif message.topic.matches("players/+/actions/shoot"):
        return asyncio.create_task(
            _actions_shoot(game_lobby, player_id, message.payload)
        )
    else:
        logger.error(f"Unknown subtopic {message.topic}")


async def run(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    async with mqtt_client.messages() as messages:
        await mqtt_client.subscribe(TOPIC)

        logger.info(f"Subscribed to topics: {TOPIC}")

        async for message in messages:
            asyncio.ensure_future(_listen(game_lobby, message))
