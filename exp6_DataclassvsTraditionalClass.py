from dataclasses import dataclass

class Student:
    def __init__(self, name: str, roll: int, cgpa: float):
        self.name = name
        self.roll = roll
        self.cgpa = cgpa

@dataclass
class DataStudent:
    name: str
    roll: int
    cgpa: float

name = input("Enter student name: ")
roll = int(input("Enter roll number: "))
cgpa = float(input("Enter CGPA: "))

traditional = Student(name, roll, cgpa)
dataclass = DataStudent(name, roll, cgpa)

print("\nTraditional Class:")
print(traditional.__dict__)

print("\nDataclass:")
print(dataclass)

print("\nObjects Equal:", dataclass == DataStudent(name, roll, cgpa))