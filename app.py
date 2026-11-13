
from flask import Flask, request, redirect, render_template, send_from_directory, abort, Response
from pathlib import Path
from werkzeug.utils import secure_filename
import sqlite3
import uuid
import csv
import io
import os

app = Flask(__name__)
BASE = Path(__file__).resolve().parent
DATA = BASE / "casefile_data"
UPLOADS = DATA / "uploads"
DB = DATA / "casefile.db"
UPLOADS.mkdir(parents=True, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
ALLOWED = {".pdf", ".txt", ".png", ".jpg", ".jpeg"}


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            number TEXT,
            court TEXT,
            status TEXT DEFAULT 'Open',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES cases(id)
        );

        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            source TEXT,
            status TEXT DEFAULT 'Needs Review',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES cases(id)
        );
        """)


init_db()


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    with connect() as db:
        cases = db.execute(
            """SELECT * FROM cases
               WHERE name LIKE ? OR number LIKE ?
               ORDER BY id DESC""",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
    return render_template("index.html", cases=cases, query=query)


@app.post("/cases")
def create_case():
    name = request.form.get("name", "").strip()
    if not name:
        abort(400, "Case name is required")

    with connect() as db:
        db.execute(
            """INSERT INTO cases (name, number, court, notes)
               VALUES (?, ?, ?, ?)""",
            (
                name,
                request.form.get("number", ""),
                request.form.get("court", ""),
                request.form.get("notes", "")
            )
        )
    return redirect("/")


@app.route("/cases/<int:case_id>")
def case_detail(case_id):
    with connect() as db:
        case = db.execute(
            "SELECT * FROM cases WHERE id=?", (case_id,)
        ).fetchone()

        if case is None:
            abort(404)

        documents = db.execute(
            "SELECT * FROM documents WHERE case_id=? ORDER BY id DESC",
            (case_id,)
        ).fetchall()

        findings = db.execute(
            "SELECT * FROM findings WHERE case_id=? ORDER BY id DESC",
            (case_id,)
        ).fetchall()

    return render_template(
        "index.html",
        cases=None,
        case=case,
        documents=documents,
        findings=findings
    )


@app.post("/cases/<int:case_id>/upload")
def upload(case_id):
    file = request.files.get("file")
    if not file or not file.filename:
        abort(400, "Select a file")

    filename = secure_filename(file.filename)
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED:
        abort(400, "Unsupported file type")

    with connect() as db:
        if not db.execute(
            "SELECT id FROM cases WHERE id=?", (case_id,)
        ).fetchone():
            abort(404)

        stored = f"{uuid.uuid4().hex}{extension}"
        folder = UPLOADS / str(case_id)
        folder.mkdir(parents=True, exist_ok=True)
        file.save(folder / stored)

        db.execute(
            """INSERT INTO documents
               (case_id, filename, stored_name, category)
               VALUES (?, ?, ?, ?)""",
            (
                case_id, filename, stored,
                request.form.get("category", "Other")
            )
        )

    return redirect(f"/cases/{case_id}")


@app.route("/documents/<int:document_id>")
def download(document_id):
    with connect() as db:
        doc = db.execute(
            "SELECT * FROM documents WHERE id=?", (document_id,)
        ).fetchone()

    if not doc:
        abort(404)

    return send_from_directory(
        UPLOADS / str(doc["case_id"]),
        doc["stored_name"],
        as_attachment=True,
        download_name=doc["filename"]
    )


@app.post("/cases/<int:case_id>/findings")
def add_finding(case_id):
    title = request.form.get("title", "").strip()
    if not title:
        abort(400, "Finding title is required")

    with connect() as db:
        if not db.execute(
            "SELECT id FROM cases WHERE id=?", (case_id,)
        ).fetchone():
            abort(404)

        db.execute(
            """INSERT INTO findings
               (case_id, title, description, source)
               VALUES (?, ?, ?, ?)""",
            (
                case_id, title,
                request.form.get("description", ""),
                request.form.get("source", "")
            )
        )

    return redirect(f"/cases/{case_id}")


@app.post("/findings/<int:finding_id>/toggle")
def toggle_finding(finding_id):
    with connect() as db:
        finding = db.execute(
            "SELECT * FROM findings WHERE id=?", (finding_id,)
        ).fetchone()

        if not finding:
            abort(404)

        status = (
            "Reviewed"
            if finding["status"] == "Needs Review"
            else "Needs Review"
        )

        db.execute(
            "UPDATE findings SET status=? WHERE id=?",
            (status, finding_id)
        )

    return redirect(f"/cases/{finding['case_id']}")


@app.route("/export")
def export_cases():
    with connect() as db:
        cases = db.execute(
            "SELECT id, name, number, court, status, notes FROM cases"
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Case Name", "Case Number", "Court", "Status", "Notes"]
    )

    for case in cases:
        writer.writerow(tuple(case))

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=casefile_cases.csv"
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
