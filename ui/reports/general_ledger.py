"""گزارش دفتر کل"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QLabel,
)

from ui.widgets import show_error, format_amount, DateRangeWidget
from utils.export import export_to_excel, export_to_pdf


class GeneralLedgerWidget(QWidget):
    def __init__(self, report_model, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        self.date_range = DateRangeWidget()
        filter_layout.addWidget(self.date_range)
        run_btn = QPushButton("نمایش گزارش")
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        layout.addLayout(filter_layout)

        export_layout = QHBoxLayout()
        excel_btn = QPushButton("خروجی Excel")
        excel_btn.clicked.connect(lambda: self._export("excel"))
        pdf_btn = QPushButton("خروجی PDF")
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["کد", "نام حساب", "جمع بدهکار", "جمع بستانکار", "مانده"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        self._report_data = []

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError as e:
            show_error(self, str(e))
            return
        data = self.report_model.general_ledger(d_from, d_to)
        self._report_data = data
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item["code"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(format_amount(item["total_debit"])))
            self.table.setItem(row, 3, QTableWidgetItem(format_amount(item["total_credit"])))
            self.table.setItem(row, 4, QTableWidgetItem(format_amount(item["balance"])))

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        title = "دفتر کل"
        headers = ["کد", "نام حساب", "جمع بدهکار", "جمع بستانکار", "مانده"]
        rows = [
            [d["code"], d["name"], d["total_debit"], d["total_credit"], d["balance"]]
            for d in self._report_data
        ]
        if fmt == "excel":
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره Excel", "", "Excel (*.xlsx)")
            if path:
                export_to_excel(path, title, headers, rows)
        else:
            path, _ = QFileDialog.getSaveFileName(self, "ذخیره PDF", "", "PDF (*.pdf)")
            if path:
                export_to_pdf(path, title, headers, [
                    [r[0], r[1], format_amount(r[2]), format_amount(r[3]), format_amount(r[4])]
                    for r in rows
                ])
