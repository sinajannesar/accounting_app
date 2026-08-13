"""گزارش دفتر معین"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QLabel, QHeaderView, QFileDialog, QFrame,
)

from ui.widgets import show_error, format_amount, DateRangeWidget, apply_shadow
from utils.export import export_to_excel, export_to_pdf


class LedgerWidget(QWidget):
    def __init__(self, report_model, account_model, level, title, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.account_model = account_model
        self.level = level
        self.title = title
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # wrap content in a content card for consistent look
        content_card = QFrame()
        content_card.setObjectName("contentCard")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)
        try:
            apply_shadow(content_card)
        except Exception:
            pass
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("حساب:"))
        self.account_combo = QComboBox()
        accounts = self.report_model.ledger_accounts(self.level)
        for acc in accounts:
            self.account_combo.addItem(f"{acc['code']} - {acc['name']}", acc["id"])
        filter_layout.addWidget(self.account_combo)
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        run_btn = QPushButton("🔍 نمایش گزارش")
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        content_layout.addLayout(filter_layout)

        export_layout = QHBoxLayout()
        excel_btn = QPushButton("📊 خروجی Excel")
        excel_btn.clicked.connect(lambda: self._export("excel"))
        pdf_btn = QPushButton("📄 خروجی PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addStretch()
        content_layout.addLayout(export_layout)

        self.info_label = QLabel("")
        self.info_label.setObjectName("sectionLabel")
        content_layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["تاریخ", "شماره سند", "شرح", "بدهکار", "بستانکار", "مانده"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(240)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        content_layout.addWidget(self.table)
        layout.addWidget(content_card)

        self._report_data = []

    def refresh(self):
        account_id = self.account_combo.currentData()
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError as e:
            show_error(self, str(e))
            return
        account, movements = self.report_model.subsidiary_ledger(account_id, d_from, d_to)
        if not account:
            return
        self.info_label.setText(f"{self.title}: {account['code']} - {account['name']}")
        self._report_data = movements
        self.table.setRowCount(len(movements))
        for row, m in enumerate(movements):
            self.table.setItem(row, 0, QTableWidgetItem(m["entry_date"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(m["entry_number"])))
            desc = m.get("line_description") or m.get("entry_description") or ""
            self.table.setItem(row, 2, QTableWidgetItem(desc))
            self.table.setItem(row, 3, QTableWidgetItem(format_amount(m["debit"])))
            self.table.setItem(row, 4, QTableWidgetItem(format_amount(m["credit"])))
            self.table.setItem(row, 5, QTableWidgetItem(format_amount(m["balance"])))
        # ensure wrapped descriptions are visible
        self.table.resizeRowsToContents()

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        account_label = self.account_combo.currentText()
        title = f"{self.title} - {account_label}"
        headers = ["تاریخ", "شماره سند", "شرح", "بدهکار", "بستانکار", "مانده"]
        rows = []
        for m in self._report_data:
            desc = m.get("line_description") or m.get("entry_description") or ""
            rows.append([
                m["entry_date"], m["entry_number"], desc,
                m["debit"], m["credit"], m["balance"],
            ])
        if fmt == "excel":
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره Excel", "", "Excel (*.xlsx)")
            if path:
                export_to_excel(path, title, headers, rows)
        else:
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره PDF", "", "PDF (*.pdf)")
            if path:
                export_to_pdf(path, title, headers, [
                    [str(c) for c in r[:3]] + [format_amount(r[3]), format_amount(r[4]), format_amount(r[5])]
                    for r in rows
                ])


class SubsidiaryLedgerWidget(LedgerWidget):
    """دفتر معین: فقط حساب‌های سطح ۳ انتخاب می‌شوند."""
    def __init__(self, report_model, account_model, parent=None):
        super().__init__(report_model, account_model, 3, "دفتر معین", parent)


class DetailLedgerWidget(LedgerWidget):
    """دفتر تفصیلی: فقط حساب‌های سطح ۴ انتخاب می‌شوند."""
    def __init__(self, report_model, account_model, parent=None):
        super().__init__(report_model, account_model, 4, "دفتر تفصیلی", parent)
