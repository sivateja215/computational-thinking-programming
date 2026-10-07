# Computational Thinking and Programming - Lab Exam

## Experiment: List-Based vs Generator-Based Processing

### 1. Problem Statement

An e-commerce company has millions of transaction records.
It needs to identify transactions above ₹10,000 for further analysis.

The task is to implement the processing in two ways:

1. List-based processing
2. Generator-based processing

The execution time, memory usage, and number of records processed are compared.

---

## 2. Objective

The objective is to understand the difference between eager and lazy evaluation.

The program measures:
- Execution time using `time.perf_counter()`
- Memory usage using `tracemalloc`
- Number of transactions above ₹10,000

---

## 3. Approach

### List-Based Approach

All transactions are checked and the transactions above ₹10,000 are stored in a new list.

Example:

    Transactions:
    8000, 15000, 12000, 5000, 20000

    Filtered List:
    15000, 12000, 20000

This is called eager evaluation because the results are generated and stored immediately.

### Generator-Based Approach

A generator checks transactions one at a time and produces only the transactions that satisfy the condition.

It uses the `yield` keyword and does not create a complete filtered list.

This is called lazy evaluation because values are produced only when required.

---

## 4. Python Concepts Used

### List Comprehension

    result = [x for x in transactions if x > 10000]

It creates and stores all matching transactions in a list.

### Generator

    def filter_transactions(data):
        for x in data:
            if x > 10000:
                yield x

The `yield` statement makes the function a generator.

### time.perf_counter()

Used to measure the execution time of each approach.

### tracemalloc

Used to measure memory allocated during processing.

---

## 5. Time Complexity

For both approaches, every transaction needs to be checked.

Time Complexity: O(n)

where `n` is the number of transactions.

---

## 6. Space Complexity

### List-Based

The filtered transactions are stored in a new list.

Additional Space Complexity: O(k)

where `k` is the number of transactions above ₹10,000.

### Generator-Based

The generator produces one value at a time.

Additional Space Complexity: O(1), excluding the original input list.

Note: The program stores the original transactions in a list, so the overall program still requires O(n) memory for the input.

---

## 7. Sample Input

    Enter number of transactions: 5
    8000
    15000
    12000
    5000
    20000

---

## 8. Sample Output

    List: records = 3
    Generator: records = 3

Both approaches correctly identify three transactions above ₹10,000.

---

## 9. Actual Observation

In one execution:

    List: records = 3
    time = 0.000431 seconds
    memory = 0.08 KB

    Generator: records = 3
    time = 0.000018 seconds
    memory = 0.97 KB

The exact time and memory values may vary depending on the system and dataset size.

---

## 10. Why Generator Is Useful

For millions of transactions, storing all filtered results in a list can require significant additional memory.

A generator processes values one at a time, making it suitable for large datasets and streaming data.

---

## 11. Eager vs Lazy Evaluation

### Eager Evaluation

The complete operation is performed immediately and results are stored.

Example: List

### Lazy Evaluation

Values are generated only when they are requested.

Example: Generator

---

## 12. Result / Conclusion

Both approaches successfully identify transactions above ₹10,000.

The list approach stores all matching records, while the generator processes them one at a time.

Generator-based processing is generally more memory-efficient for large datasets.

---

# Viva Questions

### 1. What is eager evaluation?

Eager evaluation processes the data immediately and stores the results.
It may require more memory when the dataset is large.
Lists use eager evaluation.

### 2. What is lazy evaluation?

Lazy evaluation delays processing until a value is required.
It avoids storing all results at the same time.
Generators use lazy evaluation.

### 3. What is a generator?

A generator produces values one at a time instead of returning all values together.
It is created using the `yield` keyword.
Generators are useful for large datasets.

### 4. What is the use of `yield`?

`yield` produces a value from a generator.
It pauses the function and preserves its current state.
The function continues when the next value is requested.

### 5. Why is `time.perf_counter()` used?

`time.perf_counter()` measures execution time with high resolution.
It is useful for performance comparisons.
Here it compares list and generator processing time.
