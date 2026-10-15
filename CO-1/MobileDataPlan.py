import torch  # Import PyTorch for tensor operations

# Store the cost of each mobile plan
cost = torch.tensor([200, 400, 500, 300])

# Store the benefit provided by each plan
benefit = torch.tensor([30, 60, 70, 40])

# Names of the available plans
plans = ["A", "B", "C", "D"]

# Maximum amount the customer can spend
budget = 1000

# DP array: dp[b] stores the maximum benefit possible with budget b
dp = torch.zeros(budget + 1)

# Stores the plan combination that gives the best benefit for each budget
selected = [[] for _ in range(budget + 1)]

# Process each mobile plan one by one
for i in range(4):

    # Traverse budget in reverse to ensure each plan is selected at most once
    for b in range(budget, cost[i] - 1, -1):

        # Calculate the benefit if the current plan is selected
        new_benefit = dp[b - cost[i]] + benefit[i]

        # Check whether selecting the current plan gives a better benefit
        if new_benefit > dp[b]:

            # Update the maximum benefit for this budget
            dp[b] = new_benefit

            # Store the selected plan combination
            selected[b] = selected[b - cost[i]] + [plans[i]]

# Display the optimal plan combination
print("Selected Plans:", selected[budget])

# Calculate and display the total cost of the selected plans
print("Total Cost:", sum(cost[plans.index(p)] for p in selected[budget]).item())

# Display the maximum achievable benefit
print("Maximum Benefit:", dp[budget].item())
