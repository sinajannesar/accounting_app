"""مدل گزارش‌های حسابداری"""


class ReportModel:
    def __init__(self, db, account_model):
        self.db = db
        self.account_model = account_model

    def _account_ids_for_level(self, level_filter=None):
        if level_filter:
            rows = self.db.conn.execute(
                "SELECT id FROM accounts WHERE level = ? AND is_active = 1", (level_filter,)
            ).fetchall()
            return [r["id"] for r in rows]
        return None

    def _get_account_movements(self, account_ids, date_from=None, date_to=None):
        if not account_ids:
            return []
        placeholders = ",".join("?" * len(account_ids))
        query = f"""
            SELECT je.entry_date, je.entry_number, je.description AS entry_description,
                   jl.debit, jl.credit, jl.line_description,
                   a.id AS account_id, a.code AS account_code, a.name AS account_name,
                   a.account_type
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE jl.account_id IN ({placeholders})
        """
        params = list(account_ids)
        if date_from:
            query += " AND je.entry_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND je.entry_date <= ?"
            params.append(date_to)
        query += " ORDER BY je.entry_date, je.entry_number, jl.id"
        rows = self.db.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def subsidiary_ledger(self, account_id, date_from=None, date_to=None):
        account = self.account_model.get_by_id(account_id)
        if not account:
            return None, []
        account_ids = self.account_model.get_children_ids(account_id)
        movements = self._get_account_movements(account_ids, date_from, date_to)

        balance = 0
        running = []
        for m in movements:
            balance += m["debit"] - m["credit"]
            running.append({**m, "balance": balance})
        return account, running

    def general_ledger(self, date_from=None, date_to=None):
        accounts = self.db.conn.execute(
            "SELECT * FROM accounts WHERE level = 2 AND is_active = 1 ORDER BY code"
        ).fetchall()
        result = []
        for acc in accounts:
            acc_dict = dict(acc)
            child_ids = self.account_model.get_children_ids(acc["id"])
            movements = self._get_account_movements(child_ids, date_from, date_to)
            total_debit = sum(m["debit"] for m in movements)
            total_credit = sum(m["credit"] for m in movements)
            balance = total_debit - total_credit
            if movements or balance != 0:
                result.append({
                    **acc_dict,
                    "total_debit": total_debit,
                    "total_credit": total_credit,
                    "balance": balance,
                    "movements": movements,
                })
        return result

    def trial_balance(self, date_from=None, date_to=None, eight_column=False):
        accounts = self.db.conn.execute(
            "SELECT * FROM accounts WHERE level >= 3 AND is_active = 1 ORDER BY code"
        ).fetchall()
        rows = []
        total_debit = total_credit = 0
        total_debit_balance = total_credit_balance = 0

        for acc in accounts:
            acc_dict = dict(acc)
            child_ids = self.account_model.get_children_ids(acc["id"])
            movements = self._get_account_movements(child_ids, date_from, date_to)
            period_debit = sum(m["debit"] for m in movements)
            period_credit = sum(m["credit"] for m in movements)
            balance = period_debit - period_credit

            if period_debit == 0 and period_credit == 0:
                continue

            debit_balance = balance if balance > 0 else 0
            credit_balance = -balance if balance < 0 else 0

            rows.append({
                **acc_dict,
                "period_debit": period_debit,
                "period_credit": period_credit,
                "debit_balance": debit_balance,
                "credit_balance": credit_balance,
            })
            total_debit += period_debit
            total_credit += period_credit
            total_debit_balance += debit_balance
            total_credit_balance += credit_balance

        return {
            "rows": rows,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "total_debit_balance": total_debit_balance,
            "total_credit_balance": total_credit_balance,
            "eight_column": eight_column,
        }

    def income_statement(self, date_from=None, date_to=None):
        income_accounts = self.db.conn.execute(
            "SELECT * FROM accounts WHERE account_type = 'income' AND level >= 3 AND is_active = 1 ORDER BY code"
        ).fetchall()
        expense_accounts = self.db.conn.execute(
            "SELECT * FROM accounts WHERE account_type = 'expense' AND level >= 3 AND is_active = 1 ORDER BY code"
        ).fetchall()

        def calc_total(accounts):
            items = []
            grand = 0
            for acc in accounts:
                child_ids = self.account_model.get_children_ids(acc["id"])
                movements = self._get_account_movements(child_ids, date_from, date_to)
                total = sum(m["credit"] - m["debit"] for m in movements)
                if total != 0:
                    items.append({**dict(acc), "amount": total})
                    grand += total
            return items, grand

        income_items, total_income = calc_total(income_accounts)
        expense_items, total_expense = calc_total(expense_accounts)
        # هزینه‌ها بدهکار هستند، مقدار مثبت نشان‌دهنده هزینه
        total_expense = abs(total_expense)
        for item in expense_items:
            item["amount"] = abs(item["amount"])

        net_profit = total_income - total_expense
        return {
            "income_items": income_items,
            "expense_items": expense_items,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": net_profit,
        }
