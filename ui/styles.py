# ui/styles.py — FULL FILE, replace entirely
"""سیستم طراحی رابط کاربری — نسخه ۲ (RTL فارسی)

نکته: PyQt5/QSS محدودیت‌های CSS استاندارد را دارد (بدون box-shadow واقعی،
بدون transition). سایه‌ی کارت‌ها با QGraphicsDropShadowEffect در پایتون
اعمال می‌شود، نه در این استایل‌شیت. برای همین منظور از ui.widgets.apply_shadow
استفاده کنید.
"""

# ---------------------------------------------------------------------------
# پالت رنگی (Design Tokens)
# ---------------------------------------------------------------------------
# New palette per user request
COLOR_PRIMARY = "#4F46E5"
COLOR_PRIMARY_HOVER = "#4338CA"
COLOR_PRIMARY_DARK = "#3730A3"
COLOR_PRIMARY_LIGHT = "#EEF2FF"
COLOR_PRIMARY_VERY_LIGHT = "#F5F7FF"

COLOR_ACCENT = "#7C3AED"

COLOR_SUCCESS = "#12B76A"
COLOR_SUCCESS_LIGHT = "#ECFDF3"

COLOR_DANGER = "#F04438"
COLOR_DANGER_LIGHT = "#FEF3F2"

COLOR_WARNING = "#F79009"
COLOR_WARNING_LIGHT = "#FFFAEB"

COLOR_INFO = "#0EA5E9"
COLOR_INFO_LIGHT = "#E6F7FF"

# accent palette for dashboard quick-cards (pastel)
ACCENT_GREEN = "#DFF7EA"
ACCENT_ORANGE = "#FFF2E6"
ACCENT_PURPLE = "#F3E9FF"
ACCENT_CYAN = "#E8F7FF"

# sidebar tokens
SIDEBAR_DARK = "#111827"
SIDEBAR_DARK_SECONDARY = "#1F2937"
SIDEBAR_ACTIVE = "#312E81"
SIDEBAR_TEXT = "#F9FAFB"
SIDEBAR_MUTED = "#9CA3AF"

# Additional darker variants used by older rules
COLOR_PRIMARY_DARKER = "#312E81"
COLOR_SUCCESS_DARK = "#0F9C57"
COLOR_DANGER_DARK = "#D92F1F"

COLOR_TEXT = "#172033"  # requested
COLOR_TEXT_MUTED = "#667085"
COLOR_TEXT_FAINT = "#98A0B0"

COLOR_BG = "#F7F8FC"
COLOR_CARD = "#FFFFFF"
COLOR_CARD_ALT = "#FAFBFF"
COLOR_BORDER = "#E4E7EC"
COLOR_BORDER_STRONG = "#D0D5DD"

# مقیاس فاصله‌گذاری (px) — برای استفاده‌ی یکدست در setContentsMargins/setSpacing
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 14
SPACE_LG = 20
SPACE_XL = 28

RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14

