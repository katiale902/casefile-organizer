# Casefile Organizer

A beginner-friendly Python project for organizing fictional case records, searching cases, exporting CSV reports, and managing PDF case files in a browser dashboard.

## Features
- View all case records in a dashboard
- Search by case ID or category
- Filter by case status
- Add new case records from the browser
- Export a report to CSV
- Upload PDFs and organize them by date and case metadata

## Quick start

1. Create a virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .\.venv\Scripts\activate   # Windows
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Start the dashboard
   ```bash
   streamlit run app.py
   ```

4. Open the browser URL shown in the terminal, usually:
   ```text
   http://localhost:8501
   ```

## CLI version

The original terminal-based workflow is still available in `casefile_organizer.py`.

```bash
python casefile_organizer.py
```

## Notes
- The app stores case data in `cases.json`.
- Organized PDFs are placed in the `organized_case_files/` folder.
- If PDF metadata is unclear, the dashboard lets you type in the missing values before saving.

