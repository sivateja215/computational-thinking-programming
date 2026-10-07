import time
import tracemalloc

n = int(input("Enter number of transactions: "))
transactions = [float(input()) for _ in range(n)]

tracemalloc.start()
start = time.perf_counter()
result = [x for x in transactions if x > 10000]
list_time = time.perf_counter() - start
_, list_memory = tracemalloc.get_traced_memory()
tracemalloc.stop()

def filter_transactions(data):
    for x in data:
        if x > 10000:
            yield x

tracemalloc.start()
start = time.perf_counter()
result_gen = filter_transactions(transactions)
count = sum(1 for _ in result_gen)
gen_time = time.perf_counter() - start
_, gen_memory = tracemalloc.get_traced_memory()
tracemalloc.stop()

print("List: records =", len(result), "time =", round(list_time, 6),
      "memory =", round(list_memory / 1024, 2), "KB")
print("Generator: records =", count, "time =", round(gen_time, 6),
      "memory =", round(gen_memory / 1024, 2), "KB")