# casefile-organizer
A beginner-friendly Python automation project for organizing fictional case records, searching cases by ID or status, exporting reports to CSV, and organizing PDF case files by date, case number, and defendant last name.

## Features
- List all case records
- Search by case ID
- Filter records by status
- Add new case records
- Export a CSV report
- Drag in a PDF file or folder to organize it into date- and case-based folders

## Quick start

1. Create a virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On macOS/Linux
   .\.venv\Scripts\activate    # On Windows
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app
   ```bash
   python casefile_organizer.py
   ```

## PDF organization
The organizer is designed to work locally and will try to detect metadata automatically from the PDF text.

- Drag a PDF file or folder onto the terminal/command line path when launching.
- Or choose option 6 in the menu and paste a PDF path.
- The script will group files under an `organized_case_files` folder by date, then by case number and defendant last name.

Example:
```bash
python casefile_organizer.py organize "C:/Cases/Incoming"
```

## Notes
- This project is intended for training and local file organization.
- PDFs that are scanned images may need OCR before the metadata can be extracted reliably.
- The app keeps a local `cases.json` file in the project folder so records persist between runs.
