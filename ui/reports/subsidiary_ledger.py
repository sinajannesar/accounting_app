"""گزارش دفتر معین"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QLabel, QHeaderView, QFileDialog,
)

from ui.widgets import show_error, format_amount, DateRangeWidget
from utils.export import export_to_excel, export_to_pdf


class SubsidiaryLedgerWidget(QWidget):
    def __init__(self, report_model, account_model, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.account_model = account_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("حساب:"))
        self.account_combo = QComboBox()
        accounts = self.account_model.get_postable_accounts()
        for acc in accounts:
            self.account_combo.addItem(f"{acc['code']} - {acc['name']}", acc["id"])
        filter_layout.addWidget(self.account_combo)
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        run_btn = QPushButton("🔍 نمایش گزارش")
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        layout.addLayout(filter_layout)

        export_layout = QHBoxLayout()
        excel_btn = QPushButton("📊 خروجی Excel")
        excel_btn.clicked.connect(lambda: self._export("excel"))
        pdf_btn = QPushButton("📄 خروجی PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.info_label = QLabel("")
        self.info_label.setObjectName("titleLabel")
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["تاریخ", "شماره سند", "شرح", "بدهکار", "بستانکار", "مانده"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

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
        self.info_label.setText(f"دفتر معین: {account['code']} - {account['name']}")
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

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        account_label = self.account_combo.currentText()
        title = f"دفتر معین - {account_label}"
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