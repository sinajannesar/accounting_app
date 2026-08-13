"""گزارش صورت سود و زیان"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QLabel, QGroupBox, QFrame,
)

from ui.widgets import show_error, format_amount, DateRangeWidget, apply_shadow
from utils.export import export_to_excel, export_to_pdf


class IncomeStatementWidget(QWidget):
    def __init__(self, report_model, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # content card wrapper
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
        run_btn = QPushButton("نمایش گزارش")
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        content_layout.addLayout(filter_layout)

        export_layout = QHBoxLayout()
        excel_btn = QPushButton("خروجی Excel")
        excel_btn.clicked.connect(lambda: self._export("excel"))
        pdf_btn = QPushButton("خروجی PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addStretch()
        content_layout.addLayout(export_layout)

        income_group = QGroupBox("درآمدها")
        income_layout = QVBoxLayout(income_group)
        self.income_table = QTableWidget()
        self.income_table.setColumnCount(3)
        self.income_table.setHorizontalHeaderLabels(["کد", "نام", "مبلغ"])
        iheader = self.income_table.horizontalHeader()
        iheader.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        iheader.setSectionResizeMode(1, QHeaderView.Stretch)
        iheader.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.income_table.setWordWrap(True)
        self.income_table.setTextElideMode(Qt.ElideNone)
        income_layout.addWidget(self.income_table)
        self.total_income_label = QLabel("جمع درآمد: 0")
        income_layout.addWidget(self.total_income_label)
        content_layout.addWidget(income_group)

        expense_group = QGroupBox("هزینه‌ها")
        expense_layout = QVBoxLayout(expense_group)
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(3)
        self.expense_table.setHorizontalHeaderLabels(["کد", "نام", "مبلغ"])
        eheader = self.expense_table.horizontalHeader()
        eheader.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        eheader.setSectionResizeMode(1, QHeaderView.Stretch)
        eheader.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.expense_table.setWordWrap(True)
        self.expense_table.setTextElideMode(Qt.ElideNone)
        expense_layout.addWidget(self.expense_table)
        self.total_expense_label = QLabel("جمع هزینه: 0")
        expense_layout.addWidget(self.total_expense_label)
        content_layout.addWidget(expense_group)

        self.net_label = QLabel("")
        self.net_label.setObjectName("sectionLabel")
        content_layout.addWidget(self.net_label)
        layout.addWidget(content_card)
        self._report_data = None

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError as e:
            show_error(self, str(e))
            return
        data = self.report_model.income_statement(d_from, d_to)
        self._report_data = data

        self.income_table.setRowCount(len(data["income_items"]))
        for row, item in enumerate(data["income_items"]):
            self.income_table.setItem(row, 0, QTableWidgetItem(item["code"]))
            self.income_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.income_table.setItem(row, 2, QTableWidgetItem(format_amount(item["amount"])))
        # ensure wrapped names show fully
        self.income_table.resizeRowsToContents()
        self.total_income_label.setText(f"جمع درآمد: {format_amount(data['total_income'])} ریال")

        self.expense_table.setRowCount(len(data["expense_items"]))
        for row, item in enumerate(data["expense_items"]):
            self.expense_table.setItem(row, 0, QTableWidgetItem(item["code"]))
            self.expense_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.expense_table.setItem(row, 2, QTableWidgetItem(format_amount(item["amount"])))
        # ensure wrapped names show fully
        self.expense_table.resizeRowsToContents()
        self.total_expense_label.setText(f"جمع هزینه: {format_amount(data['total_expense'])} ریال")

        net = data["net_profit"]
        if net >= 0:
            self.net_label.setText(f"سود خالص: {format_amount(net)} ریال")
            self.net_label.setStyleSheet("color: #27ae60; font-size: 14pt; font-weight: bold;")
        else:
            self.net_label.setText(f"زیان خالص: {format_amount(abs(net))} ریال")
            self.net_label.setStyleSheet("color: #e74c3c; font-size: 14pt; font-weight: bold;")

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        data = self._report_data
        title = "صورت سود و زیان"
        headers = ["کد", "نام", "مبلغ"]
        rows = [["--- درآمدها ---", "", ""]]
        for item in data["income_items"]:
            rows.append([item["code"], item["name"], item["amount"]])
        rows.append(["", "جمع درآمد", data["total_income"]])
        rows.append(["--- هزینه‌ها ---", "", ""])
        for item in data["expense_items"]:
            rows.append([item["code"], item["name"], item["amount"]])
        rows.append(["", "جمع هزینه", data["total_expense"]])
        net_label = "سود خالص" if data["net_profit"] >= 0 else "زیان خالص"
        rows.append(["", net_label, abs(data["net_profit"])])

        if fmt == "excel":
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره Excel", "", "Excel (*.xlsx)")
            if path:
                export_to_excel(path, title, headers, rows)
        else:
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره PDF", "", "PDF (*.pdf)")
            if path:
                export_to_pdf(path, title, headers, [
                    [r[0], r[1], format_amount(r[2]) if isinstance(r[2], (int, float)) else r[2]]
                    for r in rows
                ])
