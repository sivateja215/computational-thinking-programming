def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    return result + left[i:] + right[j:]


n = int(input("Enter number of elements: "))
arr = list(map(int, input("Enter elements: ").split()))

if len(arr) != n:
    print("Invalid input")
else:
    print("Original array:", arr)
    print("Sorted array:", merge_sort(arr))
    print("Time Complexity: O(n log n)")
    print("Space Complexity: O(n)")