import asyncio
import logging
import signal
import sys

import aiomqtt

from game.lobby import GameLobby
from game.callbacks import Callbacks

from os import environ

from tasks import player, decision

# MQTT settings
MQTT_BROKER_HOST = str(environ.get("MQTT_BROKER_HOST", "localhost"))
MQTT_BROKER_PORT = int(environ.get("MQTT_BROKER_PORT", 1883))
RECONNECT_DELAY = int(environ.get("RECONNECT_DELAY", 5))
USERNAME = str(environ.get("USERNAME"))
PASSWORD = str(environ.get("PASSWORD"))

# Game settings
MAX_PLAYERS = int(environ.get("MAX_PLAYERS", 2))


def init_logging():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def init_signal_handler():
    def signal_handler(sig, _):
        logging.info(f"Received signal {sig}, exiting gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_tasks(mqtt_client: aiomqtt.Client, game_lobby: GameLobby):
    async with asyncio.TaskGroup() as tg:
        tg.create_task(player.run(mqtt_client, game_lobby))
        tg.create_task(decision.run(mqtt_client, game_lobby))


async def main():

    init_logging()

    mqtt_client = aiomqtt.Client(
        MQTT_BROKER_HOST,
        port=MQTT_BROKER_PORT,
        username=USERNAME,
        password=PASSWORD,
        clean_session=True,
    )

    game_lobby = GameLobby(
        players_max=MAX_PLAYERS,
        callbacks=Callbacks(mqtt_client),
    )

    while True:
        try:
            async with mqtt_client:
                logging.info(f"Connected to MQTT broker")
                await run_tasks(mqtt_client, game_lobby)
        except aiomqtt.MqttError as e:
            logging.info("MQTT connection error, reconnecting...")
            logging.error(e)
            await asyncio.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    asyncio.run(main())
