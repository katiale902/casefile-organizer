import csv
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


DEFAULT_CASES = [
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

DATA_FILE = Path(__file__).with_name("cases.json")
ORGANIZED_OUTPUT = Path(__file__).with_name("organized_case_files")


def load_cases():
    if not DATA_FILE.exists():
        save_cases(DEFAULT_CASES)
        return list(DEFAULT_CASES)

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return list(DEFAULT_CASES)

    if isinstance(data, list) and data:
        return data
    return list(DEFAULT_CASES)


def save_cases(records):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def list_cases(records):
    if not records:
        print("No cases found.")
        return

    for case in records:
        print(
            f"{case.get('case_id', 'UNKNOWN')} | "
            f"{case.get('category', 'N/A')} | "
            f"{case.get('status', 'N/A')} | "
            f"{case.get('priority', 'N/A')}"
        )


def search_case(records):
    case_id = input("Enter case ID: ").strip().upper()
    matches = [
        case for case in records if str(case.get("case_id", "")).upper() == case_id
    ]
    list_cases(matches)


def filter_by_status(records):
    status = input("Enter status (Open, Pending, Closed): ").strip().lower()
    matches = [
        case for case in records if str(case.get("status", "")).lower() == status
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
            fieldnames=["case_id", "category", "status", "priority"],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"Report saved to {filename}")


def add_case(records):
    case_id = input("Enter case ID: ").strip().upper()

    for case in records:
        if str(case.get("case_id", "")).upper() == case_id:
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
    save_cases(records)
    print(f"Case {case_id} added successfully.")


def sanitize_filename(value):
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "", str(value)).strip()
    return cleaned or "unknown"


def unique_destination(path):
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def normalize_date_value(raw_date):
    value = str(raw_date).strip()
    if not value or value.lower() == "unknown-date":
        return "unknown-date"

    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
    ):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    value = value.replace("/", "-")
    value = value.replace(" ", "-")
    return value


def extract_text_from_pdf(pdf_path):
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed. Run: pip install -r requirements.txt")

    reader = PdfReader(str(pdf_path))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text_parts.append(text)
    return "\n".join(text_parts)


def find_date_in_text(text):
    patterns = [
        r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:\d{2}|\d{4})\b",
        r"\b(?:\d{4})-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return "unknown-date"


def find_case_number_in_text(text):
    patterns = [
        r"\b(?:CASE|Case|Docket|DOCKET|Case No\.?|Case Number|No\.?|No)[#:\s-]*([A-Z]{2,}[-\s]?\d{2,})\b",
        r"\b([A-Z]{2,}-\d{2,})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1) if match.lastindex else match.group(0)
            return candidate.strip().upper().replace(" ", "-")
    return "unknown-case"


def find_last_name_in_text(text):
    patterns = [
        r"Defendant(?:\s*(?:Name|Last Name|Surname|Legal Name))?:?\s*([A-Z][A-Za-z'-.]+(?:\s+[A-Z][A-Za-z'-.]+)*)",
        r"\bDefendant\s+([A-Z][A-Za-z'-.]+(?:\s+[A-Z][A-Za-z'-.]+)*)",
        r"\b([A-Z][A-Za-z'-.]+),\s*(?:[A-Z][A-Za-z'-.]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if "," in candidate:
                candidate = candidate.split(",")[0]
            parts = candidate.split()
            if len(parts) > 1:
                return parts[-1].title()
            return candidate.title()
    return "unknown-lastname"


def infer_pdf_metadata(pdf_path):
    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as exc:
        print(f"Could not read PDF text in {pdf_path.name}: {exc}")
        return {
            "date": "unknown-date",
            "case_number": "unknown-case",
            "last_name": "unknown-lastname",
        }

    return {
        "date": find_date_in_text(text),
        "case_number": find_case_number_in_text(text),
        "last_name": find_last_name_in_text(text),
    }


def organize_pdf_files(paths):
    ORGANIZED_OUTPUT.mkdir(exist_ok=True)

    discovered = []

    for item in paths:
        path = Path(item).expanduser()
        if not path.exists():
            print(f"Skipped missing path: {path}")
            continue

        if path.is_dir():
            discovered.extend(sorted(path.rglob("*.pdf")))
        elif path.suffix.lower() == ".pdf":
            discovered.append(path)

    if not discovered:
        print("No PDF files found in the provided path(s).")
        return

    for pdf_path in discovered:
        print(f"Processing: {pdf_path.name}")

        metadata = infer_pdf_metadata(pdf_path)
        date_value = metadata["date"]
        case_number = metadata["case_number"]
        last_name = metadata["last_name"]

        if date_value == "unknown-date":
            date_value = input(
                f"Enter filing date for {pdf_path.name} (YYYY-MM-DD or MM/DD/YYYY): "
            ).strip() or "unknown-date"

        if case_number == "unknown-case":
            case_number = input(f"Enter case number for {pdf_path.name}: ").strip() or "unknown-case"

        if last_name == "unknown-lastname":
            last_name = input(f"Enter defendant last name for {pdf_path.name}: ").strip() or "unknown-lastname"

        normalized_date = normalize_date_value(date_value)

        target_folder = ORGANIZED_OUTPUT / normalized_date
        target_folder.mkdir(exist_ok=True)

        safe_base = f"{sanitize_filename(case_number)}_{sanitize_filename(last_name)}"
        target_file = target_folder / f"{safe_base}.pdf"
        target_file = unique_destination(target_file)

        shutil.copy2(pdf_path, target_file)
        print(f"Stored as: {target_file}")

    print(f"\nFinished organizing PDFs. Output folder: {ORGANIZED_OUTPUT}")


def prompt_for_pdf_path():
    path_input = input("Drag in a PDF file or folder path and press Enter: ").strip().strip('"')
    if not path_input:
        print("No path provided.")
        return

    organize_pdf_files([path_input])


def main():
    records = load_cases()

    while True:
        print("\n=== CASEFILE ORGANIZER ===")
        print("1. List all cases")
        print("2. Search by case ID")
        print("3. Filter by status")
        print("4. Export CSV report")
        print("5. Add a new case")
        print("6. Organize PDFs")
        print("7. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_cases(records)
        elif choice == "2":
            search_case(records)
        elif choice == "3":
            filter_by_status(records)
        elif choice == "4":
            export_report(records)
        elif choice == "5":
            add_case(records)
        elif choice == "6":
            prompt_for_pdf_path()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-7.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "organize":
        if len(sys.argv) > 2:
            organize_pdf_files(sys.argv[2:])
        else:
            print("Usage: python casefile_organizer.py organize /path/to/file_or_folder")
    else:
        main()
