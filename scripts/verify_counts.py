"""Verify document counts in SQLite database."""
import sqlite3
import os

DB_PATH = 'document_db.sqlite'

def verify_counts():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total count
        total = cursor.execute("SELECT count(1) FROM documents").fetchone()[0]
        print(f"Total documents: {total}")

        # Count by extension (approximate using last 4-5 chars)
        cursor.execute("SELECT filename FROM documents")
        filenames = [r[0] for r in cursor.fetchall()]

        counts = {}
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            counts[ext] = counts.get(ext, 0) + 1

        print("\nDocument counts by extension:")
        for ext, count in sorted(counts.items()):
            print(f"  {ext}: {count}")

        # HTML specific check
        html_count = counts.get('.html', 0) + counts.get('.htm', 0)
        print(f"\nHTML files found: {html_count}")

        # PDF specific check
        pdf_count = counts.get('.pdf', 0)
        print(f"PDF files found: {pdf_count}")

        conn.close()

    except Exception as e:
        print(f"❌ Error verifying counts: {e}")

if __name__ == "__main__":
    verify_counts()
