# ui/dashboard_widget.py — FULL FILE, replace entirely
"""تب داشبورد — خلاصه وضعیت مالی"""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout,
)
import os

from ui.widgets import format_amount, apply_shadow
from utils.config import low_resource_mode
from ui.styles import (
    COLOR_CARD, COLOR_BORDER, COLOR_BORDER_STRONG, COLOR_TEXT, COLOR_TEXT_MUTED,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_PRIMARY, COLOR_INFO,
    RADIUS_MD, RADIUS_SM,
)
from ui.styles import COLOR_TEXT_DARK, COLOR_CHART_TEXT
from utils.jalali import last_n_months, current_jalali_year_month, PERSIAN_MONTH_NAMES


class MetricCard(QFrame):
    """High-contrast metric card: white background, dark text, colored icon/accent."""

    def __init__(self, title, color=COLOR_TEXT, icon="", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        if color != COLOR_TEXT:
            self.setProperty("variant", "accent")
        self.setMinimumHeight(120)
        # white card with subtle border
        self.setStyleSheet(f"QFrame#metricCard {{ background-color: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px; }}")
        apply_shadow(self, blur=20, y_offset=3, alpha=22)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        if icon:
            icon_label = QLabel()
            icon_label.setProperty("role", "cardIcon")
            # if icon is a QIcon or a path, load it via QIcon to support SVG
            pix = QPixmap()
            try:
                if not low_resource_mode():
                    if isinstance(icon, QIcon):
                        pix = icon.pixmap(20, 20)
                    else:
                        icon_path = icon if isinstance(icon, str) and os.path.exists(icon) else None
                        if icon_path:
                            ic = QIcon(icon_path)
                            pix = ic.pixmap(20, 20)
                    if not pix.isNull():
                        icon_label.setPixmap(pix)
                else:
                    # hide icon to save memory/cpu on low-resource systems
                    icon_label.setVisible(False)
            except Exception:
                # any failure loading icons shouldn't stop the UI
                icon_label.setVisible(False)
            icon_label.setStyleSheet(f"background-color: {color}; border-radius: {RADIUS_SM}px; padding: 6px;")
            icon_label.setFixedSize(40, 40)
            header.addWidget(icon_label, 0)
        self.title_label = QLabel(title)
        # Title: medium dark
        self.title_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10pt; font-weight: 700; border: none;")
        header.addWidget(self.title_label, 1)
        outer.addLayout(header)

        # main value and unit on same row for compactness
        value_row = QHBoxLayout()
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 18pt; font-weight: 900; border: none;")
        value_row.addWidget(self.value_label)
        self.unit_label = QLabel("")
        self.unit_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11pt; padding-right: 8px;")
        value_row.addWidget(self.unit_label)
        value_row.addStretch()
        outer.addLayout(value_row)

    def set_value(self, text, unit=""):
        self.value_label.setText(text)
        self.unit_label.setText(unit)


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
        # In low-resource mode, skip complex painting and show a lightweight message
        if low_resource_mode():
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(COLOR_CARD))
            painter.setPen(QPen(QColor(COLOR_CHART_TEXT)))
            painter.setFont(QFont("Vazirmatn", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "نمودار غیرفعال (حالت کم‌منابع)")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(COLOR_CARD))

        if not self.data:
            painter.setPen(QPen(QColor(COLOR_CHART_TEXT)))
            painter.setFont(QFont("Vazirmatn", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "داده‌ای برای نمایش وجود ندارد")
            painter.end()
            return

        margin_left = 74
        margin_right = 20
        margin_top = 20
        margin_bottom = 45
        w = self.width() - margin_left - margin_right
        h = self.height() - margin_top - margin_bottom

        max_val = max([max(d["income"], d["expense"]) for d in self.data] + [1])
        if max_val <= 0:
            max_val = 1

        # خطوط راهنما و برچسب محور عمودی
        painter.setFont(QFont("Vazirmatn", 8))
        for i in range(5):
            y = margin_top + h - (h * i / 4)
            val = max_val * i / 4
            painter.setPen(QPen(QColor(COLOR_BORDER)))
            painter.drawLine(margin_left, int(y), margin_left + w, int(y))
            painter.setPen(QPen(QColor(COLOR_CHART_TEXT)))
            painter.drawText(QRectF(0, y - 8, margin_left - 10, 16), Qt.AlignRight | Qt.AlignVCenter, format_amount(val))

        # محور پایه پررنگ‌تر از خطوط راهنما
        painter.setPen(QPen(QColor(COLOR_BORDER_STRONG), 1.2))
        painter.drawLine(margin_left, margin_top + h, margin_left + w, margin_top + h)

        n = len(self.data)
        group_width = w / n
        bar_width = min(group_width * 0.26, 24)

        for idx, d in enumerate(self.data):
            group_center = margin_left + group_width * idx + group_width / 2
            income_h = (d["income"] / max_val) * h
            expense_h = (d["expense"] / max_val) * h

            income_x = group_center - bar_width - 3
            expense_x = group_center + 3

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(COLOR_SUCCESS))
            painter.drawRoundedRect(
                QRectF(income_x, margin_top + h - income_h, bar_width, max(income_h, 0)), 4, 4
            )
            painter.setBrush(QColor(COLOR_DANGER))
            painter.drawRoundedRect(
                QRectF(expense_x, margin_top + h - expense_h, bar_width, max(expense_h, 0)), 4, 4
            )

            painter.setPen(QPen(QColor(COLOR_CHART_TEXT)))
            painter.setFont(QFont("Vazirmatn", 9))
            painter.drawText(
                QRectF(group_center - group_width / 2, margin_top + h + 8, group_width, 20),
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
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("داشبورد خلاصه وضعیت مالی")
        title.setObjectName("titleLabel")
        title_box.addWidget(title)
        subtitle = QLabel("نمای کلی ماه جاری — درآمد، هزینه، سود و موجودی صندوق")
        subtitle.setObjectName("subtitleLabel")
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # use SVG refresh icon, avoid emoji
        refresh_btn = QPushButton("  بروزرسانی")
        refresh_icon = os.path.join(os.path.dirname(__file__), "icons", "refresh.svg")
        if os.path.exists(refresh_icon):
            refresh_btn.setIcon(QIcon(refresh_icon))
        refresh_btn.setObjectName("flatBtn")
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        self.income_card = MetricCard("درآمد این ماه", color=COLOR_SUCCESS, icon=os.path.join(icons_dir, "chart_up.svg"))
        self.expense_card = MetricCard("هزینه این ماه", color=COLOR_DANGER, icon=os.path.join(icons_dir, "chart_down.svg"))
        self.profit_card = MetricCard("سود/زیان این ماه", color=COLOR_PRIMARY, icon=os.path.join(icons_dir, "profit.svg"))
        self.cash_card = MetricCard("موجودی صندوق", color=COLOR_INFO, icon=os.path.join(icons_dir, "cash.svg"))
        cards_layout.addWidget(self.income_card, 0, 0)
        cards_layout.addWidget(self.expense_card, 0, 1)
        cards_layout.addWidget(self.profit_card, 0, 2)
        cards_layout.addWidget(self.cash_card, 0, 3)
        layout.addLayout(cards_layout)

        # کارت نمودار — با سایه، مشابه بقیه کارت‌ها تا رابط یکدست بماند
        chart_card = QFrame()
        chart_card.setObjectName("chartCard")
        chart_card.setStyleSheet(f"""
            QFrame#chartCard {{
                background-color: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: {RADIUS_MD}px;
            }}
        """)
        apply_shadow(chart_card, blur=20, y_offset=3, alpha=18)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(18, 16, 18, 12)
        chart_layout.setSpacing(6)

        chart_header = QHBoxLayout()
        chart_title = QLabel("روند ۶ ماه اخیر")
        chart_title.setObjectName("sectionLabel")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_header.addWidget(self._legend_dot(COLOR_SUCCESS, "درآمد"))
        chart_header.addWidget(self._legend_dot(COLOR_DANGER, "هزینه"))
        chart_layout.addLayout(chart_header)

        self.chart = MonthlyBarChart()
        chart_layout.addWidget(self.chart)
        layout.addWidget(chart_card, 1)

    def _legend_dot(self, color, text):
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(12, 0, 0, 0)
        row.setSpacing(6)
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        row.addWidget(dot)
        label = QLabel(text)
        label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9pt; border: none;")
        row.addWidget(label)
        return wrap

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

        # skip building chart data on low-resource systems to save CPU and DB queries
        chart_data = []
        if low_resource_mode():
            # leave chart_data empty so paintEvent shows lightweight message
            self.chart.set_data([])
            return
        for (y, m, label, d_from, d_to) in months:
            month_stmt = self.report_model.income_statement(d_from, d_to)
            chart_data.append({
                "label": label,
                "income": month_stmt["total_income"],
                "expense": month_stmt["total_expense"],
            })
        self.chart.set_data(chart_data)