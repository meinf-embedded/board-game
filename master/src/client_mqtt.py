import asyncio
import logging
import signal
import sys

import aiomqtt

from os import environ


def init_logging():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def init_signal_handler():
    def signal_handler(sig, _):
        logging.info(f"Received signal {sig}, exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


MQTT_BROKER_HOST = str(environ.get("MQTT_BROKER_HOST", "localhost"))
MQTT_BROKER_PORT = int(environ.get("MQTT_BROKER_PORT", 1883))

USERNAME = str(environ.get("MASTER_USERNAME"))
PASSWORD = str(environ.get("MASTER_PASSWORD"))


async def main():

    while True:
        try:
            async with aiomqtt.Client(
                MQTT_BROKER_HOST,
                MQTT_BROKER_PORT,
                # TODO: Add username and password to the MQTT client
            ) as mqtt_client:
                await mqtt_client.connect()

                print("Connected to MQTT broker")

                while True:
                    await asyncio.sleep(1)
        except aiomqtt.MqttError as e:
            logging.info("MQTT connection error, reconnecting...")
            logging.error(e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
