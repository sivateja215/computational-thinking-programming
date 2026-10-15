class Customer:
    def __init__(self, name: str, contact: str | int):
        self.name = name
        self.contact = contact

    def display(self) -> None:
        print("Customer:", self.name)
        print("Contact:", self.contact)


c1 = Customer("Rahul", "rahul@gmail.com")
c2 = Customer("Priya", 9876543210)

c1.display()
c2.display()
