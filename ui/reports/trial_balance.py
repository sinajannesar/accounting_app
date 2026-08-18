"""گزارش تراز آزمایشی"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QFrame,
)

from ui.widgets import show_error, format_amount, DateRangeWidget, apply_shadow
from utils.export import export_to_excel, export_to_pdf


class TrialBalanceWidget(QWidget):
    def __init__(self, report_model, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # content card to match app visual
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
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        self.eight_col_check = QCheckBox("تراز هشت‌ستونی")
        filter_layout.addWidget(self.eight_col_check)
        run_btn = QPushButton("🔍 نمایش گزارش")
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        content_layout.addLayout(filter_layout)

        export_layout = QHBoxLayout()
        excel_btn = QPushButton("  خروجی Excel")
        excel_icon = os.path.join(os.path.dirname(__file__), "..", "icons", "report.svg")
        excel_icon = os.path.normpath(excel_icon)
        if os.path.exists(excel_icon):
            excel_btn.setIcon(QIcon(excel_icon))
        excel_btn.clicked.connect(lambda: self._export("excel"))
        pdf_btn = QPushButton("📄 خروجی PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addStretch()
        content_layout.addLayout(export_layout)

        self.table = QTableWidget()
        # Do not set per-section resize modes here because column count
        # is not known yet; resize modes are applied after columns are set
        # in `refresh()` where we call `setSectionResizeMode` safely.
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        content_layout.addWidget(self.table)
        layout.addWidget(content_card)
        self._report_data = None

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError as e:
            show_error(self, str(e))
            return
        eight = self.eight_col_check.isChecked()
        data = self.report_model.trial_balance(d_from, d_to, eight)
        self._report_data = data

        if eight:
            headers = ["کد", "نام", "گردش بدهکار", "گردش بستانکار", "مانده بدهکار", "مانده بستانکار"]
            self.table.setColumnCount(6)
        else:
            headers = ["کد", "نام", "بدهکار", "بستانکار", "مانده"]
            self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(headers)
        rows = data["rows"]
        self.table.setRowCount(len(rows) + 1)

        for row_idx, item in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item["code"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            if eight:
                self.table.setItem(row_idx, 2, QTableWidgetItem(format_amount(item["period_debit"])))
                self.table.setItem(row_idx, 3, QTableWidgetItem(format_amount(item["period_credit"])))
                self.table.setItem(row_idx, 4, QTableWidgetItem(format_amount(item["debit_balance"])))
                self.table.setItem(row_idx, 5, QTableWidgetItem(format_amount(item["credit_balance"])))
            else:
                self.table.setItem(row_idx, 2, QTableWidgetItem(format_amount(item["period_debit"])))
                self.table.setItem(row_idx, 3, QTableWidgetItem(format_amount(item["period_credit"])))
                balance = item["debit_balance"] - item["credit_balance"]
                self.table.setItem(row_idx, 4, QTableWidgetItem(format_amount(balance)))

        total_row = len(rows)
        self.table.setItem(total_row, 0, QTableWidgetItem(""))
        self.table.setItem(total_row, 1, QTableWidgetItem("جمع کل"))
        if eight:
            self.table.setItem(total_row, 2, QTableWidgetItem(format_amount(data["total_debit"])))
            self.table.setItem(total_row, 3, QTableWidgetItem(format_amount(data["total_credit"])))
            self.table.setItem(total_row, 4, QTableWidgetItem(format_amount(data["total_debit_balance"])))
            self.table.setItem(total_row, 5, QTableWidgetItem(format_amount(data["total_credit_balance"])))
        else:
            self.table.setItem(total_row, 2, QTableWidgetItem(format_amount(data["total_debit"])))
            self.table.setItem(total_row, 3, QTableWidgetItem(format_amount(data["total_credit"])))
            self.table.setItem(total_row, 4, QTableWidgetItem(""))
        # After columns are set, adjust resize modes: code narrow, name stretch, numbers resize to contents
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in range(2, self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        # ensure wrapping and no elide
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        # resize rows so multi-line names are shown
        self.table.resizeRowsToContents()

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        eight = self.eight_col_check.isChecked()
        title = "تراز آزمایشی"
        data = self._report_data
        if eight:
            headers = ["کد", "نام", "گردش بدهکار", "گردش بستانکار", "مانده بدهکار", "مانده بستانکار"]
            rows = [
                [r["code"], r["name"], r["period_debit"], r["period_credit"], r["debit_balance"], r["credit_balance"]]
                for r in data["rows"]
            ]
            totals = ["", "جمع", data["total_debit"], data["total_credit"], data["total_debit_balance"], data["total_credit_balance"]]
        else:
            headers = ["کد", "نام", "بدهکار", "بستانکار", "مانده"]
            rows = [
                [r["code"], r["name"], r["period_debit"], r["period_credit"], r["debit_balance"] - r["credit_balance"]]
                for r in data["rows"]
            ]
            totals = ["", "جمع", data["total_debit"], data["total_credit"], ""]

        from utils.config import low_resource_mode
        lr = low_resource_mode(self.report_model.db)
        if fmt == "excel":
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره Excel", "", "Excel (*.xlsx)")
            if path:
                # If low-resource mode, pass rows as iterator and enable streaming path
                if lr:
                    export_to_excel(path, title, headers, (r for r in rows), totals, low_memory=True)
                else:
                    export_to_excel(path, title, headers, rows, totals)
        else:
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره PDF", "", "PDF (*.pdf)")
            if path:
                export_to_pdf(path, title, headers, rows + [totals])