"""ماژول سرفصل حساب‌ها"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QDialog, QFormLayout, QComboBox,
    QCheckBox, QLabel, QHeaderView, QTreeWidget, QTreeWidgetItem,
    QSplitter,
)

from database.db_manager import ACCOUNT_TYPE_LABELS, LEVEL_LABELS
from models.account import AccountModel
from ui.widgets import show_error, show_info, show_confirm


class AccountDialog(QDialog):
    def __init__(self, account_model, account=None, parent=None):
        super().__init__(parent)
        self.account_model = account_model
        self.account = account
        self.setWindowTitle("ویرایش حساب" if account else "حساب جدید")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        if account:
            self._load_account()

    def _build_ui(self):
        layout = QFormLayout(self)
        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("— بدون والد —", None)
        for acc in self.account_model.get_all(active_only=False):
            if acc["level"] < 5:
                label = f"{acc['code']} - {acc['name']} ({LEVEL_LABELS[acc['level']]})"
                self.parent_combo.addItem(label, acc["id"])
        self.level_combo = QComboBox()
        for lvl, label in LEVEL_LABELS.items():
            self.level_combo.addItem(label, lvl)
        self.type_combo = QComboBox()
        for key, label in ACCOUNT_TYPE_LABELS.items():
            self.type_combo.addItem(label, key)
        self.active_check = QCheckBox("فعال")
        self.active_check.setChecked(True)

        layout.addRow("کد:", self.code_edit)
        layout.addRow("نام:", self.name_edit)
        layout.addRow("حساب والد:", self.parent_combo)
        layout.addRow("سطح:", self.level_combo)
        layout.addRow("نوع حساب:", self.type_combo)
        layout.addRow("", self.active_check)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ذخیره")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        self.parent_combo.currentIndexChanged.connect(self._on_parent_changed)

    def _on_parent_changed(self):
        parent_id = self.parent_combo.currentData()
        if parent_id:
            parent = self.account_model.get_by_id(parent_id)
            if parent:
                idx = self.level_combo.findData(parent["level"] + 1)
                if idx >= 0:
                    self.level_combo.setCurrentIndex(idx)
                tidx = self.type_combo.findData(parent["account_type"])
                if tidx >= 0:
                    self.type_combo.setCurrentIndex(tidx)

    def _load_account(self):
        self.code_edit.setText(self.account["code"])
        self.name_edit.setText(self.account["name"])
        idx = self.parent_combo.findData(self.account["parent_id"])
        if idx >= 0:
            self.parent_combo.setCurrentIndex(idx)
        self.level_combo.setCurrentIndex(self.level_combo.findData(self.account["level"]))
        self.type_combo.setCurrentIndex(self.type_combo.findData(self.account["account_type"]))
        self.active_check.setChecked(bool(self.account["is_active"]))
        if self.account:
            self.parent_combo.setEnabled(False)
            self.level_combo.setEnabled(False)

    def _save(self):
        try:
            code = self.code_edit.text().strip()
            name = self.name_edit.text().strip()
            if not code or not name:
                raise ValueError("کد و نام الزامی است")
            parent_id = self.parent_combo.currentData()
            level = self.level_combo.currentData()
            acc_type = self.type_combo.currentData()
            if self.account:
                self.account_model.update(
                    self.account["id"], code, name, acc_type, self.active_check.isChecked()
                )
            else:
                self.account_model.create(code, name, parent_id, level, acc_type)
            self.accept()
        except ValueError as e:
            show_error(self, str(e))


class AccountsWidget(QWidget):
    def __init__(self, account_model, parent=None):
        super().__init__(parent)
        self.account_model = account_model
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("جستجو بر اساس کد یا نام...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit)

        add_btn = QPushButton("حساب جدید")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("ویرایش")
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("حذف")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["کد", "نام", "سطح", "نوع"])
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 250)
        self.tree.itemDoubleClicked.connect(lambda: self._edit())

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["کد", "نام", "سطح", "نوع", "وضعیت"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(lambda: self._edit())

        splitter.addWidget(self.tree)
        splitter.addWidget(self.table)
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)

    def refresh(self):
        search = self.search_edit.text().strip()
        accounts = self.account_model.get_all(search=search, active_only=False)
        self._fill_tree(accounts)
        self._fill_table(accounts)

    def _fill_tree(self, accounts):
        self.tree.clear()
        by_parent = {}
        for acc in accounts:
            pid = acc["parent_id"] or 0
            by_parent.setdefault(pid, []).append(acc)
        self._add_tree_items(None, 0, by_parent)

    def _add_tree_items(self, parent_item, parent_id, by_parent):
        for acc in by_parent.get(parent_id, []):
            item = QTreeWidgetItem([
                acc["code"], acc["name"],
                AccountModel.level_label(acc["level"]),
                AccountModel.type_label(acc["account_type"]),
            ])
            item.setData(0, Qt.UserRole, acc["id"])
            if parent_item:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            self._add_tree_items(item, acc["id"], by_parent)

    def _fill_table(self, accounts):
        self.table.setRowCount(len(accounts))
        for row, acc in enumerate(accounts):
            self.table.setItem(row, 0, QTableWidgetItem(acc["code"]))
            self.table.setItem(row, 1, QTableWidgetItem(acc["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(AccountModel.level_label(acc["level"])))
            self.table.setItem(row, 3, QTableWidgetItem(AccountModel.type_label(acc["account_type"])))
            status = "فعال" if acc["is_active"] else "غیرفعال"
            item = QTableWidgetItem(status)
            item.setData(Qt.UserRole, acc["id"])
            self.table.setItem(row, 4, item)

    def _selected_id(self):
        rows = self.table.selectedItems()
        if rows:
            return self.table.item(self.table.currentRow(), 4).data(Qt.UserRole)
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return None

    def _add(self):
        dlg = AccountDialog(self.account_model, parent=self)
        if dlg.exec_():
            self.refresh()
            show_info(self, "حساب با موفقیت ایجاد شد")

    def _edit(self):
        acc_id = self._selected_id()
        if not acc_id:
            show_error(self, "لطفاً یک حساب انتخاب کنید")
            return
        account = self.account_model.get_by_id(acc_id)
        dlg = AccountDialog(self.account_model, account, parent=self)
        if dlg.exec_():
            self.refresh()
            show_info(self, "حساب با موفقیت ویرایش شد")

    def _delete(self):
        acc_id = self._selected_id()
        if not acc_id:
            show_error(self, "لطفاً یک حساب انتخاب کنید")
            return
        if not show_confirm(self, "آیا از حذف این حساب اطمینان دارید؟"):
            return
        try:
            self.account_model.delete(acc_id)
            self.refresh()
            show_info(self, "حساب حذف شد")
        except ValueError as e:
            show_error(self, str(e))
