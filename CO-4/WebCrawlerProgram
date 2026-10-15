import asyncio
import random

async def download(url):
    print("Downloading:", url)

    await asyncio.sleep(random.uniform(1, 3))

    print("Finished:", url)
    return url


async def main():
    urls = [
        "site1.com",
        "site2.com",
        "site3.com",
        "site4.com",
        "site5.com"
    ]

    tasks = [download(url) for url in urls]

    results = await asyncio.gather(*tasks)

    print("Completed:", results)


asyncio.run(main())
