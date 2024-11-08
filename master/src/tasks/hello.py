import aiomqtt
import asyncio


async def run(mqtt_client: aiomqtt.Client):
    counter = 0
    while True:
        counter += 1
        print(f"Publishing hello world {counter}...")
        await mqtt_client.publish(
            topic="hello-world/",
            payload=f"Hello, world {counter}!",
        )
        await asyncio.sleep(5)
