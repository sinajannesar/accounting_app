"""تب داشبورد — خلاصه وضعیت مالی"""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout,
)

from ui.widgets import format_amount
from utils.jalali import last_n_months, current_jalali_year_month, PERSIAN_MONTH_NAMES


class MetricCard(QFrame):
    def __init__(self, title, color="#2c3e50", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                border-top: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #7f8c8d; font-size: 10pt; border: none;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {color}; font-size: 15pt; font-weight: bold; border: none;")
        layout.addWidget(self.value_label)

    def set_value(self, text):
        self.value_label.setText(text)


class MonthlyBarChart(QWidget):
    """نمودار ساده میله‌ای درآمد/هزینه ماهانه، رسم‌شده با QPainter (بدون کتابخانه جانبی)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # لیست دیکشنری‌ها: {label, income, expense}
        self.setMinimumHeight(260)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self.data:
            painter.end()
            return

        margin_left = 70
        margin_right = 20
        margin_top = 20
        margin_bottom = 45
        w = self.width() - margin_left - margin_right
        h = self.height() - margin_top - margin_bottom

        max_val = max([max(d["income"], d["expense"]) for d in self.data] + [1])
        if max_val <= 0:
            max_val = 1

        # محورها
        axis_pen = QPen(QColor("#bdc3c7"))
        painter.setPen(axis_pen)
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + h)
        painter.drawLine(margin_left, margin_top + h, margin_left + w, margin_top + h)

        # خطوط راهنما و برچسب محور عمودی
        painter.setFont(QFont("Tahoma", 8))
        for i in range(5):
            y = margin_top + h - (h * i / 4)
            val = max_val * i / 4
            painter.setPen(QPen(QColor("#ecf0f1")))
            painter.drawLine(margin_left, int(y), margin_left + w, int(y))
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.drawText(QRectF(0, y - 8, margin_left - 8, 16), Qt.AlignRight | Qt.AlignVCenter, format_amount(val))

        n = len(self.data)
        group_width = w / n
        bar_width = min(group_width * 0.28, 26)

        for idx, d in enumerate(self.data):
            group_center = margin_left + group_width * idx + group_width / 2
            income_h = (d["income"] / max_val) * h
            expense_h = (d["expense"] / max_val) * h

            income_x = group_center - bar_width - 3
            expense_x = group_center + 3

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#27ae60"))
            painter.drawRoundedRect(
                QRectF(income_x, margin_top + h - income_h, bar_width, income_h), 3, 3
            )
            painter.setBrush(QColor("#e74c3c"))
            painter.drawRoundedRect(
                QRectF(expense_x, margin_top + h - expense_h, bar_width, expense_h), 3, 3
            )

            painter.setPen(QPen(QColor("#2c3e50")))
            painter.setFont(QFont("Tahoma", 9))
            painter.drawText(
                QRectF(group_center - group_width / 2, margin_top + h + 6, group_width, 20),
                Qt.AlignCenter, d["label"],
            )

        painter.end()


class DashboardWidget(QWidget):
    def __init__(self, report_model, journal_model, db, parent=None):
        super().__init__(parent)
        self.report_model = report_model
        self.journal_model = journal_model
        self.db = db
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("داشبورد خلاصه وضعیت مالی")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        cards_layout = QGridLayout()
        self.income_card = MetricCard("درآمد این ماه", color="#27ae60")
        self.expense_card = MetricCard("هزینه این ماه", color="#e74c3c")
        self.profit_card = MetricCard("سود/زیان این ماه", color="#2980b9")
        self.cash_card = MetricCard("موجودی صندوق", color="#8e44ad")
        cards_layout.addWidget(self.income_card, 0, 0)
        cards_layout.addWidget(self.expense_card, 0, 1)
        cards_layout.addWidget(self.profit_card, 0, 2)
        cards_layout.addWidget(self.cash_card, 0, 3)
        layout.addLayout(cards_layout)

        chart_label = QLabel("روند ۶ ماه اخیر (درآمد سبز، هزینه قرمز)")
        chart_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(chart_label)

        self.chart = MonthlyBarChart()
        layout.addWidget(self.chart)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("بروزرسانی")
        refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _cash_account_id(self):
        cash_id = self.db.get_setting("cash_account_id")
        return int(cash_id) if cash_id else None

    def refresh(self):
        year, month = current_jalali_year_month()
        months = last_n_months(6)
        _, _, _, date_from, date_to = months[-1]  # آخرین ماه = ماه جاری

        stmt = self.report_model.income_statement(date_from, date_to)
        self.income_card.set_value(format_amount(stmt["total_income"]) + " ریال")
        self.expense_card.set_value(format_amount(stmt["total_expense"]) + " ریال")
        net = stmt["net_profit"]
        self.profit_card.set_value(("+" if net >= 0 else "") + format_amount(net) + " ریال")

        cash_id = self._cash_account_id()
        if cash_id:
            balance = self.journal_model.get_cash_balance(cash_id)
            self.cash_card.set_value(format_amount(balance) + " ریال")
        else:
            self.cash_card.set_value("-")

        chart_data = []
        for (y, m, label, d_from, d_to) in months:
            month_stmt = self.report_model.income_statement(d_from, d_to)
            chart_data.append({
                "label": label,
                "income": month_stmt["total_income"],
                "expense": month_stmt["total_expense"],
            })
        self.chart.set_data(chart_data)
