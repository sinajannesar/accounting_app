"""ابزارهای تقویم شمسی (جلالی)"""

import jdatetime
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QDateEdit, QLineEdit, QHBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QIntValidator


def today_jalali():
    return jdatetime.date.today().strftime("%Y/%m/%d")


def format_jalali(date_str):
    if not date_str:
        return ""
    return date_str.replace("-", "/")


def parse_jalali(date_str):
    if not date_str:
        return None
    date_str = date_str.strip().replace("-", "/")
    parts = date_str.split("/")
    if len(parts) != 3:
        raise ValueError("فرمت تاریخ نامعتبر است (مثال: 1403/05/20)")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    jdatetime.date(y, m, d)
    return f"{y:04d}/{m:02d}/{d:02d}"


def jalali_str_add_days(jalali_str, days):
    """تاریخ شمسی را به‌همراه تعداد روز داده‌شده جلو/عقب می‌برد"""
    parts = jalali_str.split("/")
    jd = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    new_jd = jd + jdatetime.timedelta(days=days)
    return new_jd.strftime("%Y/%m/%d")


PERSIAN_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def jalali_month_bounds(year, month):
    """بازه (اول تا آخر) یک ماه شمسی را برمی‌گرداند"""
    start = jdatetime.date(year, month, 1)
    if month == 12:
        next_start = jdatetime.date(year + 1, 1, 1)
    else:
        next_start = jdatetime.date(year, month + 1, 1)
    end = next_start - jdatetime.timedelta(days=1)
    return start.strftime("%Y/%m/%d"), end.strftime("%Y/%m/%d")


def current_jalali_year_month():
    today = jdatetime.date.today()
    return today.year, today.month


def last_n_months(n=6):
    """لیست n ماه اخیر شمسی را از قدیم به جدید برمی‌گرداند: (year, month, label, date_from, date_to)"""
    year, month = current_jalali_year_month()
    months = []
    for _ in range(n):
        date_from, date_to = jalali_month_bounds(year, month)
        label = PERSIAN_MONTH_NAMES[month - 1]
        months.append((year, month, label, date_from, date_to))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def gregorian_to_jalali_str(gdate):
    if isinstance(gdate, QDate):
        jd = jdatetime.date.fromgregorian(year=gdate.year(), month=gdate.month(), day=gdate.day())
    else:
        jd = jdatetime.date.fromgregorian(date=gdate)
    return jd.strftime("%Y/%m/%d")


def jalali_to_gregorian_str(jalali_str):
    jalali_str = parse_jalali(jalali_str)
    parts = jalali_str.split("/")
    jd = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    gd = jd.togregorian()
    return gd.strftime("%Y-%m-%d")


class JalaliDateEdit(QWidget):
    """ویجت ورود تاریخ شمسی با سه فیلد"""

    def __init__(self, parent=None, default_today=True):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.year_edit = QLineEdit()
        self.year_edit.setMaxLength(4)
        self.year_edit.setValidator(QIntValidator(1300, 1500))
        self.year_edit.setPlaceholderText("سال")
        self.year_edit.setFixedWidth(70)
        self.year_edit.setFixedHeight(36)
        self.year_edit.setAlignment(Qt.AlignCenter)
        # reduced padding so two-digit month/day are not clipped
        self.year_edit.setStyleSheet("padding: 6px 7px; border: 1px solid #E4E7EC; border-radius: 8px; background-color: #FFFFFF;")

        self.month_edit = QLineEdit()
        self.month_edit.setMaxLength(2)
        self.month_edit.setValidator(QIntValidator(1, 12))
        self.month_edit.setPlaceholderText("ماه")
        self.month_edit.setFixedWidth(52)
        self.month_edit.setFixedHeight(36)
        self.month_edit.setAlignment(Qt.AlignCenter)
        self.month_edit.setStyleSheet("padding: 6px 7px; border: 1px solid #E4E7EC; border-radius: 8px; background-color: #FFFFFF;")

        self.day_edit = QLineEdit()
        self.day_edit.setMaxLength(2)
        self.day_edit.setValidator(QIntValidator(1, 31))
        self.day_edit.setPlaceholderText("روز")
        self.day_edit.setFixedWidth(52)
        self.day_edit.setFixedHeight(36)
        self.day_edit.setAlignment(Qt.AlignCenter)
        self.day_edit.setStyleSheet("padding: 6px 7px; border: 1px solid #E4E7EC; border-radius: 8px; background-color: #FFFFFF;")

        layout.addWidget(self.day_edit)
        layout.addWidget(QLabel("/"))
        layout.addWidget(self.month_edit)
        layout.addWidget(QLabel("/"))
        layout.addWidget(self.year_edit)
        layout.addStretch()

        if default_today:
            self.set_date(today_jalali())

    def set_date(self, jalali_str):
        if not jalali_str:
            self.year_edit.clear()
            self.month_edit.clear()
            self.day_edit.clear()
            return
        parts = jalali_str.replace("-", "/").split("/")
        if len(parts) == 3:
            # ensure zero-padded display for month/day and full year visible
            self.year_edit.setText(parts[0])
            try:
                self.month_edit.setText(f"{int(parts[1]):02d}")
            except Exception:
                self.month_edit.setText(parts[1])
            try:
                self.day_edit.setText(f"{int(parts[2]):02d}")
            except Exception:
                self.day_edit.setText(parts[2])

    def get_date(self):
        y = self.year_edit.text().strip()
        m = self.month_edit.text().strip()
        d = self.day_edit.text().strip()
        if not y and not m and not d:
            return ""
        if not y or not m or not d:
            raise ValueError("تاریخ ناقص است")
        return parse_jalali(f"{y}/{m}/{d}")

    def clear(self):
        self.year_edit.clear()
        self.month_edit.clear()
        self.day_edit.clear()