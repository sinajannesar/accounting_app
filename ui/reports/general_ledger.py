"""گزارش دفتر کل"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QLabel, QSplitter, QFrame,
)

from ui.widgets import show_error, format_amount, DateRangeWidget, apply_shadow
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

        splitter = QSplitter(Qt.Vertical)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(
            ["کد", "نام حساب", "جمع بدهکار", "جمع بستانکار", "مانده"]
        )
        header = self.accounts_table.horizontalHeader()
        # Prefer specific sizing: code narrow, name wide, amounts medium
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.accounts_table.setWordWrap(True)
        self.accounts_table.setTextElideMode(Qt.ElideNone)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.itemSelectionChanged.connect(self._on_account_selected)
        splitter.addWidget(self.accounts_table)

        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("sectionLabel")
        detail_layout.addWidget(self.detail_label)
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(6)
        self.movements_table.setHorizontalHeaderLabels(
            ["تاریخ", "شماره سند", "شرح", "بدهکار", "بستانکار", "مانده"]
        )
        mheader = self.movements_table.horizontalHeader()
        # prioritize description column
        mheader.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mheader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        mheader.setSectionResizeMode(2, QHeaderView.Stretch)
        mheader.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        mheader.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        mheader.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.movements_table.setWordWrap(True)
        self.movements_table.setTextElideMode(Qt.ElideNone)
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setMinimumHeight(220)
        detail_layout.addWidget(self.movements_table)
        splitter.addWidget(detail_container)

        content_layout.addWidget(splitter)
        layout.addWidget(content_card)

        self._report_data = []

    def refresh(self):
        try:
            d_from, d_to = self.date_range.get_range()
        except ValueError as e:
            show_error(self, str(e))
            return

        data = self.report_model.general_ledger(d_from, d_to)
        self._report_data = data

        self.accounts_table.setRowCount(len(data))
        for row, acc in enumerate(data):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(acc["code"]))
            self.accounts_table.setItem(row, 1, QTableWidgetItem(acc["name"]))
            self.accounts_table.setItem(row, 2, QTableWidgetItem(format_amount(acc["total_debit"])))
            self.accounts_table.setItem(row, 3, QTableWidgetItem(format_amount(acc["total_credit"])))
            self.accounts_table.setItem(row, 4, QTableWidgetItem(format_amount(acc["balance"])))
        # ensure wrapped names are fully visible
        self.accounts_table.resizeRowsToContents()

        self.movements_table.setRowCount(0)
        self.detail_label.setText("")

    def _on_account_selected(self):
        rows = self.accounts_table.selectionModel().selectedRows()
        if not rows or not self._report_data:
            return
        index = rows[0].row()
        acc = self._report_data[index]
        self.detail_label.setText(f"گردش حساب: {acc['code']} - {acc['name']}")

        movements = acc["movements"]
        self.movements_table.setRowCount(len(movements))
        balance = 0
        for row, m in enumerate(movements):
            balance += m["debit"] - m["credit"]
            self.movements_table.setItem(row, 0, QTableWidgetItem(m["entry_date"]))
            self.movements_table.setItem(row, 1, QTableWidgetItem(str(m["entry_number"])))
            desc = m.get("line_description") or m.get("entry_description") or ""
            self.movements_table.setItem(row, 2, QTableWidgetItem(desc))
            self.movements_table.setItem(row, 3, QTableWidgetItem(format_amount(m["debit"])))
            self.movements_table.setItem(row, 4, QTableWidgetItem(format_amount(m["credit"])))
            self.movements_table.setItem(row, 5, QTableWidgetItem(format_amount(balance)))
        # ensure movement descriptions are fully visible
        self.movements_table.resizeRowsToContents()

    def _export(self, fmt):
        if not self._report_data:
            show_error(self, "ابتدا گزارش را نمایش دهید")
            return
        title = "دفتر کل"
        headers = ["کد", "نام حساب", "جمع بدهکار", "جمع بستانکار", "مانده"]
        rows = [
            [acc["code"], acc["name"], acc["total_debit"], acc["total_credit"], acc["balance"]]
            for acc in self._report_data
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