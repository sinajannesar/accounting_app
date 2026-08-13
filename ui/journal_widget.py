# ui/journal_widget.py — FULL FILE, replace entirely
"""ماژول ثبت اسناد حسابداری"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QDialog, QFormLayout, QComboBox,
    QLabel, QHeaderView, QTextEdit, QTabWidget,
    QGroupBox, QFileDialog,
)

from models.journal import JournalModel
from models.account import AccountModel
from ui.widgets import show_error, show_info, show_confirm, format_amount, DateRangeWidget, AmountInput
from ui.styles import COLOR_DANGER, COLOR_DANGER_LIGHT, COLOR_SUCCESS_DARK, COLOR_SUCCESS_LIGHT
from utils.jalali import JalaliDateEdit, today_jalali
from utils.export import export_receipt_pdf


class JournalLineDialog(QDialog):
    def __init__(self, accounts, line=None, parent=None):
        super().__init__(parent)
        self.accounts = accounts
        self.line = line
        self.setWindowTitle("سطر سند")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        if line:
            self._load_line()

    def _build_ui(self):
        layout = QFormLayout(self)
        self.group_combo = QComboBox()
        self.group_combo.addItem("همه گروه‌ها", None)
        roots = {}
        for acc in self.accounts:
            roots.setdefault(acc["account_type"], AccountModel.type_label(acc["account_type"]))
        for key, label in roots.items():
            self.group_combo.addItem(label, key)
        self.account_combo = QComboBox()
        self.debit_spin = AmountInput()
        self.credit_spin = AmountInput()
        self.desc_edit = QLineEdit()

        layout.addRow("گروه حساب:", self.group_combo)
        layout.addRow("حساب قابل ثبت:", self.account_combo)
        layout.addRow("بدهکار:", self.debit_spin)
        layout.addRow("بستانکار:", self.credit_spin)
        layout.addRow("شرح:", self.desc_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("✔ تأیید")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        self.group_combo.currentIndexChanged.connect(self._fill_accounts)
        self._fill_accounts()

    def _fill_accounts(self):
        selected = self.account_combo.currentData()
        group = self.group_combo.currentData()
        self.account_combo.clear()
        for acc in self.accounts:
            if not group or acc["account_type"] == group:
                self.account_combo.addItem(f"{acc['code']} — {acc['name']} ({AccountModel.level_label(acc['level'])})", acc["id"])
        index = self.account_combo.findData(selected)
        if index >= 0:
            self.account_combo.setCurrentIndex(index)

    def _load_line(self):
        current = next((a for a in self.accounts if a["id"] == self.line["account_id"]), None)
        if current:
            self.group_combo.setCurrentIndex(self.group_combo.findData(current["account_type"]))
        idx = self.account_combo.findData(self.line["account_id"])
        if idx >= 0:
            self.account_combo.setCurrentIndex(idx)
        self.debit_spin.setValue(self.line.get("debit", 0))
        self.credit_spin.setValue(self.line.get("credit", 0))
        self.desc_edit.setText(self.line.get("line_description", ""))

    def get_line(self):
        debit = self.debit_spin.value()
        credit = self.credit_spin.value()
        if debit > 0 and credit > 0:
            raise ValueError("فقط یکی از بدهکار یا بستانکار را پر کنید")
        if debit == 0 and credit == 0:
            raise ValueError("مبلغ نمی‌تواند صفر باشد")
        return {
            "account_id": self.account_combo.currentData(),
            "debit": debit,
            "credit": credit,
            "line_description": self.desc_edit.text().strip(),
        }


class JournalEntryDialog(QDialog):
    def __init__(self, journal_model, account_model, entry=None, parent=None):
        super().__init__(parent)
        self.journal_model = journal_model
        self.account_model = account_model
        self.entry = entry
        self.lines = []
        self.setWindowTitle("ویرایش سند" if entry else "سند جدید")
        self.setMinimumSize(700, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        if entry:
            self._load_entry()
        else:
            self.number_edit.setText(str(journal_model.next_entry_number()))
            self.date_edit.set_date(today_jalali())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.number_edit = QLineEdit()
        self.number_edit.setReadOnly(True)
        self.date_edit = JalaliDateEdit()
        self.due_date_edit = JalaliDateEdit(default_today=False)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)

        form.addRow("شماره سند:", self.number_edit)
        form.addRow("تاریخ:", self.date_edit)
        form.addRow("سررسید:", self.due_date_edit)
        form.addRow("شرح:", self.desc_edit)
        layout.addLayout(form)

        lines_group = QGroupBox("سطرهای سند")
        lines_layout = QVBoxLayout(lines_group)
        line_btns = QHBoxLayout()
        add_line_btn = QPushButton("➕ افزودن سطر")
        add_line_btn.clicked.connect(self._add_line)
        edit_line_btn = QPushButton("✏ ویرایش سطر")
        edit_line_btn.clicked.connect(self._edit_line)
        del_line_btn = QPushButton("🗑 حذف سطر")
        del_line_btn.setObjectName("dangerBtn")
        del_line_btn.clicked.connect(self._delete_line)
        line_btns.addWidget(add_line_btn)
        line_btns.addWidget(edit_line_btn)
        line_btns.addWidget(del_line_btn)
        lines_layout.addLayout(line_btns)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels(["حساب", "بدهکار", "بستانکار", "شرح", ""])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.setSelectionBehavior(QTableWidget.SelectRows)
        lines_layout.addWidget(self.lines_table)

        self.totals_label = QLabel("جمع بدهکار: 0 | جمع بستانکار: 0")
        lines_layout.addWidget(self.totals_label)
        layout.addWidget(lines_group)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("✔ ذخیره سند")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_entry(self):
        self.number_edit.setText(str(self.entry["entry_number"]))
        self.date_edit.set_date(self.entry["entry_date"])
        if self.entry.get("due_date"):
            self.due_date_edit.set_date(self.entry["due_date"])
        else:
            self.due_date_edit.clear()
        self.desc_edit.setPlainText(self.entry.get("description", ""))
        self.lines = list(self.entry.get("lines", []))
        self._refresh_lines_table()

    def _refresh_lines_table(self):
        # برای نمایش اسناد قدیمی، حتی حساب‌های قدیمیِ غیرقابل انتخاب نیز خوانده می‌شوند.
        accounts = {a["id"]: a for a in self.account_model.get_all(active_only=False)}
        self.lines_table.setRowCount(len(self.lines))
        total_d = total_c = 0
        for row, line in enumerate(self.lines):
            acc = accounts.get(line["account_id"], {})
            acc_label = f"{acc.get('code', '')} - {acc.get('name', '')}"
            self.lines_table.setItem(row, 0, QTableWidgetItem(acc_label))
            self.lines_table.setItem(row, 1, QTableWidgetItem(format_amount(line["debit"])))
            self.lines_table.setItem(row, 2, QTableWidgetItem(format_amount(line["credit"])))
            self.lines_table.setItem(row, 3, QTableWidgetItem(line.get("line_description", "")))
            total_d += line["debit"]
            total_c += line["credit"]
        self.totals_label.setText(
            f"جمع بدهکار: {format_amount(total_d)} | جمع بستانکار: {format_amount(total_c)}"
        )
        diff = total_d - total_c
        if abs(diff) > 0.01:
            self.totals_label.setStyleSheet(
                f"color: {COLOR_DANGER}; font-weight: 700; background-color: {COLOR_DANGER_LIGHT}; "
                f"border-radius: 6px; padding: 6px 10px;"
            )
        else:
            self.totals_label.setStyleSheet(
                f"color: {COLOR_SUCCESS_DARK}; font-weight: 700; background-color: {COLOR_SUCCESS_LIGHT}; "
                f"border-radius: 6px; padding: 6px 10px;"
            )

    def _add_line(self):
        accounts = self.account_model.get_postable_accounts()
        dlg = JournalLineDialog(accounts, parent=self)
        if dlg.exec_():
            try:
                self.lines.append(dlg.get_line())
                self._refresh_lines_table()
            except ValueError as e:
                show_error(self, str(e))

    def _edit_line(self):
        row = self.lines_table.currentRow()
        if row < 0:
            show_error(self, "یک سطر انتخاب کنید")
            return
        accounts = self.account_model.get_postable_accounts()
        dlg = JournalLineDialog(accounts, self.lines[row], parent=self)
        if dlg.exec_():
            try:
                self.lines[row] = dlg.get_line()
                self._refresh_lines_table()
            except ValueError as e:
                show_error(self, str(e))

    def _delete_line(self):
        row = self.lines_table.currentRow()
        if row >= 0:
            del self.lines[row]
            self._refresh_lines_table()

    def _save(self):
        try:
            entry_date = self.date_edit.get_date()
            try:
                due_date = self.due_date_edit.get_date()
            except ValueError:
                due_date = ""
            description = self.desc_edit.toPlainText().strip()
            if self.entry:
                self.journal_model.update(
                    self.entry["id"], entry_date, due_date, description, self.lines
                )
            else:
                self.journal_model.create(
                    int(self.number_edit.text()), entry_date, due_date, description, self.lines
                )
            self.accept()
        except ValueError as e:
            show_error(self, str(e))


class JournalWidget(QWidget):
    def __init__(self, journal_model, account_model, parent=None):
        super().__init__(parent)
        self.journal_model = journal_model
        self.account_model = account_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        filter_layout = QHBoxLayout()
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو بر اساس شماره یا شرح سند...")
        filter_layout.addWidget(self.search_edit)
        search_btn = QPushButton("🔍 جستجو")
        search_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(search_btn)
        all_layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ سند جدید")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add_entry)
        edit_btn = QPushButton("✏ ویرایش سند")
        edit_btn.clicked.connect(self._edit_entry)
        delete_btn = QPushButton("🗑 حذف سند")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self._delete_entry)
        print_btn = QPushButton("🖨 چاپ رسید")
        print_btn.clicked.connect(self._print_receipt)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addStretch()
        all_layout.addLayout(btn_layout)

        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(6)
        self.entries_table.setHorizontalHeaderLabels(
            ["شماره سند", "تاریخ", "سررسید", "شرح", "جمع بدهکار", "جمع بستانکار"]
        )
        self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.doubleClicked.connect(self._edit_entry)
        all_layout.addWidget(self.entries_table)

        self.tabs.addTab(all_tab, "همه اسناد")

        due_tab = QWidget()
        due_layout = QVBoxLayout(due_tab)
        due_refresh_btn = QPushButton("🔄 بروزرسانی")
        due_refresh_btn.clicked.connect(self._refresh_due)
        due_layout.addWidget(due_refresh_btn)
        self.due_table = QTableWidget()
        self.due_table.setColumnCount(4)
        self.due_table.setHorizontalHeaderLabels(["شماره سند", "تاریخ", "سررسید", "شرح"])
        self.due_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.due_table.setAlternatingRowColors(True)
        due_layout.addWidget(self.due_table)
        self.tabs.addTab(due_tab, "اسناد سررسید شده")

        layout.addWidget(self.tabs)
        self._entries = []
        self._due_entries = []

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError:
            d_from, d_to = None, None
        search = self.search_edit.text().strip()
        self._entries = self.journal_model.get_entries(d_from, d_to, search)

        self.entries_table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            self.entries_table.setItem(row, 0, QTableWidgetItem(str(entry["entry_number"])))
            self.entries_table.setItem(row, 1, QTableWidgetItem(entry["entry_date"]))
            self.entries_table.setItem(row, 2, QTableWidgetItem(entry.get("due_date") or ""))
            self.entries_table.setItem(row, 3, QTableWidgetItem(entry.get("description") or ""))
            self.entries_table.setItem(row, 4, QTableWidgetItem(format_amount(entry["total_debit"])))
            self.entries_table.setItem(row, 5, QTableWidgetItem(format_amount(entry["total_credit"])))

        self._refresh_due()

    def _refresh_due(self):
        self._due_entries = self.journal_model.get_due_entries()
        self.due_table.setRowCount(len(self._due_entries))
        for row, entry in enumerate(self._due_entries):
            self.due_table.setItem(row, 0, QTableWidgetItem(str(entry["entry_number"])))
            self.due_table.setItem(row, 1, QTableWidgetItem(entry["entry_date"]))
            self.due_table.setItem(row, 2, QTableWidgetItem(entry.get("due_date") or ""))
            self.due_table.setItem(row, 3, QTableWidgetItem(entry.get("description") or ""))

    def _selected_entry(self):
        row = self.entries_table.currentRow()
        if row < 0 or row >= len(self._entries):
            return None
        return self._entries[row]

    def _add_entry(self):
        dlg = JournalEntryDialog(self.journal_model, self.account_model, parent=self)
        if dlg.exec_():
            self.refresh()

    def _edit_entry(self):
        selected = self._selected_entry()
        if not selected:
            show_error(self, "یک سند را انتخاب کنید")
            return
        full_entry = self.journal_model.get_entry(selected["id"])
        dlg = JournalEntryDialog(self.journal_model, self.account_model, entry=full_entry, parent=self)
        if dlg.exec_():
            self.refresh()

    def _delete_entry(self):
        selected = self._selected_entry()
        if not selected:
            show_error(self, "یک سند را انتخاب کنید")
            return
        if show_confirm(self, f"آیا از حذف سند شماره {selected['entry_number']} مطمئن هستید؟"):
            self.journal_model.delete(selected["id"])
            self.refresh()

    def _print_receipt(self):
        selected = self._selected_entry()
        if not selected:
            show_error(self, "یک سند را انتخاب کنید")
            return
        full_entry = self.journal_model.get_entry(selected["id"])
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره رسید", "", "PDF (*.pdf)")
        if path:
            export_receipt_pdf(path, full_entry)
            show_info(self, "رسید با موفقیت ذخیره شد")