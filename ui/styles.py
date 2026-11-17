"""توکن‌ها و استایل سراسری رابط کاربری.

QSS یک‌بار در ``run_app`` اعمال می‌شود. برای سایه‌ها از ``apply_shadow``
در ui.widgets استفاده کنید؛ QSS از box-shadow پشتیبانی نمی‌کند.
"""

# Colors
COLOR_PRIMARY = "#4F46E5"
COLOR_PRIMARY_HOVER = "#4338CA"
COLOR_PRIMARY_LIGHT = "#EEF2FF"
COLOR_BG = "#F9FAFB"
COLOR_SURFACE = "#FFFFFF"
COLOR_BORDER = "#E5E7EB"
COLOR_BORDER_STRONG = "#D1D5DB"
COLOR_TEXT_PRIMARY = "#111827"
COLOR_TEXT_SECONDARY = "#6B7280"
COLOR_SUCCESS = "#16A34A"
COLOR_DANGER = "#DC2626"
COLOR_WARNING = "#D97706"

# Compatibility names used by the existing UI modules. New code should use the
# names above, which are the design-system source of truth.
COLOR_CARD = COLOR_SURFACE
COLOR_CARD_ALT = "#F3F4F6"
COLOR_TEXT = COLOR_TEXT_PRIMARY
COLOR_TEXT_DARK = COLOR_TEXT_PRIMARY
COLOR_TEXT_MUTED = COLOR_TEXT_SECONDARY
COLOR_TEXT_FAINT = "#9CA3AF"
COLOR_CHART_TEXT = COLOR_TEXT_SECONDARY
COLOR_PRIMARY_DARK = COLOR_PRIMARY_HOVER
COLOR_PRIMARY_DARKER = COLOR_PRIMARY_HOVER
COLOR_SUCCESS_DARK = COLOR_SUCCESS
COLOR_SUCCESS_LIGHT = "#F0FDF4"
COLOR_DANGER_LIGHT = "#FEF2F2"
COLOR_WARNING_LIGHT = "#FFFBEB"
COLOR_INFO = "#0284C7"
COLOR_INFO_LIGHT = "#F0F9FF"

# Spacing (multiples of four only)
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_XXL = 32

RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16

