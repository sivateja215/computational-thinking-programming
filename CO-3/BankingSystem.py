def process_transaction(
    account_id: str,
    amount: float,
    transaction_type: str
) -> bool:

    if amount > 0:
        print(f"Transaction: {transaction_type}")
        print(f"Account: {account_id}")
        print(f"Amount: ₹{amount}")
        return True

    return False


result = process_transaction("ACC101", 5000.0, "Deposit")

print("Success:", result)
