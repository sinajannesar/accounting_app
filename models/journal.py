"""مدل اسناد حسابداری"""

from datetime import datetime


class JournalModel:
    def __init__(self, db):
        self.db = db

    def next_entry_number(self):
        row = self.db.conn.execute("SELECT MAX(entry_number) AS mx FROM journal_entries").fetchone()
        return (row["mx"] or 0) + 1

    def get_entries(self, date_from=None, date_to=None, search="", due_only=False):
        query = """
            SELECT je.*,
                   COALESCE(SUM(jl.debit), 0) AS total_debit,
                   COALESCE(SUM(jl.credit), 0) AS total_credit
            FROM journal_entries je
            LEFT JOIN journal_lines jl ON je.id = jl.journal_entry_id
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND je.entry_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND je.entry_date <= ?"
            params.append(date_to)
        if search:
            query += " AND (je.description LIKE ? OR CAST(je.entry_number AS TEXT) LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if due_only:
            query += " AND je.due_date IS NOT NULL AND je.due_date != ''"
        query += " GROUP BY je.id ORDER BY je.entry_date DESC, je.entry_number DESC"
        rows = self.db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_entry(self, entry_id):
        entry = self.db.conn.execute(
            "SELECT * FROM journal_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if not entry:
            return None
        lines = self.db.conn.execute(
            """
            SELECT jl.*, a.code AS account_code, a.name AS account_name
            FROM journal_lines jl
            JOIN accounts a ON jl.account_id = a.id
            WHERE jl.journal_entry_id = ?
            ORDER BY jl.id
            """,
            (entry_id,),
        ).fetchall()
        result = dict(entry)
        result["lines"] = [dict(l) for l in lines]
        return result

    def create(self, entry_number, entry_date, due_date, description, lines):
        self._validate_lines(lines)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.conn.execute(
            """
            INSERT INTO journal_entries (entry_number, entry_date, due_date, description, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entry_number, entry_date, due_date or None, description, now),
        )
        entry_id = cur.lastrowid
        self._insert_lines(entry_id, lines)
        self.db.conn.commit()
        return entry_id

    def update(self, entry_id, entry_date, due_date, description, lines):
        self._validate_lines(lines)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.conn.execute(
            """
            UPDATE journal_entries
            SET entry_date=?, due_date=?, description=?, updated_at=?
            WHERE id=?
            """,
            (entry_date, due_date or None, description, now, entry_id),
        )
        self.db.conn.execute("DELETE FROM journal_lines WHERE journal_entry_id = ?", (entry_id,))
        self._insert_lines(entry_id, lines)
        self.db.conn.commit()

    def delete(self, entry_id):
        self.db.conn.execute("DELETE FROM journal_lines WHERE journal_entry_id = ?", (entry_id,))
        self.db.conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
        self.db.conn.commit()

    def _insert_lines(self, entry_id, lines):
        for line in lines:
            self.db.conn.execute(
                """
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, line_description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    line["account_id"],
                    float(line.get("debit", 0) or 0),
                    float(line.get("credit", 0) or 0),
                    line.get("line_description", ""),
                ),
            )

    def _validate_lines(self, lines):
        if len(lines) < 2:
            raise ValueError("هر سند باید حداقل دو سطر داشته باشد")
        total_debit = sum(float(l.get("debit", 0) or 0) for l in lines)
        total_credit = sum(float(l.get("credit", 0) or 0) for l in lines)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"جمع بدهکار ({total_debit:,.0f}) با بستانکار ({total_credit:,.0f}) برابر نیست")
        for line in lines:
            debit = float(line.get("debit", 0) or 0)
            credit = float(line.get("credit", 0) or 0)
            if debit > 0 and credit > 0:
                raise ValueError("هر سطر فقط می‌تواند بدهکار یا بستانکار داشته باشد")
            if debit == 0 and credit == 0:
                raise ValueError("مبلغ سطر نمی‌تواند صفر باشد")

    def get_due_entries(self, as_of_date=None):
        query = """
            SELECT je.*,
                   COALESCE(SUM(jl.debit), 0) AS total_debit,
                   COALESCE(SUM(jl.credit), 0) AS total_credit
            FROM journal_entries je
            LEFT JOIN journal_lines jl ON je.id = jl.journal_entry_id
            WHERE je.due_date IS NOT NULL AND je.due_date != ''
        """
        params = []
        if as_of_date:
            query += " AND je.due_date <= ?"
            params.append(as_of_date)
        query += " GROUP BY je.id ORDER BY je.due_date ASC"
        rows = self.db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_cash_balance(self, cash_account_id, date_to=None):
        query = """
            SELECT
                COALESCE(SUM(jl.debit), 0) - COALESCE(SUM(jl.credit), 0) AS balance
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE jl.account_id = ?
        """
        params = [cash_account_id]
        if date_to:
            query += " AND je.entry_date <= ?"
            params.append(date_to)
        row = self.db.conn.execute(query, params).fetchone()
        return row["balance"] if row else 0

    def get_cash_transactions(self, cash_account_id, date_from=None, date_to=None):
        query = """
            SELECT je.id AS entry_id, je.entry_date, je.entry_number, je.description,
                   jl.debit, jl.credit, jl.line_description
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE jl.account_id = ?
        """
        params = [cash_account_id]
        if date_from:
            query += " AND je.entry_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND je.entry_date <= ?"
            params.append(date_to)
        query += " ORDER BY je.entry_date, je.entry_number"
        rows = self.db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def create_cash_transaction(self, cash_account_id, counter_account_id, entry_date, amount, is_income, description):
        """ثبت سریع ورود/خروج صندوق"""
        entry_number = self.next_entry_number()
        if is_income:
            lines = [
                {"account_id": cash_account_id, "debit": amount, "credit": 0, "line_description": description},
                {"account_id": counter_account_id, "debit": 0, "credit": amount, "line_description": description},
            ]
        else:
            lines = [
                {"account_id": counter_account_id, "debit": amount, "credit": 0, "line_description": description},
                {"account_id": cash_account_id, "debit": 0, "credit": amount, "line_description": description},
            ]
        return self.create(entry_number, entry_date, None, description or "تراکنش صندوق", lines)