APP_STYLE = f"""
* {{ outline: none; }}
QMainWindow, QWidget {{
    background: {COLOR_BG}; color: {COLOR_TEXT_PRIMARY};
    font-family: "Vazirmatn", "Segoe UI", Tahoma, sans-serif; font-size: 13px;
}}
QToolTip {{ background: {COLOR_TEXT_PRIMARY}; color: white; border: none;
    border-radius: {RADIUS_SM}px; padding: {SPACE_SM}px; font-size: 11px; }}
QMenuBar, QToolBar {{ background: {COLOR_SURFACE}; border-bottom: 1px solid {COLOR_BORDER}; padding: {SPACE_XS}px; }}
QMenuBar::item {{ padding: {SPACE_SM}px {SPACE_LG}px; border-radius: {RADIUS_SM}px; }}
QMenuBar::item:selected, QMenu::item:selected {{ background: {COLOR_PRIMARY_LIGHT}; color: {COLOR_PRIMARY}; }}
QMenu {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px; padding: {SPACE_XS}px; }}
QMenu::item {{ padding: {SPACE_SM}px {SPACE_XL}px; border-radius: {RADIUS_SM}px; }}

QPushButton {{ background: {COLOR_PRIMARY}; color: white; border: none; border-radius: {RADIUS_SM}px;
    min-height: 32px; padding: {SPACE_SM}px {SPACE_LG}px; font-weight: 600; }}
QPushButton:hover {{ background: {COLOR_PRIMARY_HOVER}; }}
QPushButton:disabled {{ background: {COLOR_BORDER_STRONG}; color: {COLOR_TEXT_SECONDARY}; }}
QPushButton#flatBtn {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {COLOR_BORDER}; }}
QPushButton#flatBtn:hover {{ background: {COLOR_PRIMARY_LIGHT}; border-color: {COLOR_PRIMARY}; color: {COLOR_PRIMARY}; }}
QPushButton#successBtn {{ background: {COLOR_SUCCESS}; }}
QPushButton#dangerBtn {{ background: {COLOR_DANGER}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{ background: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_SM}px; min-height: 32px; padding: {SPACE_SM}px {SPACE_MD}px;
    selection-background-color: {COLOR_PRIMARY}; selection-color: white; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QDateEdit:focus {{ border-color: {COLOR_PRIMARY}; }}
QComboBox::drop-down {{ border: none; width: {SPACE_XL}px; }}
QComboBox QAbstractItemView {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; selection-background-color: {COLOR_PRIMARY_LIGHT}; selection-color: {COLOR_TEXT_PRIMARY}; }}

QTableWidget, QTreeWidget {{ background: {COLOR_SURFACE}; alternate-background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px; gridline-color: {COLOR_BORDER}; }}
QTableWidget::item {{ padding: {SPACE_SM}px {SPACE_MD}px; border-bottom: 1px solid {COLOR_BORDER}; }}
QTableWidget::item:selected, QTreeWidget::item:selected {{ background: {COLOR_PRIMARY_LIGHT}; color: {COLOR_TEXT_PRIMARY}; }}
QHeaderView::section {{ background: {COLOR_SURFACE}; color: {COLOR_TEXT_SECONDARY}; border: none;
    border-bottom: 1px solid {COLOR_BORDER}; padding: {SPACE_SM}px {SPACE_MD}px; font-weight: 600; font-size: 11px; }}
QTreeWidget::item {{ padding: {SPACE_SM}px; border-radius: {RADIUS_SM}px; }}

QGroupBox {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px;
    margin-top: {SPACE_LG}px; padding: {SPACE_LG}px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; padding: 0 {SPACE_SM}px; color: {COLOR_TEXT_PRIMARY}; }}
QLabel#titleLabel {{ color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 700; }}
QLabel#subtitleLabel {{ color: {COLOR_TEXT_SECONDARY}; font-size: 11px; }}
QLabel#sectionLabel {{ color: {COLOR_TEXT_PRIMARY}; font-size: 15px; font-weight: 600; }}
QLabel#balanceLabel {{ color: {COLOR_SUCCESS}; font-size: 20px; font-weight: 700; }}
QFrame#contentCard, QFrame#appHeader {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_LG}px; }}
QFrame#metricCard, QFrame#chartCard {{ background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px; }}
QLabel#metricTitle {{ color: {COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 600; }}
QLabel#metricValue {{ color: {COLOR_TEXT_PRIMARY}; font-size: 20px; font-weight: 700; }}
QLabel#metricUnit, QLabel#chartLegendLabel {{ color: {COLOR_TEXT_SECONDARY}; font-size: 11px; }}
QWidget#monthlyBarChart {{ background: {COLOR_SURFACE}; }}

QFrame#rightSidebar {{ background: {COLOR_SURFACE}; border-left: 1px solid {COLOR_BORDER}; }}
QPushButton#sidebarLogo {{ background: transparent; color: {COLOR_TEXT_PRIMARY}; text-align: right; font-size: 15px; font-weight: 700; padding: {SPACE_SM}px; }}
QPushButton#sidebarSection {{ background: transparent; color: {COLOR_TEXT_SECONDARY}; border: none; text-align: right; font-size: 11px; padding: {SPACE_SM}px; }}
QPushButton#sidebarItem {{ background: transparent; color: {COLOR_TEXT_PRIMARY}; border: none; text-align: right;
    min-height: 32px; padding: {SPACE_SM}px; border-radius: {RADIUS_SM}px; }}
QPushButton#sidebarItem:hover {{ background: {COLOR_PRIMARY_LIGHT}; color: {COLOR_PRIMARY}; }}
QPushButton#sidebarItem:checked {{ background: {COLOR_PRIMARY_LIGHT}; color: {COLOR_PRIMARY}; font-weight: 600; }}
QPushButton#sidebarItem QLabel, QPushButton#sidebarItem QLabel#sidebarItemText, QPushButton#sidebarItem QLabel#sidebarItemIcon {{ background: transparent; border: none; color: inherit; }}
QPushButton#sidebarCollapse, QPushButton#sidebarProfile, QPushButton#sidebarTheme {{ background: transparent; color: {COLOR_TEXT_SECONDARY}; border: 1px solid {COLOR_BORDER}; padding: {SPACE_SM}px; }}
QTabWidget::pane {{ border: 1px solid {COLOR_BORDER}; border-radius: {RADIUS_MD}px; background: {COLOR_SURFACE}; }}
QTabBar::tab {{ color: {COLOR_TEXT_SECONDARY}; padding: {SPACE_SM}px {SPACE_MD}px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {COLOR_PRIMARY}; border-bottom-color: {COLOR_PRIMARY}; font-weight: 600; }}
QScrollBar:vertical {{ width: {SPACE_MD}px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {COLOR_BORDER_STRONG}; border-radius: {RADIUS_SM}px; min-height: {SPACE_XL}px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

# Added after the light stylesheet so controls keep the same geometry while
# only their visual tokens change. It avoids translucent layers and blur.
DARK_APP_STYLE = APP_STYLE + f"""
QMainWindow, QWidget {{ background: #111827; color: #F9FAFB; }}
QMenuBar, QToolBar, QMenu, QDialog, QMessageBox {{ background: #111827; color: #F9FAFB; border-color: #374151; }}
QMenuBar::item:selected, QMenu::item:selected, QPushButton#sidebarItem:checked {{ background: #312E81; color: #E0E7FF; }}
QPushButton {{ background: {COLOR_PRIMARY}; color: white; }}
QPushButton:hover {{ background: {COLOR_PRIMARY_HOVER}; }}
QPushButton#flatBtn, QPushButton#sidebarCollapse, QPushButton#sidebarProfile, QPushButton#sidebarTheme {{ background: #1F2937; color: #F9FAFB; border-color: #374151; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{ background: #1F2937; color: #F9FAFB; border-color: #374151; }}
QComboBox QAbstractItemView {{ background: #1F2937; color: #F9FAFB; border-color: #374151; }}
QTableWidget, QTreeWidget, QGroupBox, QFrame#contentCard, QFrame#appHeader {{ background: #1F2937; color: #F9FAFB; border-color: #374151; }}
QFrame#metricCard, QFrame#chartCard {{ background: #1E293B; border-color: #334155; }}
QFrame#chartCard QWidget#monthlyBarChart {{ background: #1E293B; }}
QLabel#metricTitle, QLabel#metricUnit, QLabel#chartLegendLabel {{ color: #CBD5E1; }}
QLabel#metricValue {{ color: #F8FAFC; }}
QTableWidget {{ alternate-background-color: #182235; gridline-color: #374151; }}
QTableWidget::item {{ border-bottom-color: #374151; }}
QHeaderView::section {{ background: #1F2937; color: #D1D5DB; border-bottom-color: #374151; }}
QLabel#titleLabel, QLabel#sectionLabel, QGroupBox::title {{ color: #F9FAFB; }}
QLabel#subtitleLabel, QPushButton#sidebarSection {{ color: #9CA3AF; }}
QFrame#rightSidebar {{ background: #111827; border-left-color: #334155; }}
QPushButton#sidebarLogo, QPushButton#sidebarItem {{ color: #F8FAFC; }}
QFrame#rightSidebar QLabel, QFrame#rightSidebar QPushButton#sidebarItem QLabel, QFrame#rightSidebar QLabel#sidebarItemText {{ color: #CBD5E1; background: transparent; }}
QFrame#rightSidebar QPushButton#sidebarItem:checked QLabel, QFrame#rightSidebar QPushButton#sidebarItem:checked QLabel#sidebarItemText {{ color: #FFFFFF; }}
QFrame#rightSidebar QPushButton#sidebarSection, QFrame#rightSidebar QPushButton:disabled {{ color: #94A3B8; }}
QPushButton#sidebarItem:hover {{ background: #1F2937; color: #E0E7FF; }}
QTabWidget::pane {{ background: #1F2937; border-color: #374151; }}
QTabBar::tab {{ color: #9CA3AF; }}
QScrollBar::handle:vertical {{ background: #4B5563; }}
"""


def app_style(dark=False):
    """Return the application stylesheet for the chosen appearance."""
    return DARK_APP_STYLE if dark else APP_STYLE
