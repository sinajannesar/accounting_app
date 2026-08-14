"""ماژول صندوق"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QFormLayout, QGroupBox, QLabel,
    QHeaderView, QLineEdit, QDialog, QFileDialog,
)

from models.journal import JournalModel
from models.account import AccountModel
from ui.widgets import show_error, show_info, format_amount, DateRangeWidget, AmountInput
from utils.jalali import JalaliDateEdit, today_jalali
from utils.export import export_receipt_pdf


class CashTransactionDialog(QDialog):
    def __init__(self, journal_model, account_model, cash_account_id, is_income=None, parent=None):
        super().__init__(parent)
        self.journal_model = journal_model
        self.cash_account_id = cash_account_id
        self.is_income = is_income
        self.setWindowTitle("تراکنش صندوق")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui(account_model)

    def _build_ui(self, account_model):
        layout = QFormLayout(self)
        self.type_combo = QComboBox()
        self.type_combo.addItem("ورود وجه (دریافت)", True)
        self.type_combo.addItem("خروج وجه (پرداخت)", False)
        if self.is_income is not None:
            self.type_combo.setCurrentIndex(0 if self.is_income else 1)
        self.date_edit = JalaliDateEdit()
        self.date_edit.set_date(today_jalali())
        self.amount_spin = AmountInput(minimum=1)
        self.counter_combo = QComboBox()
        accounts = account_model.get_postable_accounts()
        for acc in accounts:
            if acc["id"] != self.cash_account_id:
                self.counter_combo.addItem(f"{acc['code']} - {acc['name']}", acc["id"])
        self.desc_edit = QLineEdit()

        layout.addRow("نوع:", self.type_combo)
        layout.addRow("تاریخ:", self.date_edit)
        layout.addRow("مبلغ:", self.amount_spin)
        layout.addRow("حساب طرف:", self.counter_combo)
        layout.addRow("شرح:", self.desc_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("✔ ثبت")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _save(self):
        try:
            amount = self.amount_spin.value()
            if amount <= 0:
                raise ValueError("مبلغ باید بیشتر از صفر باشد")
            entry_date = self.date_edit.get_date()
            is_income = self.type_combo.currentData()
            counter_id = self.counter_combo.currentData()
            description = self.desc_edit.text().strip()
            self.journal_model.create_cash_transaction(
                self.cash_account_id, counter_id, entry_date, amount, is_income, description
            )
            self.accept()
        except ValueError as e:
            show_error(self, str(e))


class CashWidget(QWidget):
    def __init__(self, db, journal_model, account_model, parent=None):
        super().__init__(parent)
        self.db = db
        self.journal_model = journal_model
        self.account_model = account_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self.refresh()

    def _get_cash_account_id(self):
        cash_id = self.db.get_setting("cash_account_id")
        if cash_id:
            return int(cash_id)
        return None

    def _build_ui(self):
        layout = QVBoxLayout(self)

        balance_group = QGroupBox("موجودی صندوق")
        balance_layout = QHBoxLayout(balance_group)
        self.balance_label = QLabel("0")
        self.balance_label.setObjectName("balanceLabel")
        balance_layout.addWidget(QLabel("موجودی لحظه‌ای:"))
        balance_layout.addWidget(self.balance_label)
        balance_layout.addStretch()
        layout.addWidget(balance_group)

        self.date_range = DateRangeWidget()
        layout.addWidget(self.date_range)

        btn_layout = QHBoxLayout()
        in_btn = QPushButton("⬆ ورود وجه")
        in_btn.setObjectName("successBtn")
        in_btn.clicked.connect(lambda: self._add_transaction(True))
        out_btn = QPushButton("⬇ خروج وجه")
        out_btn.setObjectName("dangerBtn")
        out_btn.clicked.connect(lambda: self._add_transaction(False))
        refresh_btn = QPushButton("  بروزرسانی")
        refresh_icon = os.path.join(os.path.dirname(__file__), "icons", "refresh.svg")
        if os.path.exists(refresh_icon):
            refresh_btn.setIcon(QIcon(refresh_icon))
        refresh_btn.clicked.connect(self.refresh)
        print_btn = QPushButton("🖨 چاپ رسید")
        print_btn.clicked.connect(self._print_receipt)
        btn_layout.addWidget(in_btn)
        btn_layout.addWidget(out_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(print_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["تاریخ", "شماره سند", "شرح", "ورود", "خروج", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

    def refresh(self):
        cash_id = self._get_cash_account_id()
        if not cash_id:
            show_error(self, "حساب صندوق تعریف نشده است")
            return
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError:
            d_from, d_to = None, None

        balance = self.journal_model.get_cash_balance(cash_id, d_to)
        self.balance_label.setText(format_amount(balance) + " ریال")

        transactions = self.journal_model.get_cash_transactions(cash_id, d_from, d_to)
        self.table.setRowCount(len(transactions))
        for row, tx in enumerate(transactions):
            self.table.setItem(row, 0, QTableWidgetItem(tx["entry_date"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(tx["entry_number"])))
            desc = tx.get("line_description") or tx.get("description") or ""
            self.table.setItem(row, 2, QTableWidgetItem(desc))
            self.table.setItem(row, 3, QTableWidgetItem(format_amount(tx["debit"])))
            self.table.setItem(row, 4, QTableWidgetItem(format_amount(tx["credit"])))
            id_item = QTableWidgetItem("")
            id_item.setData(Qt.UserRole, tx["entry_id"])
            self.table.setItem(row, 5, id_item)

    def _print_receipt(self):
        row = self.table.currentRow()
        if row < 0:
            show_error(self, "لطفاً یک تراکنش را از جدول انتخاب کنید")
            return
        entry_id = self.table.item(row, 5).data(Qt.UserRole)
        entry = self.journal_model.get_entry(entry_id)
        if not entry:
            show_error(self, "سند یافت نشد")
            return
        default_name = f"فیش صندوق {entry['entry_number']}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "چاپ رسید", default_name, "PDF (*.pdf)")
        if not path:
            return
        try:
            export_receipt_pdf(path, entry)
            show_info(self, f"رسید با موفقیت ذخیره شد:\n{path}")
        except Exception as e:
            show_error(self, f"خطا در ساخت رسید: {e}")

    def _add_transaction(self, is_income=None):
        cash_id = self._get_cash_account_id()
        if not cash_id:
            show_error(self, "حساب صندوق تعریف نشده است")
            return
        dlg = CashTransactionDialog(self.journal_model, self.account_model, cash_id, is_income, parent=self)
        if dlg.exec_():
            self.refresh()
            show_info(self, "تراکنش با موفقیت ثبت شد")
