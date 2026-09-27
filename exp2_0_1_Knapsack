def knapsack(w, v, W):
    dp = [0] * (W + 1)
    for wt, val in zip(w, v):
        for j in range(W, wt - 1, -1):
            dp[j] = max(dp[j], dp[j - wt] + val)
    return dp[W]

n = int(input("Enter number of items: "))
w = list(map(int, input("Enter weights: ").split()))
v = list(map(int, input("Enter values: ").split()))
W = int(input("Enter capacity: "))

print("Maximum value:", knapsack(w, v, W))
print("Time Complexity: O(nW)")
print("Space Complexity: O(W)")