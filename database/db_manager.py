"""مدیریت پایگاه داده SQLite"""

import os
import shutil
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES accounts(id),
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
    account_type TEXT NOT NULL CHECK(account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_number INTEGER NOT NULL UNIQUE,
    entry_date TEXT NOT NULL,
    due_date TEXT,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    debit REAL DEFAULT 0 CHECK(debit >= 0),
    credit REAL DEFAULT 0 CHECK(credit >= 0),
    line_description TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_accounts_parent ON accounts(parent_id);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_due ON journal_entries(due_date);
CREATE INDEX IF NOT EXISTS idx_lines_account ON journal_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_lines_entry ON journal_lines(journal_entry_id);
"""

DEFAULT_ACCOUNTS = [
    ("1", "دارایی‌ها", None, 1, "asset"),
    ("11", "دارایی‌های جاری", "1", 2, "asset"),
    ("111", "صندوق", "11", 3, "asset"),
    ("111001", "صندوق اصلی", "111", 4, "asset"),
    ("112", "بانک", "11", 3, "asset"),
    ("112001", "بانک ملت", "112", 4, "asset"),
    ("2", "بدهی‌ها", None, 1, "liability"),
    ("21", "بدهی‌های جاری", "2", 2, "liability"),
    ("211", "حساب‌های پرداختنی", "21", 3, "liability"),
    ("3", "سرمایه", None, 1, "equity"),
    ("31", "سرمایه اولیه", "3", 2, "equity"),
    ("4", "درآمدها", None, 1, "income"),
    ("41", "درآمد فروش", "4", 2, "income"),
    ("411", "فروش کالا", "41", 3, "income"),
    ("5", "هزینه‌ها", None, 1, "expense"),
    ("51", "هزینه‌های عملیاتی", "5", 2, "expense"),
    ("511", "هزینه اجاره", "51", 3, "expense"),
    ("512", "هزینه حقوق", "51", 3, "expense"),
]

ACCOUNT_TYPE_LABELS = {
    "asset": "دارایی",
    "liability": "بدهی",
    "equity": "سرمایه",
    "income": "درآمد",
    "expense": "هزینه",
}

LEVEL_LABELS = {
    1: "گروه",
    2: "کل",
    3: "معین",
    4: "تفصیلی",
    5: "تفصیلی شناور",
}


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            app_data = Path.home() / "Documents" / "HesabdariApp"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = app_data / "accounting.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def initialize(self):
        self.conn.executescript(SCHEMA)
        count = self.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if count == 0:
            self._seed_default_accounts()
        self.conn.commit()

    def _seed_default_accounts(self):
        id_map = {}
        for code, name, parent_code, level, acc_type in DEFAULT_ACCOUNTS:
            parent_id = id_map.get(parent_code) if parent_code else None
            cur = self.conn.execute(
                "INSERT INTO accounts (code, name, parent_id, level, account_type) VALUES (?, ?, ?, ?, ?)",
                (code, name, parent_id, level, acc_type),
            )
            id_map[code] = cur.lastrowid
        self.conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('cash_account_id', ?)",
            (str(id_map["111001"]),),
        )

    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        self.conn.commit()

    def backup(self, dest_path):
        dest_path = Path(dest_path)
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None
        shutil.copy2(self.db_path, dest_path)
        self.conn

    def restore(self, src_path):
        src_path = Path(src_path)
        if not src_path.exists():
            raise FileNotFoundError("فایل پشتیبان یافت نشد")
        if self._conn:
            self._conn.close()
            self._conn = None
        shutil.copy2(src_path, self.db_path)
        self.conn

    def close(self):
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None
