#!/usr/bin/env python3
"""
Student Finance Manager
Simple CLI app to track incomes/expenses per student, with JSON persistence.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional

DATA_FILE = "students_finance.json"
DATE_FMT = "%Y-%m-%d"  # ISO-like date format


@dataclass
class Transaction:
    ttype: str        # "income" or "expense"
    amount: float
    description: str
    date: str         # YYYY-MM-DD

    def to_dict(self):
        return asdict(self)


@dataclass
class Student:
    student_id: str
    name: str
    transactions: List[Transaction]

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "name": self.name,
            "transactions": [t.to_dict() for t in self.transactions]
        }

    def balance(self) -> float:
        bal = 0.0
        for t in self.transactions:
            if t.ttype == "income":
                bal += t.amount
            else:
                bal -= t.amount
        return bal


class FinanceManager:
    def __init__(self):
        self.students: Dict[str, Student] = {}

    # Student management
    def add_student(self, student_id: str, name: str) -> bool:
        if student_id in self.students:
            return False
        self.students[student_id] = Student(student_id=student_id, name=name, transactions=[])
        return True

    def remove_student(self, student_id: str) -> bool:
        return (self.students.pop(student_id, None) is not None)

    def find_student(self, student_id: str) -> Optional[Student]:
        return self.students.get(student_id)

    # Transactions
    def record_transaction(self, student_id: str, ttype: str, amount: float, description: str, date: Optional[str] = None) -> bool:
        student = self.find_student(student_id)
        if not student:
            return False
        if ttype not in ("income", "expense"):
            return False
        if date is None:
            date = datetime.now().strftime(DATE_FMT)
        tx = Transaction(ttype=ttype, amount=round(amount, 2), description=description, date=date)
        student.transactions.append(tx)
        return True

    # Reports
    def student_report(self, student_id: str) -> Optional[Dict]:
        student = self.find_student(student_id)
        if not student:
            return None
        return {
            "student_id": student.student_id,
            "name": student.name,
            "balance": round(student.balance(), 2),
            "transactions": [t.to_dict() for t in student.transactions]
        }

    def all_students_summary(self) -> List[Dict]:
        out = []
        for s in self.students.values():
            out.append({
                "student_id": s.student_id,
                "name": s.name,
                "balance": round(s.balance(), 2),
                "num_transactions": len(s.transactions)
            })
        return out

    # Persistence
    def save(self, filename: str = DATA_FILE) -> None:
        data = {"students": [s.to_dict() for s in self.students.values()]}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved data to {filename}.")

    def load(self, filename: str = DATA_FILE) -> bool:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.students = {}
            for s in data.get("students", []):
                transactions = [Transaction(**t) for t in s.get("transactions", [])]
                student = Student(student_id=s["student_id"], name=s["name"], transactions=transactions)
                self.students[student.student_id] = student
            print(f"Loaded data from {filename}.")
            return True
        except FileNotFoundError:
            print(f"No data file found at {filename}. Starting fresh.")
            return False
        except Exception as e:
            print("Failed to load data:", e)
            return False


def main_menu():
    print("\n=== Student Finance Manager ===")
    print("1. Add student")
    print("2. Remove student")
    print("3. Record income")
    print("4. Record expense")
    print("5. Show student report")
    print("6. List all students (summary)")
    print("7. Save data")
    print("8. Load data")
    print("9. Exit")
    print("===============================")


def input_nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Please enter a non-empty value.")


def run_cli():
    fm = FinanceManager()
    fm.load()  # attempt to load existing data on start

    while True:
        main_menu()
        choice = input("Enter choice: ").strip()
        if choice == "1":
            sid = input_nonempty("Student ID (unique): ")
            name = input_nonempty("Student name: ")
            if fm.add_student(sid, name):
                print("Student added.")
            else:
                print("Student ID already exists.")
        elif choice == "2":
            sid = input_nonempty("Student ID to remove: ")
            if fm.remove_student(sid):
                print("Student removed.")
            else:
                print("Student not found.")
        elif choice == "3" or choice == "4":
            sid = input_nonempty("Student ID: ")
            student = fm.find_student(sid)
            if not student:
                print("Student not found.")
                continue
            try:
                amount_str = input_nonempty("Amount: ")
                amount = float(amount_str)
            except ValueError:
                print("Invalid amount. Use numbers like 1500.50")
                continue
            desc = input("Description (optional): ").strip() or ("Income" if choice == "3" else "Expense")
            # allow custom date or default today
            date_input = input("Date (YYYY-MM-DD) [leave empty for today]: ").strip()
            if date_input:
                try:
                    datetime.strptime(date_input, DATE_FMT)
                    date = date_input
                except ValueError:
                    print("Invalid date format; using today's date.")
                    date = datetime.now().strftime(DATE_FMT)
            else:
                date = None
            ttype = "income" if choice == "3" else "expense"
            if fm.record_transaction(sid, ttype, amount, desc, date):
                print(f"{ttype.title()} recorded.")
            else:
                print("Failed to record transaction.")
        elif choice == "5":
            sid = input_nonempty("Student ID: ")
            report = fm.student_report(sid)
            if not report:
                print("Student not found.")
                continue
            print("\n--- Student Report ---")
            print(f"ID: {report['student_id']}\nName: {report['name']}\nBalance: {report['balance']:.2f}")
            print("Transactions:")
            if not report["transactions"]:
                print("  (no transactions)")
            else:
                for i, t in enumerate(report["transactions"], 1):
                    sign = "+" if t["ttype"] == "income" else "-"
                    print(f" {i}. [{t['date']}] {t['ttype'].title():7} {sign}{t['amount']:.2f} — {t['description']}")
        elif choice == "6":
            summary = fm.all_students_summary()
            if not summary:
                print("No students.")
            else:
                print("\nStudents summary:")
                for s in summary:
                    print(f" - {s['student_id']}: {s['name']} | Balance: {s['balance']:.2f} | Tx: {s['num_transactions']}")
        elif choice == "7":
            fm.save()
        elif choice == "8":
            fm.load()
        elif choice == "9":
            print("Saving before exit...")
            fm.save()
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Pick 1-9.")


if __name__ == "__main__":
    run_cli()
