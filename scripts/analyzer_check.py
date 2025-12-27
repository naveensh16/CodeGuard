"""Utility script to verify analyzer pipeline end-to-end."""

import os
import sys
from pathlib import Path
from textwrap import dedent

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app, db, Project, CodeFile, Issue, analyze_code_file

SAMPLE_FILENAME = "analyzer_sample.py"
SAMPLE_CODE = dedent(
    """
    import os
    import sqlite3
    import pickle

    password = "supersecret"
    api_key = "sk-demo-key"

    def insecure_eval(cmd):
        return eval(cmd)

    def insecure_query(user_id):
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE id = " + user_id
        cursor.execute(query)
        return cursor.fetchall()

    def file_leak(path):
        f = open(path)
        data = f.read()
        return data

    def performance_issue(items):
        total = 0
        for item in items:
            for other in items:
                total += item * other
        return total
    """
)


def ensure_upload_dir():
    uploads = app.config["UPLOAD_FOLDER"]
    os.makedirs(uploads, exist_ok=True)
    return uploads


def write_sample_file(uploads_dir: str) -> str:
    file_path = os.path.join(uploads_dir, SAMPLE_FILENAME)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(SAMPLE_CODE)
    return file_path


def main():
    uploads_dir = ensure_upload_dir()
    file_path = write_sample_file(uploads_dir)

    with app.app_context():
        project = Project.query.first()
        if project is None:
            raise RuntimeError("No project found. Create one via the UI before running this script.")

        existing = CodeFile.query.filter_by(filename=SAMPLE_FILENAME, project_id=project.id).first()
        if existing:
            Issue.query.filter_by(file_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

        code_file = CodeFile(
            filename=SAMPLE_FILENAME,
            filepath=file_path,
            language="python",
            content=SAMPLE_CODE,
            project_id=project.id,
        )
        db.session.add(code_file)
        db.session.commit()

        analyze_code_file(code_file.id)
        issue_count = Issue.query.filter_by(file_id=code_file.id).count()
        print(f"Analyzer produced {issue_count} issues for {SAMPLE_FILENAME}.")

        if issue_count == 0:
            print("⚠️  No issues detected. Something is wrong with the analyzer pipeline.")
        else:
            print("✅ Analyzer is working correctly.")


if __name__ == "__main__":
    main()
