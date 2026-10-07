def calculate_discount(price: float, discount: float) -> float:
    return price - (price * discount / 100)


def main() -> None:
    price = float(input("Enter price: "))
    discount = float(input("Enter discount: "))

    result = calculate_discount(price, discount)
    print("Final Price:", round(result, 2))


assert calculate_discount(1000, 10) == 900
assert calculate_discount(500, 20) == 400

if __name__ == "__main__":
    main()