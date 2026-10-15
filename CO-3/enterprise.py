from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(Generic[T]):

    def __init__(self):
        self.items: list[T] = []

    def add(self, item: T) -> None:
        self.items.append(item)

    def get_all(self) -> list[T]:
        return self.items


class Customer:
    def __init__(self, name):
        self.name = name


class Product:
    def __init__(self, name):
        self.name = name


class Employee:
    def __init__(self, name):
        self.name = name


customer_repo = Repository[Customer]()
product_repo = Repository[Product]()
employee_repo = Repository[Employee]()

customer_repo.add(Customer("Rahul"))
product_repo.add(Product("Laptop"))
employee_repo.add(Employee("Priya"))

print(customer_repo.get_all()[0].name)
print(product_repo.get_all()[0].name)
print(employee_repo.get_all()[0].name)
