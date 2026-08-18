from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox

class SettingsWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        layout = QVBoxLayout(self)
        label = QLabel("تنظیمات")
        layout.addWidget(label)

        self.low_mem_checkbox = QCheckBox("حالت کم‌منابع (Low Resource Mode)")
        # read setting from DB if available
        try:
            val = self.db.get_setting('low_resource_mode', '0')
            self.low_mem_checkbox.setChecked(val in ('1', 'true', 'True'))
        except Exception:
            self.low_mem_checkbox.setChecked(False)
        layout.addWidget(self.low_mem_checkbox)

        save_btn = QPushButton("ذخیره تنظیمات")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        note = QLabel("توجه: برای تاثیر کامل، برنامه را مجدداً راه‌اندازی کنید؛ همچنین متغیر محیطی LOW_RESOURCE در اولویت است.")
        note.setWordWrap(True)
        layout.addWidget(note)

    def _save(self):
        try:
            self.db.set_setting('low_resource_mode', '1' if self.low_mem_checkbox.isChecked() else '0')
            QMessageBox.information(self, 'ذخیره', 'تنظیمات با موفقیت ذخیره شد. برای اعمال کامل، برنامه را مجدداً راه‌اندازی کنید.')
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در ذخیره تنظیمات: {e}')
