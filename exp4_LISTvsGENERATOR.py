import time
import tracemalloc

n = int(input("Enter dataset size: "))

def measure(method):
    tracemalloc.start()
    start = time.perf_counter()
    result = method()
    time_taken = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, time_taken, peak / 1024 / 1024

lst, lt, lm = measure(lambda: [x * x for x in range(n)])
gen, gt, gm = measure(lambda: sum(x * x for x in range(n)))

print("\nList Processing")
print("Time:", round(lt, 4), "seconds")
print("Memory:", round(lm, 2), "MB")

print("\nGenerator Processing")
print("Time:", round(gt, 4), "seconds")
print("Memory:", round(gm, 2), "MB")

print("\nList Result:", sum(lst))
print("Generator Result:", gen)