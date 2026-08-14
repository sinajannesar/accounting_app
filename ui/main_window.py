"""پنجره اصلی برنامه"""

import sys

from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu, QAction,
    QStatusBar, QFileDialog, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QStyle, QLabel, QBoxLayout,
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QSizePolicy
import os

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
from ui.settings_widget import SettingsWidget
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

        # avoid emoji in window title
        self.setWindowTitle("نرم‌افزار حسابداری")
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
        register_view("settings", SettingsWidget())

        # breadcrumb mapping for header
        self._breadcrumb_map = {
            'dashboard': 'داشبورد',
            'journal': 'عملیات / اسناد حسابداری',
            'cash': 'عملیات / صندوق',
            'accounts': 'حسابداری / سرفصل حساب‌ها',
            'subsidiary': 'حسابداری / دفتر معین',
            'detail_ledger': 'حسابداری / دفتر تفصیلی',
            'general_ledger': 'حسابداری / دفتر کل',
            'trial_balance': 'گزارش‌ها / تراز آزمایشی',
            'income_statement': 'گزارش‌ها / سود و زیان',
            'settings': 'تنظیمات',
        }

        # build central widget with left sidebar and content area
        central = QWidget()
        # ensure central layout is LTR so widget order stays MainContent | Sidebar
        central.setLayoutDirection(Qt.LeftToRight)
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 18, 16, 18)
        sidebar_layout.setSpacing(6)
        sidebar.setLayoutDirection(Qt.RightToLeft)

        # track collapsed state
        self._sidebar_collapsed = False

        # Header / logo area
        logo = QPushButton("نرم‌افزار حسابداری")
        logo.setObjectName("sidebarLogo")
        logo.setEnabled(False)
        # use consistent icon set for logo
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        logo_path = os.path.join(icons_dir, "logo.svg")
        if os.path.exists(logo_path):
            logo.setIcon(QIcon(logo_path))
            logo.setIconSize(QSize(28, 28))
        sidebar_layout.addWidget(logo)

        # Navigation groups and items
        def add_section_label(text):
            lbl = QPushButton(text)
            lbl.setObjectName("sidebarSection")
            lbl.setEnabled(False)
            lbl.setLayoutDirection(Qt.RightToLeft)
            sidebar_layout.addWidget(lbl)
            return lbl

        def add_nav_item(text, key, icon=None, indent=0):
            # Use a QPushButton as a container but render icon+text using child QLabel
            # This avoids relying on QPushButton.setIcon() which can interfere with
            # text alignment across platforms.
            btn = QPushButton()
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setProperty("navKey", key)
            btn.setProperty("fullText", text)
            btn.setLayoutDirection(Qt.RightToLeft)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setText("")

            # inner layout: icon (QLabel) + text (QLabel) + stretch
            inner = QHBoxLayout()
            inner.setContentsMargins(8, 6, 8, 6)
            inner.setSpacing(8)
            inner.setDirection(QBoxLayout.RightToLeft)
            btn.setLayout(inner)

            icon_label = QLabel()
            icon_label.setObjectName("sidebarItemIcon")
            icon_label.setFixedSize(28, 28)
            icon_label.setAlignment(Qt.AlignCenter)

            # resolve icon pixmap
            if icon is None:
                icon_path = os.path.join(os.path.dirname(__file__), "icons", "report.svg")
                icon_src = icon_path if os.path.exists(icon_path) else None
            elif isinstance(icon, QIcon):
                icon_src = icon
            else:
                icon_src = icon

            pix = None
            try:
                if isinstance(icon_src, QIcon):
                    pix = icon_src.pixmap(QSize(22, 22))
                elif isinstance(icon_src, str) and os.path.exists(icon_src):
                    pix = QIcon(icon_src).pixmap(QSize(22, 22))
            except Exception:
                pix = None
            if pix and not pix.isNull():
                icon_label.setPixmap(pix)

            text_label = QLabel(text)
            text_label.setObjectName("sidebarItemText")
            text_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            inner.addWidget(icon_label)
            inner.addWidget(text_label)
            inner.addStretch()

            btn.clicked.connect(lambda _, k=key: self.show_view(k))
            sidebar_layout.addWidget(btn)
            return btn

        # top-level items
        # prepare a few standard icons for nav (fallback to platform icons)
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        ic_dashboard = os.path.join(icons_dir, "home.svg")
        ic_journal = os.path.join(icons_dir, "journal.svg")
        ic_cash = os.path.join(icons_dir, "cash.svg")
        ic_accounts = os.path.join(icons_dir, "accounts.svg")
        ic_ledger = os.path.join(icons_dir, "ledger.svg")
        ic_report = os.path.join(icons_dir, "report.svg")
        ic_settings = os.path.join(icons_dir, "settings.svg")

        add_nav_item("داشبورد", "dashboard", icon=ic_dashboard)
        add_section_label("عملیات")
        add_nav_item("اسناد حسابداری", "journal", icon=ic_journal, indent=12)
        add_nav_item("صندوق", "cash", icon=ic_cash, indent=12)
        add_section_label("حسابداری")
        add_nav_item("سرفصل حساب‌ها", "accounts", icon=ic_accounts, indent=12)
        add_nav_item("دفتر معین", "subsidiary", icon=ic_ledger, indent=12)
        add_nav_item("دفتر تفصیلی", "detail_ledger", icon=ic_ledger, indent=12)
        add_nav_item("دفتر کل", "general_ledger", icon=ic_ledger, indent=12)
        add_section_label("گزارش‌ها")
        add_nav_item("تراز آزمایشی", "trial_balance", icon=ic_report, indent=12)
        add_nav_item("سود و زیان", "income_statement", icon=ic_report, indent=12)

        sidebar_layout.addStretch()
        # footer actions
        add_nav_item("تنظیمات", "settings", icon=ic_settings)

        # collapse toggle and profile
        collapse_btn = QPushButton()
        collapse_btn.setObjectName("sidebarCollapse")
        collapse_btn.setCheckable(True)
        collapse_icon = os.path.join(os.path.dirname(__file__), "icons", "collapse.svg")
        if os.path.exists(collapse_icon):
            collapse_btn.setIcon(QIcon(collapse_icon))
        collapse_btn.setIconSize(QSize(18, 18))
        sidebar_layout.addWidget(collapse_btn)

        profile = QPushButton()
        profile.setObjectName("sidebarProfile")
        profile_icon = os.path.join(os.path.dirname(__file__), "icons", "accounts.svg")
        if os.path.exists(profile_icon):
            profile.setIcon(QIcon(profile_icon))
        profile.setFixedHeight(40)
        sidebar_layout.addWidget(profile)

        # keep reference to sidebar and buttons for collapse behavior
        self._sidebar = sidebar
        # collect nav buttons (those with navKey property)
        self._sidebar_buttons = [w for w in sidebar.findChildren(QPushButton) if w.property('navKey')]
        # use clicked to drive the toggle explicitly (avoid RTL mirroring issues)
        collapse_btn.clicked.connect(lambda: self._toggle_sidebar(not self._sidebar_collapsed))
        self._collapse_btn = collapse_btn

        # initialize sidebar state (expanded)
        self._apply_sidebar_state(self._sidebar_collapsed)
        # set collapsed property on sidebar for stylesheet to use
        self._sidebar.setProperty('collapsed', 'false')

        # right content area with header + stack
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 18, 24, 18)
        right_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("appHeader")
        header.setMinimumHeight(64)
        # build header contents: breadcrumb (right), actions (left)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        # breadcrumb (right side)
        breadcrumb = QLabel("")
        breadcrumb.setObjectName("breadcrumbLabel")
        breadcrumb.setText("")
        header_layout.addWidget(breadcrumb, 1)
        # header shows breadcrumb/title only (remove icon buttons)
        header_layout.addSpacing(6)

        right_layout.addWidget(header)
        right_layout.addWidget(self.stack, 1)

        # place the main content first then sidebar so sidebar appears on the right
        central_layout.addWidget(right, 1)
        central_layout.addWidget(sidebar)

        # sidebar width animation: animate both minimumWidth and maximumWidth together
        self._sidebar_anim_group = QParallelAnimationGroup(self)
        self._sidebar_anim_min = QPropertyAnimation(self._sidebar, b"minimumWidth")
        self._sidebar_anim_max = QPropertyAnimation(self._sidebar, b"maximumWidth")
        for a in (self._sidebar_anim_min, self._sidebar_anim_max):
            a.setDuration(240)
            a.setEasingCurve(QEasingCurve.InOutCubic)
            self._sidebar_anim_group.addAnimation(a)

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
        # allow registered views (settings is now a real view)
        idx = self.view_map.get(key)
        if idx is None:
            return
        self.stack.setCurrentIndex(idx)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()
        # update sidebar buttons' checked state so only current is active
        try:
            for btn in getattr(self, '_sidebar_buttons', []):
                nav = btn.property('navKey')
                btn.setChecked(nav == key)
        except Exception:
            pass
        # update breadcrumb in header
        bc = self.findChild(QLabel, "breadcrumbLabel")
        if bc is not None:
            bc.setText(self._breadcrumb_map.get(key, ""))

    def _toggle_sidebar(self, collapsed: bool):
        """Toggle sidebar collapsed state: update visuals and layout (not just width)."""
        # flip state
        self._sidebar_collapsed = bool(collapsed)

        # If collapsing: immediately switch to icon-only visuals, then animate width
        if self._sidebar_collapsed:
            # apply visuals immediately: hide labels, set tooltips
            for btn in getattr(self, '_sidebar_buttons', []):
                full = btn.property('fullText') or ""
                btn.setProperty('fullText', full)
                # hide the text label and center the icon label
                text_lbl = btn.findChild(QLabel, "sidebarItemText")
                icon_lbl = btn.findChild(QLabel, "sidebarItemIcon")
                if text_lbl:
                    text_lbl.hide()
                if icon_lbl:
                    icon_lbl.setAlignment(Qt.AlignCenter)
                btn.setToolTip(full)
                btn.setFixedHeight(48)
            # logo compact
            logo = self.findChild(QPushButton, "sidebarLogo")
            if logo:
                logo.setText("")
                logo.setToolTip("نرم‌افزار حسابداری")

        # animate width between expanded and collapsed values (min & max)
        current_min = self._sidebar.minimumWidth() or 240
        current_max = self._sidebar.maximumWidth() or 260
        start_min = current_min
        start_max = current_max
        end_min = 76 if self._sidebar_collapsed else 240
        end_max = 76 if self._sidebar_collapsed else 260

        # stop previous animations
        try:
            self._sidebar_anim_group.stop()
        except Exception:
            pass

        self._sidebar_anim_min.setStartValue(start_min)
        self._sidebar_anim_min.setEndValue(end_min)
        self._sidebar_anim_max.setStartValue(start_max)
        self._sidebar_anim_max.setEndValue(end_max)

        # disconnect any previous finished handlers
        try:
            self._sidebar_anim_group.finished.disconnect()
        except Exception:
            pass

        def on_finished():
            # apply final visual adjustments after animation
            self._apply_sidebar_state(self._sidebar_collapsed)

        self._sidebar_anim_group.finished.connect(on_finished)
        self._sidebar_anim_group.start()

    def _apply_sidebar_state(self, collapsed: bool):
        # width
        if collapsed:
            w = 76
            # enforce min/max to collapsed width and prefer fixed-like sizing
            self._sidebar.setMinimumWidth(w)
            self._sidebar.setMaximumWidth(w)
            self._sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        else:
            self._sidebar.setMinimumWidth(240)
            self._sidebar.setMaximumWidth(260)
            # restore flexible sizing
            self._sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # logo behaviour
        logo = self.findChild(QPushButton, "sidebarLogo")
        if logo:
            if collapsed:
                # show only icon
                logo.setText("")
                logo.setToolTip("نرم‌افزار حسابداری")
                logo_path = os.path.join(os.path.dirname(__file__), "icons", "logo.svg")
                if os.path.exists(logo_path):
                    logo.setIcon(QIcon(logo_path))
                    logo.setIconSize(QSize(28, 28))
                logo.setEnabled(False)
            else:
                logo_path = os.path.join(os.path.dirname(__file__), "icons", "logo.svg")
                if os.path.exists(logo_path):
                    logo.setIcon(QIcon(logo_path))
                    logo.setIconSize(QSize(28, 28))
                logo.setText("نرم‌افزار حسابداری")
                logo.setToolTip("")

        # set property for stylesheet rules
        self._sidebar.setProperty('collapsed', 'true' if collapsed else 'false')
        self._sidebar.style().unpolish(self._sidebar)
        self._sidebar.style().polish(self._sidebar)

        # nav buttons: show/hide labels and adjust icon-only styling
        for btn in getattr(self, '_sidebar_buttons', []):
            full = btn.property('fullText') or btn.text()
            if collapsed:
                # store full text and hide label (styling via stylesheet)
                btn.setProperty('fullText', full)
                text_lbl = btn.findChild(QLabel, "sidebarItemText")
                icon_lbl = btn.findChild(QLabel, "sidebarItemIcon")
                if text_lbl:
                    text_lbl.hide()
                if icon_lbl:
                    icon_lbl.setAlignment(Qt.AlignCenter)
                btn.setToolTip(full)
                btn.setFixedHeight(48)
            else:
                # show text label and restore layout/alignment
                text_lbl = btn.findChild(QLabel, "sidebarItemText")
                icon_lbl = btn.findChild(QLabel, "sidebarItemIcon")
                if text_lbl:
                    text_lbl.show()
                    text_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if icon_lbl:
                    icon_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                btn.setToolTip("")
                btn.setFixedHeight(36)

        # active visual for collapsed mode: find checked button and adjust style
        # active state is handled via stylesheet selectors; ensure checked state preserved
        # no inline style changes here
        # ensure collapse button checked state matches
        if self._collapse_btn:
            self._collapse_btn.setChecked(collapsed)

        # collapse button icon
        if self._collapse_btn:
            collapse_icon = os.path.join(os.path.dirname(__file__), "icons", "collapse.svg")
            expand_icon = os.path.join(os.path.dirname(__file__), "icons", "expand.svg")
            if collapsed:
                if os.path.exists(expand_icon):
                    self._collapse_btn.setIcon(QIcon(expand_icon))
            else:
                if os.path.exists(collapse_icon):
                    self._collapse_btn.setIcon(QIcon(collapse_icon))

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
