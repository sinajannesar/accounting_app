from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("تنظیمات — در حال توسعه")
        layout.addWidget(label)
