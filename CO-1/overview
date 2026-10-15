# computationalthinkingandprogrammingpy
Analysing and Problem Solving

# Dynamic Programming Problem
1.Problem Statement - Mobile Data Plan Optimization using Dynamic Programming

A customer has multiple mobile data plans. Each plan has a cost and a corresponding benefit. The customer has a fixed budget and wants to select a combination of plans that provides the maximum total benefit without exceeding the budget.

**Question:** Would Dynamic Programming be suitable? Explain why.
## Scenario

We have:

* Multiple mobile plans.
* Each plan has a different **cost**.
* Each plan provides a different **benefit**.
* The customer has a **fixed budget**.
* We need to select plans that give the **maximum benefit** without exceeding the budget.

This is similar to the **0/1 Knapsack Problem**, where each plan can either be selected or not selected.

## Example

| Plan | Cost | Benefit |
| ---- | ---- | ------- |
| A    | ₹200 | 30      |
| B    | ₹400 | 60      |
| C    | ₹500 | 70      |
| D    | ₹300 | 40      |

**Budget = ₹1000**

Possible combinations include:

* A + B + D → Cost = ₹900, Benefit = 130
* B + C → Cost = ₹900, Benefit = 130
**A + C + D → Cost = ₹1000, Benefit = 140**

Therefore:

**Optimal Combination = A + C + D**

**Maximum Benefit = 140**


## Algorithm

1. Store the cost and benefit of each plan.
2. Create a DP array of size `budget + 1`.
3. Initialize all DP values to `0`.
4. Process each plan one by one.
5. Traverse the budget in reverse order.
6. Calculate the benefit obtained by selecting the current plan.
7. If the new benefit is greater than the existing benefit, update the DP value.
8. After processing all plans, `dp[budget]` contains the maximum benefit.
9. Track the selected plans to display the optimal combination.


## Code

**python**
import torch

# Store the cost of each mobile plan
cost = torch.tensor([200, 400, 500, 300])

# Store the benefit of each mobile plan
benefit = torch.tensor([30, 60, 70, 40])

# Store the names of the plans
plans = ["A", "B", "C", "D"]

# Set the maximum available budget
budget = 1000

# Create DP array to store maximum benefit for each budget
dp = torch.zeros(budget + 1)

# Store the selected plans for each budget
selected = [[] for _ in range(budget + 1)]

# Process each mobile plan
for i in range(4):
    #Traverse budget in reverse to select each plan only once
    for b in range(budget, cost[i] - 1, -1):
        # Calculate benefit if the current plan is selected
        new_benefit = dp[b - cost[i]] + benefit[i]
        # Update if the new benefit is better
        if new_benefit > dp[b]:
            # Store the new maximum benefit
            dp[b] = new_benefit
            # Store the selected plan combination
            selected[b] = selected[b - cost[i]] + [plans[i]]

# Display the optimal plan combination
print("Selected Plans:", selected[budget])

# Calculate and display the total cost
print("Total Cost:",
      sum(cost[plans.index(p)] for p in selected[budget]).item())

# Display the maximum benefit
print("Maximum Benefit:", dp[budget].item())


## Output

Selected Plans: ['A', 'C', 'D']
Total Cost: 1000
Maximum Benefit: 140


## Time Complexity

Let:

* `n` = number of plans
* `B` = available budget

The outer loop runs `n` times and the inner loop runs up to `B` times.
O(n × B) --> O(nB)


For this example:
n = 4
B = 1000

O(4 × 1000) = O(4000)


Technologies Used
Python
PyTorch
Dynamic Programming

Output:
Selected Plans: ['A', 'C', 'D']
Total Cost: 1000
Maximum Benefit: 140

//** 1st Problem explanation completed **//
