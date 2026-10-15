class DataStore[T]:

    def __init__(self):
        self.data: list[T] = []

    def add(self, item: T) -> None:
        self.data.append(item)

    def get_all(self) -> list[T]:
        return self.data


numbers = DataStore[int]()

numbers.add(10)
numbers.add(20)
numbers.add(30)

print(numbers.get_all())


names = DataStore[str]()

names.add("Rahul")
names.add("Priya")

print(names.get_all())
