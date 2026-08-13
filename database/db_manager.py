"""مدیریت پایگاه داده SQLite و migrationهای سازگار با داده‌های قبلی."""

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
    is_active INTEGER NOT NULL DEFAULT 1,
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT
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
    debit REAL NOT NULL DEFAULT 0 CHECK(debit >= 0),
    credit REAL NOT NULL DEFAULT 0 CHECK(credit >= 0),
    line_description TEXT
);

CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX IF NOT EXISTS idx_accounts_parent ON accounts(parent_id);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_due ON journal_entries(due_date);
CREATE INDEX IF NOT EXISTS idx_lines_account ON journal_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_lines_entry ON journal_lines(journal_entry_id);
"""

# کدهای جدید از الگوی 1 / 11 / 1101 / 110101 پیروی می‌کنند. رکوردهای قدیمی
# هرگز بازکدگذاری نمی‌شوند؛ این seed فقط رکوردهای غایب را اضافه می‌کند.
DEFAULT_ACCOUNTS = [
    ("1", "دارایی‌ها", None, 1, "asset"), ("2", "بدهی‌ها", None, 1, "liability"),
    ("3", "سرمایه", None, 1, "equity"), ("4", "درآمدها", None, 1, "income"),
    ("5", "هزینه‌ها", None, 1, "expense"),
    ("11", "دارایی‌های جاری", "1", 2, "asset"), ("12", "بانک‌ها", "1", 2, "asset"),
    ("13", "صندوق", "1", 2, "asset"), ("14", "حساب‌ها و اسناد دریافتنی", "1", 2, "asset"),
    ("15", "موجودی کالا", "1", 2, "asset"), ("16", "پیش‌پرداخت‌ها", "1", 2, "asset"),
    ("17", "دارایی‌های ثابت", "1", 2, "asset"), ("18", "ساختمان", "1", 2, "asset"),
    ("19", "تجهیزات", "1", 2, "asset"),
    ("21", "بدهی‌های جاری", "2", 2, "liability"), ("22", "بستانکاران", "2", 2, "liability"),
    ("23", "بدهی به اشخاص", "2", 2, "liability"), ("24", "اسناد پرداختنی", "2", 2, "liability"),
    ("25", "وام‌ها و تسهیلات", "2", 2, "liability"), ("26", "مالیات پرداختنی", "2", 2, "liability"),
    ("27", "بیمه پرداختنی", "2", 2, "liability"),
    ("31", "سرمایه اولیه", "3", 2, "equity"), ("32", "سهامداران", "3", 2, "equity"),
    ("33", "سود و زیان انباشته", "3", 2, "equity"),
    ("41", "درآمد حاصل از فروش", "4", 2, "income"), ("42", "درآمد خدمات", "4", 2, "income"),
    ("43", "درآمد متفرقه", "4", 2, "income"), ("44", "درآمد سود بانکی", "4", 2, "income"),
    ("51", "هزینه‌های اداری", "5", 2, "expense"), ("52", "حقوق و دستمزد", "5", 2, "expense"),
    ("53", "اجاره", "5", 2, "expense"), ("54", "آب، برق و گاز", "5", 2, "expense"),
    ("55", "اینترنت و مخابرات", "5", 2, "expense"), ("56", "حمل‌ونقل", "5", 2, "expense"),
    ("57", "تبلیغات", "5", 2, "expense"), ("58", "تعمیرات", "5", 2, "expense"),
    ("59", "ملزومات اداری", "5", 2, "expense"),
    ("1201", "بانک ملت", "12", 3, "asset"), ("1202", "بانک سامان", "12", 3, "asset"),
    ("1203", "بانک ملی", "12", 3, "asset"), ("1204", "بانک صادرات", "12", 3, "asset"),
    ("120101", "ملت - شعبه شریعتی", "1201", 4, "asset"), ("120102", "ملت - شعبه مرکزی", "1201", 4, "asset"),
    ("120201", "سامان - شعبه مرکزی", "1202", 4, "asset"), ("1301", "صندوق اصلی", "13", 3, "asset"),
    ("130101", "صندوق ریالی", "1301", 4, "asset"),
    ("1401", "مشتریان", "14", 3, "asset"), ("140101", "مشتری A", "1401", 4, "asset"),
    ("140102", "مشتری B", "1401", 4, "asset"), ("140103", "مشتری C", "1401", 4, "asset"),
    ("2301", "اشخاص", "23", 3, "liability"), ("230101", "شخص A", "2301", 4, "liability"),
    ("3201", "سهامداران", "32", 3, "equity"), ("320101", "سهامدار ۱", "3201", 4, "equity"),
    ("320102", "سهامدار ۲", "3201", 4, "equity"),
    ("4101", "فروش کالا", "41", 3, "income"), ("410101", "فروش داخلی", "4101", 4, "income"),
    ("4201", "خدمات مشاوره", "42", 3, "income"), ("420101", "خدمات عمومی", "4201", 4, "income"),
    ("5101", "هزینه‌های اداری عمومی", "51", 3, "expense"), ("510101", "هزینه دفتر", "5101", 4, "expense"),
    ("5201", "حقوق کارکنان", "52", 3, "expense"), ("520101", "حقوق پرسنل", "5201", 4, "expense"),
]

ACCOUNT_TYPE_LABELS = {"asset": "دارایی", "liability": "بدهی", "equity": "سرمایه", "income": "درآمد", "expense": "هزینه"}
LEVEL_LABELS = {1: "گروه", 2: "کل", 3: "معین", 4: "تفصیلی", 5: "تفصیلی شناور"}


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
        self._migrate_accounts()
        self._seed_default_accounts()
        self.conn.commit()

    def _migrate_accounts(self):
        """افزودن ستون‌ها به دیتابیس‌های نسخه قبل، بدون حذف یا تغییر رکوردها."""
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(accounts)")}
        if "description" not in columns:
            self.conn.execute("ALTER TABLE accounts ADD COLUMN description TEXT DEFAULT ''")
        if "updated_at" not in columns:
            self.conn.execute("ALTER TABLE accounts ADD COLUMN updated_at TEXT")

    def _seed_default_accounts(self):
        for code, name, parent_code, level, account_type in DEFAULT_ACCOUNTS:
            if self.conn.execute("SELECT 1 FROM accounts WHERE code = ?", (code,)).fetchone():
                continue
            parent_id = None
            if parent_code:
                parent = self.conn.execute("SELECT id FROM accounts WHERE code = ?", (parent_code,)).fetchone()
                if not parent:
                    continue
                parent_id = parent["id"]
            self.conn.execute(
                "INSERT INTO accounts (code, name, parent_id, level, account_type) VALUES (?, ?, ?, ?, ?)",
                (code, name, parent_id, level, account_type),
            )
        cash = self.conn.execute("SELECT id FROM accounts WHERE code = '130101'").fetchone()
        if cash:
            self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cash_account_id', ?)", (str(cash['id']),))

    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def backup(self, dest_path):
        dest_path = Path(dest_path)
        if self._conn:
            self._conn.commit(); self._conn.close(); self._conn = None
        shutil.copy2(self.db_path, dest_path)
        self.conn

    def restore(self, src_path):
        src_path = Path(src_path)
        if not src_path.exists():
            raise FileNotFoundError("فایل پشتیبان یافت نشد")
        if self._conn:
            self._conn.close(); self._conn = None
        shutil.copy2(src_path, self.db_path)
        self.conn

    def close(self):
        if self._conn:
            self._conn.commit(); self._conn.close(); self._conn = None
