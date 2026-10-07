from typing import List

def total_marks(marks: List[int]) -> int:
    return sum(marks)

def main() -> None:
    n = int(input("Enter number of subjects: "))
    marks = []
    for _ in range(n):
        marks.append(int(input("Enter marks: ")))
    print("Total Marks:", total_marks(marks))

if __name__ == "__main__":
    main()