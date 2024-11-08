import aiomqtt
import asyncio

from logging import getLogger

logger = getLogger(__name__)


async def run(mqtt_client: aiomqtt.Client):
    counter = 0
    while True:
        counter += 1
        logger.info(f"Publishing hello world {counter}...")
        await mqtt_client.publish(
            topic="hello-world/",
            payload=f"Hello, world {counter}!",
        )
        await asyncio.sleep(5)
