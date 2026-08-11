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
        self.account_combo = QComboBox()
        for acc in self.accounts:
            self.account_combo.addItem(f"{acc['code']} - {acc['name']}", acc["id"])
        self.debit_spin = AmountInput()
        self.credit_spin = AmountInput()
        self.desc_edit = QLineEdit()

        layout.addRow("حساب:", self.account_combo)
        layout.addRow("بدهکار:", self.debit_spin)
        layout.addRow("بستانکار:", self.credit_spin)
        layout.addRow("شرح:", self.desc_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("تأیید")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _load_line(self):
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
        add_line_btn = QPushButton("افزودن سطر")
        add_line_btn.clicked.connect(self._add_line)
        edit_line_btn = QPushButton("ویرایش سطر")
        edit_line_btn.clicked.connect(self._edit_line)
        del_line_btn = QPushButton("حذف سطر")
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
        save_btn = QPushButton("ذخیره سند")
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
        accounts = {a["id"]: a for a in self.account_model.get_postable_accounts()}
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
            self.totals_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.totals_label.setStyleSheet("color: green; font-weight: bold;")

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
        tabs = QTabWidget()

        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        filter_layout = QHBoxLayout()
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو...")
        self.search_edit.textChanged.connect(self.refresh)
        filter_layout.addWidget(self.search_edit)
        refresh_btn = QPushButton("بروزرسانی")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)
        all_layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("سند جدید")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("ویرایش")
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("حذف")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete)
        print_btn = QPushButton("چاپ رسید")
        print_btn.clicked.connect(self._print_receipt)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(print_btn)
        all_layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "شماره", "تاریخ", "سررسید", "شرح", "بدهکار", "بستانکار", "",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self._edit)
        all_layout.addWidget(self.table)
        tabs.addTab(all_tab, "همه اسناد")

        due_tab = QWidget()
        due_layout = QVBoxLayout(due_tab)
        self.due_table = QTableWidget()
        self.due_table.setColumnCount(6)
        self.due_table.setHorizontalHeaderLabels([
            "شماره", "تاریخ", "سررسید", "شرح", "مبلغ", "",
        ])
        self.due_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.due_table.setAlternatingRowColors(True)
        due_layout.addWidget(self.due_table)
        tabs.addTab(due_tab, "اسناد سررسیددار")

        layout.addWidget(tabs)

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError:
            d_from, d_to = None, None
        search = self.search_edit.text().strip()
        entries = self.journal_model.get_entries(d_from, d_to, search)
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(str(entry["entry_number"])))
            self.table.setItem(row, 1, QTableWidgetItem(entry["entry_date"]))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("due_date") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(entry.get("description") or ""))
            self.table.setItem(row, 4, QTableWidgetItem(format_amount(entry["total_debit"])))
            self.table.setItem(row, 5, QTableWidgetItem(format_amount(entry["total_credit"])))
            id_item = QTableWidgetItem("")
            id_item.setData(Qt.UserRole, entry["id"])
            self.table.setItem(row, 6, id_item)

        due_entries = self.journal_model.get_due_entries(d_to)
        self.due_table.setRowCount(len(due_entries))
        for row, entry in enumerate(due_entries):
            self.due_table.setItem(row, 0, QTableWidgetItem(str(entry["entry_number"])))
            self.due_table.setItem(row, 1, QTableWidgetItem(entry["entry_date"]))
            self.due_table.setItem(row, 2, QTableWidgetItem(entry.get("due_date") or ""))
            self.due_table.setItem(row, 3, QTableWidgetItem(entry.get("description") or ""))
            self.due_table.setItem(row, 4, QTableWidgetItem(format_amount(entry["total_debit"])))
            id_item = QTableWidgetItem("")
            id_item.setData(Qt.UserRole, entry["id"])
            self.due_table.setItem(row, 5, id_item)

    def _selected_id(self):
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 6).data(Qt.UserRole)
        return None

    def _add(self):
        dlg = JournalEntryDialog(self.journal_model, self.account_model, parent=self)
        if dlg.exec_():
            self.refresh()
            show_info(self, "سند با موفقیت ثبت شد")

    def _edit(self):
        entry_id = self._selected_id()
        if not entry_id:
            show_error(self, "لطفاً یک سند انتخاب کنید")
            return
        entry = self.journal_model.get_entry(entry_id)
        dlg = JournalEntryDialog(self.journal_model, self.account_model, entry, parent=self)
        if dlg.exec_():
            self.refresh()
            show_info(self, "سند با موفقیت ویرایش شد")

    def _delete(self):
        entry_id = self._selected_id()
        if not entry_id:
            show_error(self, "لطفاً یک سند انتخاب کنید")
            return
        if not show_confirm(self, "آیا از حذف این سند اطمینان دارید؟"):
            return
        self.journal_model.delete(entry_id)
        self.refresh()
        show_info(self, "سند حذف شد")

    def _print_receipt(self):
        entry_id = self._selected_id()
        if not entry_id:
            show_error(self, "لطفاً یک سند انتخاب کنید")
            return
        entry = self.journal_model.get_entry(entry_id)
        if not entry:
            show_error(self, "سند یافت نشد")
            return
        default_name = f"رسید سند {entry['entry_number']}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "چاپ رسید", default_name, "PDF (*.pdf)")
        if not path:
            return
        try:
            export_receipt_pdf(path, entry)
            show_info(self, f"رسید با موفقیت ذخیره شد:\n{path}")
        except Exception as e:
            show_error(self, f"خطا در ساخت رسید: {e}")
