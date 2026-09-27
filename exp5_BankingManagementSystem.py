from abc import ABC, abstractmethod

class Account(ABC):
    def __init__(self, number: str, balance: float):
        self.number = number
        self.balance = balance

    def deposit(self, amount: float) -> None:
        self.balance += amount

    @abstractmethod
    def withdraw(self, amount: float) -> bool:
        pass

class SavingsAccount(Account):
    def withdraw(self, amount: float) -> bool:
        if 0 < amount <= self.balance:
            self.balance -= amount
            return True
        return False

class CurrentAccount(Account):
    def withdraw(self, amount: float) -> bool:
        if 0 < amount <= self.balance + 1000:
            self.balance -= amount
            return True
        return False

account_type = input("Enter account type (savings/current): ").lower()
number = input("Enter account number: ")
balance = float(input("Enter initial balance: "))
deposit = float(input("Enter deposit amount: "))
withdraw = float(input("Enter withdrawal amount: "))

account: Account = (
    SavingsAccount(number, balance)
    if account_type == "savings"
    else CurrentAccount(number, balance)
)

account.deposit(deposit)
print("Withdrawal successful:", account.withdraw(withdraw))
print("Account Number:", account.number)
print("Final Balance:", account.balance)