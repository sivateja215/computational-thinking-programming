from concurrent.futures import ThreadPoolExecutor
import time

def task(x):
    time.sleep(2)
    return x * x

with ThreadPoolExecutor(max_workers=3) as executor:

    future1 = executor.submit(task, 5)
    future2 = executor.submit(task, 10)
    future3 = executor.submit(task, 20)

    print("Tasks submitted")

    print(future1.result())
    print(future2.result())
    print(future3.result())
