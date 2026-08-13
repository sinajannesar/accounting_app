"""منطق یکپارچه کدینگ درختی حساب‌ها."""

from datetime import datetime

from database.db_manager import ACCOUNT_TYPE_LABELS, LEVEL_LABELS


class AccountModel:
    ROOT_TYPES = {"1": "asset", "2": "liability", "3": "equity", "4": "income", "5": "expense"}
    CREATABLE_LEVELS = (2, 3, 4)

    def __init__(self, db):
        self.db = db

    def get_all(self, search="", active_only=True, account_type=None, level=None):
        query = """SELECT a.*, p.name AS parent_name, p.code AS parent_code
                   FROM accounts a LEFT JOIN accounts p ON a.parent_id = p.id WHERE 1=1"""
        params = []
        if active_only:
            query += " AND a.is_active = 1"
        if account_type:
            query += " AND a.account_type = ?"; params.append(account_type)
        if level:
            query += " AND a.level = ?"; params.append(level)
        if search:
            query += " AND (a.code LIKE ? OR a.name LIKE ?)"; params += [f"%{search}%", f"%{search}%"]
        query += " ORDER BY a.code"
        return [dict(row) for row in self.db.conn.execute(query, params).fetchall()]

    def get_by_id(self, account_id):
        row = self.db.conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return dict(row) if row else None

    def get_by_code(self, code):
        row = self.db.conn.execute("SELECT * FROM accounts WHERE code = ?", (code,)).fetchone()
        return dict(row) if row else None

    def get_tree(self):
        by_parent = {}
        for account in self.get_all(active_only=False):
            by_parent.setdefault(account["parent_id"] or 0, []).append(account)
        return by_parent

    def get_children_ids(self, account_id):
        rows = self.db.conn.execute(
            """WITH RECURSIVE descendants(id) AS (
                   SELECT id FROM accounts WHERE id = ?
                   UNION ALL SELECT a.id FROM accounts a JOIN descendants d ON a.parent_id = d.id
               ) SELECT id FROM descendants""", (account_id,)
        ).fetchall()
        return [row["id"] for row in rows]

    def get_accounts_for_level(self, level, active_only=True):
        return self.get_all(active_only=active_only, level=level)

    def get_valid_parents(self, level, active_only=True):
        if level not in self.CREATABLE_LEVELS:
            return []
        return self.get_accounts_for_level(level - 1, active_only)

    def get_postable_accounts(self):
        """فقط حساب‌های برگِ معین/تفصیلی برای اسناد جدید؛ داده‌های قدیمی محفوظ‌اند."""
        rows = self.db.conn.execute("""
            SELECT a.* FROM accounts a
            WHERE a.level >= 3 AND a.is_active = 1
              AND NOT EXISTS (SELECT 1 FROM accounts c WHERE c.parent_id = a.id AND c.is_active = 1)
            ORDER BY a.code
        """).fetchall()
        return [dict(row) for row in rows]

    def next_code(self, parent_id, level):
        parent = self.get_by_id(parent_id) if parent_id else None
        self._validate_parent(parent, level, None)
        prefix = parent["code"]
        # کدهای حساب کل جدید چهاررقمی‌اند (1100، 1200، …) تا فضای کافی
        # برای توسعه داشته باشند؛ ساختار قدیمی دو/سه‌رقمی همچنان خواندنی است.
        if level == 2 and parent["level"] == 1:
            structured = self.db.conn.execute(
                "SELECT code FROM accounts WHERE parent_id = ? AND length(code) >= 4 AND substr(code, -2) = '00'",
                (parent_id,),
            ).fetchall()
            sequences = [int(row["code"][1:-2]) for row in structured if row["code"].startswith(prefix)]
            sequence = max(sequences, default=0) + 1
            return f"{prefix}{sequence}00"
        if level == 3 and len(prefix) >= 4 and prefix.endswith("00"):
            children = self.db.conn.execute("SELECT code FROM accounts WHERE parent_id = ?", (parent_id,)).fetchall()
            sequences = [int(row["code"][-2:]) for row in children if len(row["code"]) == len(prefix) and row["code"][:-2] == prefix[:-2] and row["code"][-2:].isdigit()]
            return f"{prefix[:-2]}{max(sequences, default=0) + 1:02d}"
        children = self.db.conn.execute("SELECT code FROM accounts WHERE parent_id = ?", (parent_id,)).fetchall()
        suffixes = []
        for child in children:
            suffix = child["code"][len(prefix):]
            if len(suffix) == 2 and suffix.isdigit():
                suffixes.append(int(suffix))
        sequence = max(suffixes, default=0) + 1
        if sequence > 99:
            raise ValueError("برای این حساب والد بیش از ۹۹ زیرحساب قابل ایجاد نیست")
        return f"{prefix}{sequence:02d}"

    def create(self, name, parent_id, level, description="", code=None):
        name = (name or "").strip()
        if not name:
            raise ValueError("نام حساب الزامی است")
        parent = self.get_by_id(parent_id) if parent_id else None
        self._validate_parent(parent, level, code)
        if self.db.conn.execute("SELECT 1 FROM accounts WHERE parent_id = ? AND name = ?", (parent_id, name)).fetchone():
            raise ValueError("نام حساب زیر این والد تکراری است")
        account_type = parent["account_type"]
        code = code or self.next_code(parent_id, level)
        self._validate_code(code, parent, level)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.conn.execute(
            """INSERT INTO accounts (code, name, parent_id, level, account_type, description, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, name, parent_id, level, account_type, description.strip(), now),
        )
        self.db.conn.commit()
        return cur.lastrowid

    def update(self, account_id, name, is_active, description=""):
        account = self.get_by_id(account_id)
        if not account:
            raise ValueError("حساب یافت نشد")
        name = (name or "").strip()
        if not name:
            raise ValueError("نام حساب الزامی است")
        duplicate = self.db.conn.execute(
            "SELECT 1 FROM accounts WHERE parent_id IS ? AND name = ? AND id != ?",
            (account["parent_id"], name, account_id),
        ).fetchone()
        if duplicate:
            raise ValueError("نام حساب زیر این والد تکراری است")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.conn.execute(
            "UPDATE accounts SET name=?, is_active=?, description=?, updated_at=? WHERE id=?",
            (name, 1 if is_active else 0, description.strip(), now, account_id),
        )
        self.db.conn.commit()

    def delete(self, account_id):
        if self.db.conn.execute("SELECT 1 FROM journal_lines WHERE account_id = ?", (account_id,)).fetchone():
            raise ValueError("این حساب در اسناد استفاده شده و قابل حذف نیست؛ آن را غیرفعال کنید")
        if self.db.conn.execute("SELECT 1 FROM accounts WHERE parent_id = ?", (account_id,)).fetchone():
            raise ValueError("این حساب دارای زیرمجموعه است و قابل حذف نیست")
        self.db.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.db.conn.commit()

    def validate_postable(self, account_id):
        account = self.get_by_id(account_id)
        if not account or not account["is_active"]:
            raise ValueError("حساب انتخاب‌شده معتبر یا فعال نیست")
        if account["level"] < 3:
            raise ValueError("ثبت سند فقط روی حساب معین یا تفصیلی مجاز است")
        active_child = self.db.conn.execute(
            "SELECT 1 FROM accounts WHERE parent_id = ? AND is_active = 1", (account_id,)
        ).fetchone()
        if active_child:
            raise ValueError("برای ثبت سند باید حساب برگ (معین یا تفصیلی) انتخاب شود")

    def _validate_parent(self, parent, level, code):
        if level not in self.CREATABLE_LEVELS:
            raise ValueError("ایجاد حساب فقط در سطح کل، معین یا تفصیلی مجاز است")
        if not parent:
            raise ValueError("حساب والد معتبر الزامی است")
        if parent["level"] != level - 1:
            raise ValueError(f"حساب سطح {LEVEL_LABELS[level]} باید زیر {LEVEL_LABELS[level - 1]} ایجاد شود")
        if not parent["is_active"]:
            raise ValueError("حساب والد غیرفعال است")

    def _validate_code(self, code, parent, level):
        if not code or not code.isdigit():
            raise ValueError("کد حساب باید فقط شامل رقم باشد")
        if self.db.conn.execute("SELECT 1 FROM accounts WHERE code = ?", (code,)).fetchone():
            raise ValueError("کد حساب تکراری است")
        if level == 2 and parent["level"] == 1:
            valid_shape = len(code) >= 4 and code.startswith(parent["code"]) and code.endswith("00")
        elif level == 3 and len(parent["code"]) >= 4 and parent["code"].endswith("00"):
            valid_shape = len(code) == len(parent["code"]) and code[:-2] == parent["code"][:-2]
        else:
            valid_shape = code.startswith(parent["code"]) and len(code) == len(parent["code"]) + 2
        if not valid_shape:
            raise ValueError("کد حساب با ساختار سلسله‌مراتبی والد سازگار نیست")
        root_code = code[0]
        if self.ROOT_TYPES.get(root_code) != parent["account_type"]:
            raise ValueError("کد حساب با گروه اصلی سازگار نیست")

    @staticmethod
    def type_label(account_type):
        return ACCOUNT_TYPE_LABELS.get(account_type, account_type)

    @staticmethod
    def level_label(level):
        return LEVEL_LABELS.get(level, str(level))
