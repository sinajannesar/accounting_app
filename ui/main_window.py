"""پنجره اصلی برنامه"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QMenu, QAction,
    QStatusBar, QFileDialog, QApplication,
)

from database.db_manager import DatabaseManager
from models.account import AccountModel
from models.journal import JournalModel
from models.report import ReportModel
from ui.accounts_widget import AccountsWidget
from ui.journal_widget import JournalWidget
from ui.cash_widget import CashWidget
from ui.dashboard_widget import DashboardWidget
from ui.reports.subsidiary_ledger import SubsidiaryLedgerWidget
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
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        self.tabs.addTab(DashboardWidget(self.report_model, self.journal_model, self.db), "داشبورد")
        self.tabs.addTab(AccountsWidget(self.account_model), "سرفصل حساب‌ها")
        self.tabs.addTab(JournalWidget(self.journal_model, self.account_model), "اسناد حسابداری")
        self.tabs.addTab(CashWidget(self.db, self.journal_model, self.account_model), "صندوق")
        self.tabs.addTab(SubsidiaryLedgerWidget(self.report_model, self.account_model), "دفتر معین")
        self.tabs.addTab(GeneralLedgerWidget(self.report_model), "دفتر کل")
        self.tabs.addTab(TrialBalanceWidget(self.report_model), "تراز آزمایشی")
        self.tabs.addTab(IncomeStatementWidget(self.report_model), "سود و زیان")

        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if hasattr(widget, "refresh"):
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
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, "refresh"):
                widget.refresh()

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

    def closeEvent(self, event):
        self.db.close()
        event.accept()


def run_app(db_path=None):
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    window = MainWindow(db_path)
    window.show()
    sys.exit(app.exec_())
