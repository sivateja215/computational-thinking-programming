import threading
from queue import Queue

q = Queue()
n = int(input("Enter number of items: "))

def producer():
    for i in range(1, n + 1):
        q.put(i)
        print("Produced:", i)

def consumer():
    for _ in range(n):
        item = q.get()
        print("Consumed:", item)
        q.task_done()

p = threading.Thread(target=producer)
c = threading.Thread(target=consumer)

p.start()
c.start()

p.join()
c.join()

print("Producer-Consumer completed successfully")