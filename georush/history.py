"""Independent SQLite production ledger with atomic composition reservations."""
import json
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class History:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                signature TEXT NOT NULL UNIQUE, difficulty TEXT NOT NULL,
                output_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'running',
                error TEXT NOT NULL DEFAULT '', quiz_json TEXT NOT NULL)''')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(str(self.path), timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve_quiz(self, signature, difficulty, output_path, quiz):
        with self._connect() as db:
            cursor = db.execute('INSERT INTO runs(signature,difficulty,output_path,quiz_json) VALUES(?,?,?,?)',
                                (signature, difficulty, str(output_path), json.dumps(quiz, ensure_ascii=False)))
            return cursor.lastrowid

    def finish(self, run_id, success, error=''):
        with self._connect() as db:
            cursor = db.execute("UPDATE runs SET status=?,error=? WHERE id=? AND status='running'",
                                ('success' if success else 'failed', str(error), run_id))
            if cursor.rowcount != 1:
                raise ValueError('실행 중인 제작 이력을 찾을 수 없습니다.')

    def list_runs(self, limit=100):
        with self._connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT ?', (int(limit),))]

    def used_signatures(self):
        with self._connect() as db:
            return {row[0] for row in db.execute('SELECT signature FROM runs')}

    def recent_country_codes(self, limit=20):
        codes = set()
        for row in self.list_runs(limit):
            if row['status'] in ('running', 'success'):
                codes.update(q['country_code'] for q in json.loads(row['quiz_json'])['questions'])
        return codes

    def recent_shorts_country_codes(self, limit=7):
        # Longform runs list 20-40 countries and would mark the whole pool as recent.
        runs = []
        with self._connect() as db:
            for row in db.execute("SELECT quiz_json FROM runs WHERE status IN ('running','success') "
                                  "AND signature NOT LIKE 'longform:%' ORDER BY id DESC LIMIT ?", (int(limit),)):
                runs.append({q['country_code'] for q in json.loads(row[0])['questions']})
        return runs
