"""استایل‌های RTL فارسی"""

APP_STYLE = """
QMainWindow, QWidget {
    font-family: Tahoma, Arial, sans-serif;
    font-size: 11pt;
    background-color: #f5f6fa;
}

QMenuBar {
    background-color: #2c3e50;
    color: white;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #34495e;
}

QMenu {
    background-color: white;
    border: 1px solid #bdc3c7;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QToolBar {
    background-color: #ecf0f1;
    border-bottom: 1px solid #bdc3c7;
    spacing: 4px;
    padding: 4px;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton#dangerBtn {
    background-color: #e74c3c;
}

QPushButton#dangerBtn:hover {
    background-color: #c0392b;
}

QPushButton#successBtn {
    background-color: #27ae60;
}

QPushButton#successBtn:hover {
    background-color: #219a52;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #3498db;
}

QTableWidget {
    background-color: white;
    alternate-background-color: #f8f9fa;
    gridline-color: #dee2e6;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #2c3e50;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}

QTreeWidget {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
}

QTreeWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QTabWidget::pane {
    border: 1px solid #bdc3c7;
    background-color: white;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #ecf0f1;
    padding: 8px 20px;
    margin-left: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #3498db;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 8px;
}

QLabel#titleLabel {
    font-size: 16pt;
    font-weight: bold;
    color: #2c3e50;
}

QLabel#balanceLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #27ae60;
}

QStatusBar {
    background-color: #ecf0f1;
    color: #2c3e50;
}
"""
