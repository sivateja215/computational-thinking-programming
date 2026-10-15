import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# --------------------------------------------------
# 1. ASYNCIO - For asynchronous I/O-bound tasks
# --------------------------------------------------

async def async_task(task_id):
    print(f"Async task {task_id} started")

    # Simulates network I/O
    await asyncio.sleep(2)

    print(f"Async task {task_id} completed")
    return f"Async result {task_id}"


async def run_asyncio():
    print("\n--- ASYNCIO ---")

    start = time.perf_counter()

    results = await asyncio.gather(
        async_task(1),
        async_task(2),
        async_task(3)
    )

    end = time.perf_counter()

    print("Results:", results)
    print(f"Time: {end - start:.2f} seconds")


# --------------------------------------------------
# 2. THREADS - For blocking I/O-bound tasks
# --------------------------------------------------

def blocking_task(task_id):
    print(f"Thread task {task_id} started")

    # Simulates blocking I/O
    time.sleep(2)

    print(f"Thread task {task_id} completed")
    return f"Thread result {task_id}"


def run_threads():
    print("\n--- THREADS ---")

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=3) as executor:

        results = list(
            executor.map(blocking_task, [1, 2, 3])
        )

    end = time.perf_counter()

    print("Results:", results)
    print(f"Time: {end - start:.2f} seconds")


# --------------------------------------------------
# 3. PROCESSES - For CPU-bound tasks
# --------------------------------------------------

def cpu_task(number):
    total = 0

    for i in range(10_000_000):
        total += i * number

    return total


def run_processes():
    print("\n--- PROCESSES ---")

    start = time.perf_counter()

    with ProcessPoolExecutor() as executor:

        results = list(
            executor.map(cpu_task, [1, 2, 3])
        )

    end = time.perf_counter()

    print("Results:", results)
    print(f"Time: {end - start:.2f} seconds")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    asyncio.run(run_asyncio())

    run_threads()

    run_processes()