# ---------------------------------------------------------------------------
# استایل‌شیت سراسری
# ---------------------------------------------------------------------------
APP_STYLE = f"""
* {{
    outline: none;
}}

QMainWindow, QWidget {{
    font-family: "Vazirmatn", "IRANSans", "Tahoma", "Segoe UI", Arial, sans-serif;
    font-size: 10.5pt;
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
}}

QToolTip {{
    background-color: {COLOR_TEXT};
    color: white;
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 6px 10px;
    font-size: 9.5pt;
}}

/* ---------- منو و نوار ابزار ---------- */
QMenuBar {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    padding: 4px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

QMenuBar::item {{
    padding: 7px 16px;
    border-radius: {RADIUS_SM}px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QMenu {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 6px;
}}

QMenu::item {{
    padding: 9px 24px;
    border-radius: {RADIUS_SM}px;
}}

QMenu::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QMenu::separator {{
    height: 1px;
    background: {COLOR_BORDER};
    margin: 6px 4px;
}}

QToolBar {{
    background-color: {COLOR_CARD};
    border-bottom: 1px solid {COLOR_BORDER};
    spacing: 6px;
    padding: 6px;
}}

/* ---------- دکمه‌ها ---------- */
/* Primary buttons: subtle flat gradient */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY}, stop:1 {COLOR_PRIMARY_DARK});
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 10px;
    min-width: 84px;
    font-weight: 700;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_DARK}, stop:1 {COLOR_PRIMARY_DARKER});
}}
QPushButton:pressed {{
    /* no transform in Qt stylesheets */
}}

QPushButton:disabled {{
    background-color: #d3d7e2;
    color: #f2f3f7;
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
    border: 1.5px solid {COLOR_BORDER_STRONG};
    font-weight: 600;
}}
QPushButton#flatBtn:hover {{
    background-color: {COLOR_PRIMARY_LIGHT};
    border-color: {COLOR_PRIMARY};
    color: {COLOR_PRIMARY_DARK};
}}

/* ---------- ورودی‌ها ---------- */
/* Inputs: white, thin border, consistent height */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    background-color: {COLOR_CARD};
    min-height: 36px;
    selection-background-color: {COLOR_PRIMARY};
    selection-color: white;
}}

QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QTextEdit:hover, QDateEdit:hover {{
    border-color: {COLOR_BORDER_STRONG};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QDateEdit:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
}}

QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {COLOR_CARD_ALT};
    color: {COLOR_TEXT_FAINT};
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_SM}px;
    selection-background-color: {COLOR_PRIMARY_LIGHT};
    selection-color: {COLOR_PRIMARY_DARK};
    outline: none;
    padding: 4px;
}}


QCalendarWidget QToolButton {{
    color: {COLOR_TEXT};
    background-color: transparent;
    border-radius: {RADIUS_SM}px;
    padding: 4px 8px;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {COLOR_PRIMARY_LIGHT};
}}

/* ---------- جدول‌ها ---------- */
/* Tables: clean, minimal headers */
QTableWidget {{
    background-color: {COLOR_CARD};
    alternate-background-color: {COLOR_CARD_ALT};
    gridline-color: {COLOR_BORDER};
    border: none;
    border-radius: {RADIUS_MD}px;
    selection-background-color: rgba(47,91,179,0.08);
    selection-color: {COLOR_TEXT};
}}

QTableWidget::item {{
    padding: 12px 14px;
    border-bottom: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT};
}}

QTableWidget::item:selected {{
    background-color: rgba(47,91,179,0.08);
    color: {COLOR_TEXT};
}}

QHeaderView::section {{
    background-color: transparent;
    color: {COLOR_TEXT};
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    font-weight: 700;
    font-size: 10pt;
}}

QHeaderView::section:first {{
    border-top-right-radius: {RADIUS_MD}px;
}}
QHeaderView::section:last {{
    border-top-left-radius: {RADIUS_MD}px;
}}

/* ---------- درخت (سرفصل حساب‌ها) ---------- */
QTreeWidget {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 6px;
    show-decoration-selected: 1;
}}

QTreeWidget::item {{
    padding: 7px 4px;
    border-radius: {RADIUS_SM}px;
    margin: 1px 0;
}}

QTreeWidget::item:hover {{
    background-color: {COLOR_CARD_ALT};
}}

QTreeWidget::item:selected {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY_DARK};
}}

QTreeWidget::branch {{
    background: transparent;
}}

/* ---------- تب‌ها ---------- */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    background-color: {COLOR_CARD};
    border-radius: {RADIUS_MD}px;
    top: -1px;
}}

QTabBar {{
    background: transparent;
}}

/* QTabBar styling consolidated below (Top header / tabs) */

/* ---------- گروه‌بندی ---------- */
QGroupBox {{
    font-weight: 700;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_MD}px;
    margin-top: 16px;
    padding-top: 20px;
    background-color: {COLOR_CARD};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 12px;
    color: {COLOR_TEXT_MUTED};
}}

/* ---------- برچسب‌های معنایی ---------- */
QLabel#titleLabel {{
    font-size: 12pt;
    font-weight: 800;
    color: {COLOR_TEXT};
    padding: 1px 0 4px 0;
}}

QLabel#subtitleLabel {{
    font-size: 9.5pt;
    color: {COLOR_TEXT_MUTED};
    padding-bottom: 4px;
}}

QLabel#balanceLabel {{
    font-size: 16pt;
    font-weight: 800;
    color: {COLOR_SUCCESS_DARK};
}}

QLabel#sectionLabel {{
    font-size: 9pt;
    font-weight: 700;
    color: {COLOR_TEXT};
    padding-top: 0px;
    margin: 0;
    padding-bottom: 4px;
}}

/* Content cards */
QFrame#contentCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    padding: 14px;
}}

/* Left sidebar */
QFrame#leftSidebar {{
    background-color: {SIDEBAR_DARK};
    min-width: 240px;
    max-width: 260px;
    border-right: 1px solid {COLOR_BORDER};
}}

/* Sidebar items (icon + label) */
QPushButton#sidebarItem {{
    background: transparent;
    color: {SIDEBAR_TEXT};
    text-align: right;
    padding: 10px 14px;
    border-radius: 8px;
    font-weight: 600;
}}
QPushButton#sidebarItem:hover {{
    background-color: {SIDEBAR_DARK_SECONDARY};
    color: {SIDEBAR_TEXT};
}}
QPushButton#sidebarItem:checked {{
    background-color: {COLOR_PRIMARY_LIGHT};
    color: {COLOR_PRIMARY};
}}

QPushButton#sidebarSection {{
    color: {SIDEBAR_MUTED};
    background: transparent;
    border: none;
    padding: 8px 12px;
    text-align: right;
    font-weight: 700;
}}

QPushButton#sidebarProfile {{
    background: transparent;
    color: {SIDEBAR_TEXT};
    border: none;
    padding: 8px 12px;
}}

QPushButton#sidebarCollapse {{
    background: transparent;
    color: {SIDEBAR_MUTED};
    border: 1px solid rgba(255,255,255,0.03);
    border-radius: 8px;
    padding: 6px;
}}

/* Top header / tabs */
QTabBar::tab {{
    background: transparent;
    padding: 8px 12px;
    margin: 0 6px;
    color: {COLOR_TEXT_MUTED};
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {COLOR_PRIMARY};
    border-bottom: 3px solid {COLOR_PRIMARY};
    font-weight: 700;
}}

/* Metric card icon wrapper — targets QLabel used as icon inside MetricCard */
QLabel[role="cardIcon"] {{
    border-radius: 10px;
    padding: 8px;
    min-width: 40px;
    min-height: 40px;
}}

/* Action buttons — add / delete */
QPushButton.addBtn {{
    background-color: #26A65B; /* vivid green */
    color: white;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 700;
}}

QPushButton.deleteBtn {{
    background-color: #E14D4D; /* red */
    color: white;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 700;
}}

/* Flat small buttons (e.g., refresh/search) */
QPushButton#flatBtn {{
    background: transparent;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid rgba(16,24,40,0.04);
    border-radius: 10px;
    padding: 6px 10px;
}}

/* Primary action buttons: gradient */
QPushButton {{
    border-radius: 10px;
}}
QPushButton#flatBtn, QPushButton#successBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY}, stop:1 {COLOR_PRIMARY_DARK});
    color: white;
    padding: 10px 16px;
}}
QPushButton#dangerBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_DANGER}, stop:1 {COLOR_DANGER_DARK});
    color: white;
    padding: 10px 16px;
}}

/* Metric cards */
/* Metric cards */
QFrame#metricCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
    padding: 16px;
}}
QFrame#metricCard[variant="accent"] {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
}}
QFrame#metricCard QLabel {{
    color: {COLOR_TEXT_MUTED};
}}

QDialog {{
    background-color: {COLOR_BG};
}}

QMessageBox {{
    background-color: {COLOR_CARD};
}}
QMessageBox QLabel {{
    color: {COLOR_TEXT};
}}
QMessageBox QPushButton {{
    min-width: 96px;
}}

/* ---------- اسکرول‌بار ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 11px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER_STRONG};
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: #a9aebb;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 11px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER_STRONG};
    border-radius: 5px;
    min-width: 28px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""