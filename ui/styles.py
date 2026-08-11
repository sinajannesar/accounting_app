"""استایل مدرن و ساده رابط کاربری (RTL فارسی)"""

# پالت رنگی
COLOR_PRIMARY = "#3b6ff5"
COLOR_PRIMARY_DARK = "#2d55c9"
COLOR_PRIMARY_LIGHT = "#eaf0ff"
COLOR_SUCCESS = "#22a06b"
COLOR_SUCCESS_DARK = "#188457"
COLOR_DANGER = "#e5484d"
COLOR_DANGER_DARK = "#c5393e"
COLOR_TEXT = "#1f2430"
COLOR_TEXT_MUTED = "#7a8290"
COLOR_BG = "#f4f6fb"
COLOR_CARD = "#ffffff"
COLOR_BORDER = "#e3e7ef"

APP_STYLE = f"""
* {{
    outline: none;
}}

QMainWindow, QWidget {{
    font-family: "Vazirmatn", "Tahoma", "Segoe UI", Arial, sans-serif;
    font-size: 10.5pt;
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
}}

QMenuBar {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    padding: 6px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QMenuBar::item {{
    padding: 6px 14px;
    border-radius: 6px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QMenu {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 20px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QToolBar {{
    background-color: {COLOR_CARD};
    border-bottom: 1px solid {COLOR_BORDER};
    spacing: 6px;
    padding: 6px;
}}

QPushButton {{
    background-color: {COLOR_PRIMARY};
    color: white;
    border: none;
    padding: 9px 18px;
    border-radius: 8px;
    min-width: 80px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLOR_PRIMARY_DARK};
}}

QPushButton:pressed {{
    background-color: #24409e;
}}

QPushButton:disabled {{
    background-color: #c7ccd6;
    color: #f0f1f4;
}}

QPushButton#dangerBtn {{
    background-color: {COLOR_DANGER};
}}

QPushButton#dangerBtn:hover {{
    background-color: {COLOR_DANGER_DARK};
}}

QPushButton#successBtn {{
    background-color: {COLOR_SUCCESS};
}}

QPushButton#successBtn:hover {{
    background-color: {COLOR_SUCCESS_DARK};
}}

QPushButton#flatBtn {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
}}

QPushButton#flatBtn:hover {{
    background-color: {COLOR_PRIMARY_LIGHT};
    border-color: {COLOR_PRIMARY};
    color: {COLOR_PRIMARY_DARK};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 7px 10px;
    background-color: {COLOR_CARD};
    selection-background-color: {COLOR_PRIMARY};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QDateEdit:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QTableWidget {{
    background-color: {COLOR_CARD};
    alternate-background-color: #f8f9fc;
    gridline-color: {COLOR_BORDER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    selection-background-color: {COLOR_PRIMARY_LIGHT};
    selection-color: {COLOR_PRIMARY_DARK};
}}

QTableWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QTableWidget::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QHeaderView::section {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_MUTED};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
    font-weight: 700;
}}

QTreeWidget {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 4px;
}}

QTreeWidget::item {{
    padding: 6px 4px;
    border-radius: 6px;
}}

QTreeWidget::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    background-color: {COLOR_CARD};
    border-radius: 10px;
    top: -1px;
}}

QTabBar {{
    background: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLOR_TEXT_MUTED};
    padding: 12px 22px;
    margin: 0 2px;
    font-weight: 600;
    border-bottom: 3px solid transparent;
}}

QTabBar::tab:selected {{
    color: {COLOR_PRIMARY_DARK};
    border-bottom: 3px solid {COLOR_PRIMARY};
}}

QTabBar::tab:hover {{
    color: {COLOR_PRIMARY};
}}

QGroupBox {{
    font-weight: 700;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 18px;
    background-color: {COLOR_CARD};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 10px;
    color: {COLOR_TEXT_MUTED};
}}

QLabel#titleLabel {{
    font-size: 16pt;
    font-weight: 800;
    color: {COLOR_TEXT};
    padding: 4px 0 10px 0;
}}

QLabel#balanceLabel {{
    font-size: 15pt;
    font-weight: 800;
    color: {COLOR_SUCCESS_DARK};
}}

QStatusBar {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT_MUTED};
    border-top: 1px solid {COLOR_BORDER};
    padding: 4px;
}}

QDialog {{
    background-color: {COLOR_BG};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #c7ccd6;
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: #a9aebb;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QMessageBox {{
    background-color: {COLOR_CARD};
}}
"""