import asyncio
import random

async def sensor():

    for i in range(5):

        await asyncio.sleep(1)

        temperature = random.randint(20, 35)

        yield temperature


async def main():

    async for temperature in sensor():

        print("Temperature:", temperature)


asyncio.run(main())
