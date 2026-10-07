def calculate_total(prices: list[float]) -> float:
    return sum(prices)


def calculate_average(prices: list[float]) -> float:
    if not prices:
        return 0.0
    return calculate_total(prices) / len(prices)


prices = []
n = int(input("Enter number of items: "))

for _ in range(n):
    prices.append(float(input("Enter price: ")))

print("Total:", calculate_total(prices))
print("Average:", round(calculate_average(prices), 2))

assert calculate_total([100, 200, 300]) == 600
assert calculate_average([100, 200, 300]) == 200
print("All tests passed")