from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class Stack(Generic[T]):
    items: list[T] = field(default_factory=list)

    def push(self, item: T):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

@dataclass
class Queue(Generic[T]):
    items: list[T] = field(default_factory=list)

    def enqueue(self, item: T):
        self.items.append(item)

    def dequeue(self):
        return self.items.pop(0)

s = Stack[int]()
n = int(input("Enter number of stack elements: "))
for _ in range(n):
    s.push(int(input("Enter element: ")))

q = Queue[int]()
m = int(input("Enter number of queue elements: "))
for _ in range(m):
    q.enqueue(int(input("Enter element: ")))

print("Stack:", s.items)
print("Popped:", s.pop())
print("Queue:", q.items)
print("Dequeued:", q.dequeue())