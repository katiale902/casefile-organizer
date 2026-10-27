
import csv

cases = [
    {
        "case_id": "CASE-001",
        "category": "Fraud",
        "status": "Open",
        "priority": "High",
    },
    {
        "case_id": "CASE-002",
        "category": "Missing Documents",
        "status": "Pending",
        "priority": "Medium",
    },
    {
        "case_id": "CASE-003",
        "category": "Online Harassment",
        "status": "Closed",
        "priority": "Low",
    },
]


def list_cases(records):
    if not records:
        print("No cases found.")
        return

    for case in records:
        print(
            f"{case['case_id']} | "
            f"{case['category']} | "
            f"{case['status']} | "
            f"{case['priority']}"
        )


def search_case(records):
    case_id = input("Enter case ID: ").strip().upper()

    matches = [
        case for case in records
        if case["case_id"] == case_id
    ]

    list_cases(matches)


def filter_by_status(records):
    status = input(
        "Enter status (Open, Pending, Closed): "
    ).strip().lower()

    matches = [
        case for case in records
        if case["status"].lower() == status
    ]

    list_cases(matches)


def export_report(records):
    filename = "case_report.csv"

    if not records:
        print("No records to export.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "category",
                "status",
                "priority",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"Report saved to {filename}")


def add_case(records):
    case_id = input("Enter case ID: ").strip().upper()

    # Prevent duplicate case IDs
    for case in records:
        if case["case_id"].upper() == case_id:
            print("Error: That case ID already exists.")
            return

    category = input("Enter case category: ").strip()
    status = input("Enter status (Open, Pending, Closed): ").strip().title()
    priority = input("Enter priority (High, Medium, Low): ").strip().title()

    new_case = {
        "case_id": case_id,
        "category": category,
        "status": status,
        "priority": priority,
    }

    records.append(new_case)
    print(f"Case {case_id} added successfully.")

def main():
    while True:
        print("\n=== CASEFILE ORGANIZER ===")
        print("1. List all cases")
        print("2. Search by case ID")
        print("3. Filter by status")
        print("4. Export CSV report")
        print("5. Exit")
        print("6. Add a new case")
        elif choice == "6":
    add_case(cases)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_cases(cases)
        elif choice == "2":
            search_case(cases)
        elif choice == "3":
            filter_by_status(cases)
        elif choice == "4":
            export_report(cases)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()
