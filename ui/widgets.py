# ui/widgets.py — FULL FILE, replace entirely
"""ویجت‌های مشترک"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QGroupBox, QVBoxLayout,
    QMessageBox, QFrame, QDoubleSpinBox, QGraphicsDropShadowEffect,
)
from utils.jalali import JalaliDateEdit
from utils.num2words_fa import amount_to_words_rial
from ui.styles import COLOR_TEXT_MUTED


def apply_shadow(widget, blur=28, y_offset=6, alpha=40):
    """سایه‌ی ملایم برای کارت‌ها. QSS از box-shadow پشتیبانی نمی‌کند،
    بنابراین سایه با QGraphicsDropShadowEffect در پایتون اعمال می‌شود."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    # slightly darker, more visible shadow for modern UI
    effect.setColor(QColor(6, 30, 80, alpha))
    widget.setGraphicsEffect(effect)
    return effect


class DateRangeWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("بازه تاریخی", parent)
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("از تاریخ:"))
        self.date_from = JalaliDateEdit()
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("تا تاریخ:"))
        self.date_to = JalaliDateEdit()
        layout.addWidget(self.date_to)
        layout.addStretch()

    def get_range(self):
        try:
            d_from = self.date_from.get_date()
            d_to = self.date_to.get_date()
            if d_from and d_to and d_from > d_to:
                raise ValueError("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد")
            return d_from or None, d_to or None
        except ValueError as e:
            raise ValueError(str(e))


def show_error(parent, message):
    QMessageBox.critical(parent, "خطا", message)


def show_info(parent, message):
    QMessageBox.information(parent, "اطلاع", message)


def show_confirm(parent, message):
    reply = QMessageBox.question(
        parent, "تأیید", message,
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
    )
    return reply == QMessageBox.Yes


class AmountInput(QWidget):
    """ورودی مبلغ که معادل ریالی مبلغ را به‌صورت زنده زیر فیلد نمایش می‌دهد"""

    def __init__(self, parent=None, minimum=0, maximum=999999999999):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setDecimals(0)
        self.spin.setGroupSeparatorShown(True)
        self.spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        layout.addWidget(self.spin)

        self.words_label = QLabel("")
        self.words_label.setWordWrap(True)
        self.words_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 9pt; padding: 2px 4px 0 4px; border: none;"
        )
        layout.addWidget(self.words_label)

        self.spin.valueChanged.connect(self._update_words)
        self._update_words(self.spin.value())

    def _update_words(self, value):
        if value and value > 0:
            self.words_label.setText(amount_to_words_rial(value))
        else:
            self.words_label.setText("")

    def value(self):
        return self.spin.value()

    def setValue(self, value):
        self.spin.setValue(value or 0)

    def setRange(self, minimum, maximum):
        self.spin.setRange(minimum, maximum)


def format_amount(amount):
    if amount is None:
        return "0"
    if isinstance(amount, float) and amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.0f}"