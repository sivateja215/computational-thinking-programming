def calculate_average(marks: list[int]) -> float:
    return sum(marks) / len(marks)

def main() -> None:
    n = int(input("Enter number of subjects: "))
    marks = []
    for _ in range(n):
        marks.append(int(input("Enter marks: ")))

    average = calculate_average(marks)
    print("Average:", round(average, 2))

if __name__ == "__main__":
    main()