"""پنجره اصلی برنامه"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu, QAction,
    QStatusBar, QFileDialog, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton,
)

from database.db_manager import DatabaseManager
from models.account import AccountModel
from models.journal import JournalModel
from models.report import ReportModel
from ui.accounts_widget import AccountsWidget
from ui.journal_widget import JournalWidget
from ui.cash_widget import CashWidget
from ui.dashboard_widget import DashboardWidget
from ui.reports.subsidiary_ledger import SubsidiaryLedgerWidget, DetailLedgerWidget
from ui.reports.general_ledger import GeneralLedgerWidget
from ui.reports.trial_balance import TrialBalanceWidget
from ui.reports.income_statement import IncomeStatementWidget
from ui.styles import APP_STYLE
from ui.widgets import show_info, show_error, show_confirm, format_amount
from utils.backup import restore_database
from utils.jalali import today_jalali, jalali_str_add_days


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.db = DatabaseManager(db_path)
        self.db.initialize()

        self.account_model = AccountModel(self.db)
        self.journal_model = JournalModel(self.db)
        self.report_model = ReportModel(self.db, self.account_model)

        self.setWindowTitle("💼 نرم‌افزار حسابداری")
        self.setMinimumSize(1000, 650)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(APP_STYLE)

        self._build_menu()
        self._build_tabs()
        self.statusBar().showMessage("آماده")
        self._check_due_reminders()

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("فایل")

        backup_action = QAction("پشتیبان‌گیری", self)
        backup_action.triggered.connect(self._backup)
        file_menu.addAction(backup_action)

        restore_action = QAction("بازیابی", self)
        restore_action.triggered.connect(self._restore)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()
        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("راهنما")
        about_action = QAction("درباره", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _build_tabs(self):
        # Create tabs and a left sidebar for navigation (visual parity with reference)
        # Use a single navigation system: Sidebar + QStackedWidget
        from PyQt5.QtWidgets import QStackedWidget

        self.stack = QStackedWidget()
        self.stack.setLayoutDirection(Qt.RightToLeft)

        # create views and register them in a map
        self.view_map = {}

        def register_view(key, widget):
            idx = self.stack.addWidget(widget)
            self.view_map[key] = idx

        register_view("dashboard", DashboardWidget(self.report_model, self.journal_model, self.db))
        register_view("accounts", AccountsWidget(self.account_model))
        register_view("journal", JournalWidget(self.journal_model, self.account_model))
        register_view("cash", CashWidget(self.db, self.journal_model, self.account_model))
        register_view("subsidiary", SubsidiaryLedgerWidget(self.report_model, self.account_model))
        register_view("detail_ledger", DetailLedgerWidget(self.report_model, self.account_model))
        register_view("general_ledger", GeneralLedgerWidget(self.report_model))
        register_view("trial_balance", TrialBalanceWidget(self.report_model))
        register_view("income_statement", IncomeStatementWidget(self.report_model))

        # build central widget with left sidebar and content area
        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 18, 16, 18)
        sidebar_layout.setSpacing(6)

        # Header / logo area
        logo = QPushButton("نرم‌افزار حسابداری")
        logo.setObjectName("sidebarLogo")
        logo.setEnabled(False)
        logo.setStyleSheet("text-align: right; padding: 8px")
        sidebar_layout.addWidget(logo)

        # Navigation groups and items
        def add_section_label(text):
            lbl = QPushButton(text)
            lbl.setObjectName("sidebarSection")
            lbl.setEnabled(False)
            sidebar_layout.addWidget(lbl)
            return lbl

        def add_nav_item(text, key, indent=0):
            btn = QPushButton(text)
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setProperty("navKey", key)
            btn.setStyleSheet(f"padding-right: {12 + indent}px; text-align: right;")
            btn.clicked.connect(lambda _, k=key: self.show_view(k))
            sidebar_layout.addWidget(btn)
            return btn

        # top-level items
        add_nav_item("داشبورد", "dashboard")
        add_section_label("عملیات")
        add_nav_item("اسناد حسابداری", "journal", indent=12)
        add_nav_item("صندوق", "cash", indent=12)
        add_section_label("حسابداری")
        add_nav_item("سرفصل حساب‌ها", "accounts", indent=12)
        add_nav_item("دفتر معین", "subsidiary", indent=12)
        add_nav_item("دفتر تفصیلی", "detail_ledger", indent=12)
        add_nav_item("دفتر کل", "general_ledger", indent=12)
        add_section_label("گزارش‌ها")
        add_nav_item("تراز آزمایشی", "trial_balance", indent=12)
        add_nav_item("سود و زیان", "income_statement", indent=12)

        sidebar_layout.addStretch()
        # footer actions
        add_nav_item("تنظیمات", "settings")

        # collapse toggle and profile
        collapse_btn = QPushButton("⟨")
        collapse_btn.setObjectName("sidebarCollapse")
        collapse_btn.setCheckable(True)
        sidebar_layout.addWidget(collapse_btn)

        profile = QPushButton("پروفایل")
        profile.setObjectName("sidebarProfile")
        sidebar_layout.addWidget(profile)

        # keep reference to sidebar and buttons for collapse behavior
        self._sidebar = sidebar
        # collect nav buttons (those with navKey property)
        self._sidebar_buttons = [w for w in sidebar.findChildren(QPushButton) if w.property('navKey')]
        collapse_btn.toggled.connect(self._toggle_sidebar)

        # right content area with header + stack
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 18, 24, 18)
        right_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("appHeader")
        header.setMinimumHeight(64)
        right_layout.addWidget(header)
        right_layout.addWidget(self.stack, 1)

        central_layout.addWidget(sidebar)
        central_layout.addWidget(right, 1)

        self.setCentralWidget(central)

    def _on_tab_changed(self, index):
        # legacy: kept for compatibility if called; refresh current stacked widget
        widget = self.stack.widget(index) if hasattr(self, 'stack') else None
        if widget:
            self._refresh_widget(widget)

    def _refresh_widget(self, widget):
        # refresh QStackedWidget children or direct widgets
        from PyQt5.QtWidgets import QStackedWidget
        if isinstance(widget, QStackedWidget):
            inner = widget.currentWidget()
            self._refresh_widget(inner)
        elif hasattr(widget, "refresh"):
            widget.refresh()

    def _backup(self):
        default_dir = str(self.db.db_path.parent / "backups")
        path, _ = QFileDialog.getSaveFileName(
            self, "پشتیبان‌گیری", default_dir + "/backup.db", "Database (*.db)"
        )
        if path:
            try:
                self.db.backup(path)
                show_info(self, f"پشتیبان با موفقیت ذخیره شد:\n{path}")
            except Exception as e:
                show_error(self, f"خطا در پشتیبان‌گیری: {e}")

    def _restore(self):
        if not show_confirm(self, "بازیابی، داده‌های فعلی را جایگزین می‌کند. ادامه می‌دهید؟"):
            return
        path, _ = QFileDialog.getOpenFileName(self, "بازیابی", "", "Database (*.db)")
        if path:
            try:
                restore_database(self.db, path)
                show_info(self, "بازیابی با موفقیت انجام شد. برنامه را مجدداً راه‌اندازی کنید.")
                self._reload_all()
            except Exception as e:
                show_error(self, f"خطا در بازیابی: {e}")

    def _reload_all(self):
        # iterate all registered views in the stacked widget and refresh if possible
        if hasattr(self, "stack"):
            for i in range(self.stack.count()):
                w = self.stack.widget(i)
                if hasattr(w, "refresh"):
                    w.refresh()

    def _check_due_reminders(self):
        """هشدار اسناد سررسیدشده یا نزدیک به سررسید هنگام باز شدن برنامه"""
        try:
            today = today_jalali()
            upper_bound = jalali_str_add_days(today, 7)
            due_entries = self.journal_model.get_due_entries(as_of_date=upper_bound)
        except Exception:
            return
        if not due_entries:
            return

        overdue = [e for e in due_entries if e["due_date"] < today]
        upcoming = [e for e in due_entries if e["due_date"] >= today]

        lines = []
        if overdue:
            lines.append(f"سررسید گذشته ({len(overdue)} سند):")
            for e in overdue[:10]:
                amount = e["total_debit"] or e["total_credit"]
                lines.append(f"  • سند {e['entry_number']} — سررسید {e['due_date']} — {format_amount(amount)} ریال — {e['description']}")
        if upcoming:
            if lines:
                lines.append("")
            lines.append(f"نزدیک به سررسید تا ۷ روز آینده ({len(upcoming)} سند):")
            for e in upcoming[:10]:
                amount = e["total_debit"] or e["total_credit"]
                lines.append(f"  • سند {e['entry_number']} — سررسید {e['due_date']} — {format_amount(amount)} ریال — {e['description']}")

        show_info(self, "\n".join(lines))

    def _about(self):
        show_info(
            self,
            "نرم‌افزار حسابداری آفلاین\n"
            "نسخه 1.0\n\n"
            "یک برنامه ساده حسابداری برای ویندوز\n"
            "کاملاً آفلاین با پایگاه داده SQLite",
        )

    def show_view(self, key):
        """Switch to the view with the given key and refresh it."""
        if key == "settings":
            show_info(self, "تنظیمات هنوز پیاده‌سازی نشده است")
            return
        idx = self.view_map.get(key)
        if idx is None:
            return
        self.stack.setCurrentIndex(idx)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _toggle_sidebar(self, collapsed: bool):
        """Toggle sidebar collapsed state: adjust width and button labels."""
        if collapsed:
            # collapsed width
            self._sidebar.setMinimumWidth(80)
            self._sidebar.setMaximumWidth(80)
            for btn in self._sidebar_buttons:
                full = btn.text()
                btn.setProperty('fullText', full)
                btn.setToolTip(full)
                btn.setText("")
        else:
            self._sidebar.setMinimumWidth(240)
            self._sidebar.setMaximumWidth(260)
            for btn in self._sidebar_buttons:
                full = btn.property('fullText') or ""
                btn.setText(full)
                btn.setToolTip("")

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def run_app(db_path=None):
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont("Tahoma", 10))
    window = MainWindow(db_path)
    window.show()
    sys.exit(app.exec_())
