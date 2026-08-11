"""مدل سرفصل حساب‌ها"""

from database.db_manager import ACCOUNT_TYPE_LABELS, LEVEL_LABELS


class AccountModel:
    def __init__(self, db):
        self.db = db

    def get_all(self, search="", active_only=True):
        query = """
            SELECT a.*, p.name AS parent_name
            FROM accounts a
            LEFT JOIN accounts p ON a.parent_id = p.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND a.is_active = 1"
        if search:
            query += " AND (a.code LIKE ? OR a.name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY a.code"
        rows = self.db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, account_id):
        row = self.db.conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return dict(row) if row else None

    def get_tree(self):
        accounts = self.get_all(active_only=False)
        by_parent = {}
        for acc in accounts:
            pid = acc["parent_id"] or 0
            by_parent.setdefault(pid, []).append(acc)
        return by_parent

    def get_children_ids(self, account_id):
        """تمام زیرمجموعه‌های یک حساب (شامل خود حساب)"""
        result = [account_id]
        children = self.db.conn.execute(
            "SELECT id FROM accounts WHERE parent_id = ?", (account_id,)
        ).fetchall()
        for child in children:
            result.extend(self.get_children_ids(child["id"]))
        return result

    def get_postable_accounts(self):
        """حساب‌های قابل ثبت (معین و تفصیلی)"""
        rows = self.db.conn.execute(
            "SELECT * FROM accounts WHERE level >= 3 AND is_active = 1 ORDER BY code"
        ).fetchall()
        return [dict(r) for r in rows]

    def create(self, code, name, parent_id, level, account_type):
        if self.db.conn.execute("SELECT id FROM accounts WHERE code = ?", (code,)).fetchone():
            raise ValueError("کد حساب تکراری است")
        if parent_id:
            parent = self.get_by_id(parent_id)
            if not parent:
                raise ValueError("حساب والد یافت نشد")
            if level != parent["level"] + 1:
                raise ValueError(f"سطح حساب باید {parent['level'] + 1} باشد")
        elif level != 1:
            raise ValueError("حساب سطح اول نباید والد داشته باشد")

        cur = self.db.conn.execute(
            "INSERT INTO accounts (code, name, parent_id, level, account_type) VALUES (?, ?, ?, ?, ?)",
            (code, name, parent_id, level, account_type),
        )
        self.db.conn.commit()
        return cur.lastrowid

    def update(self, account_id, code, name, account_type, is_active):
        if self.db.conn.execute(
            "SELECT id FROM accounts WHERE code = ? AND id != ?", (code, account_id)
        ).fetchone():
            raise ValueError("کد حساب تکراری است")
        self.db.conn.execute(
            "UPDATE accounts SET code=?, name=?, account_type=?, is_active=? WHERE id=?",
            (code, name, account_type, 1 if is_active else 0, account_id),
        )
        self.db.conn.commit()

    def delete(self, account_id):
        if self.db.conn.execute(
            "SELECT id FROM journal_lines WHERE account_id = ?", (account_id,)
        ).fetchone():
            raise ValueError("این حساب در اسناد استفاده شده و قابل حذف نیست")
        if self.db.conn.execute(
            "SELECT id FROM accounts WHERE parent_id = ?", (account_id,)
        ).fetchone():
            raise ValueError("این حساب دارای زیرمجموعه است و قابل حذف نیست")
        self.db.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.db.conn.commit()

    @staticmethod
    def type_label(account_type):
        return ACCOUNT_TYPE_LABELS.get(account_type, account_type)

    @staticmethod
    def level_label(level):
        return LEVEL_LABELS.get(level, str(level))
