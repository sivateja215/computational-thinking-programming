import asyncio
import time
import aiohttp


async def fetch(session, url):
    for _ in range(3):
        try:
            async with session.get(url, timeout=10) as response:
                return response.status
        except Exception:
            await asyncio.sleep(1)

    return "Failed"


async def sequential_crawl(urls):
    results = []

    async with aiohttp.ClientSession() as session:
        for url in urls:
            results.append(await fetch(session, url))

    return results


async def concurrent_crawl(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)


urls = input("Enter URLs separated by space: ").split()

# Sequential execution
start = time.perf_counter()
sequential = asyncio.run(sequential_crawl(urls))
seq_time = time.perf_counter() - start

# Asynchronous concurrent execution
start = time.perf_counter()
async_results = asyncio.run(concurrent_crawl(urls))
async_time = time.perf_counter() - start

print("\nSequential:", sequential)
print("Asynchronous:", async_results)

print("\nSequential Time:", round(seq_time, 2), "seconds")
print("Async Time:", round(async_time, 2), "seconds")