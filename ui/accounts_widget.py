"""صفحه کدینگ حساب‌ها؛ تمام ساختار از دیتابیس خوانده می‌شود."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QDialog, QFormLayout, QComboBox, QCheckBox, QLabel, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QSplitter, QTextEdit, QFrame,
)

from database.db_manager import ACCOUNT_TYPE_LABELS, LEVEL_LABELS
from models.account import AccountModel
from ui.widgets import show_error, show_info, show_confirm, apply_shadow


class AccountDialog(QDialog):
    def __init__(self, account_model, account=None, parent=None):
        super().__init__(parent)
        self.account_model, self.account = account_model, account
        self.setWindowTitle("ویرایش حساب" if account else "حساب جدید")
        self.setMinimumWidth(460); self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        if account: self._load_account()
        else: self._reload_parents()

    def _build_ui(self):
        layout = QFormLayout(self)
        self.code_label = QLabel("پس از انتخاب والد تولید می‌شود")
        self.name_edit = QLineEdit()
        self.level_combo = QComboBox()
        for level in AccountModel.CREATABLE_LEVELS:
            self.level_combo.addItem(LEVEL_LABELS[level], level)
        self.parent_combo = QComboBox()
        self.type_label = QLabel("—")
        self.description_edit = QTextEdit(); self.description_edit.setMaximumHeight(65)
        self.active_check = QCheckBox("فعال"); self.active_check.setChecked(True)
        layout.addRow("کد خودکار:", self.code_label)
        layout.addRow("نام حساب:", self.name_edit)
        layout.addRow("سطح:", self.level_combo)
        layout.addRow("حساب والد:", self.parent_combo)
        layout.addRow("نوع حساب:", self.type_label)
        layout.addRow("توضیحات:", self.description_edit)
        layout.addRow("", self.active_check)
        buttons = QHBoxLayout(); save = QPushButton("✔ ذخیره"); save.setObjectName("successBtn")
        save.clicked.connect(self._save); cancel = QPushButton("انصراف"); cancel.clicked.connect(self.reject)
        buttons.addWidget(save); buttons.addWidget(cancel); layout.addRow(buttons)
        self.level_combo.currentIndexChanged.connect(self._reload_parents)
        self.parent_combo.currentIndexChanged.connect(self._refresh_preview)

    def _reload_parents(self):
        if self.account: return
        level = self.level_combo.currentData()
        self.parent_combo.blockSignals(True); self.parent_combo.clear()
        for item in self.account_model.get_valid_parents(level):
            self.parent_combo.addItem(f"{item['code']} — {item['name']}", item["id"])
        self.parent_combo.blockSignals(False); self._refresh_preview()

    def _refresh_preview(self):
        parent = self.account_model.get_by_id(self.parent_combo.currentData())
        if not parent:
            self.code_label.setText("والد معتبر انتخاب کنید"); self.type_label.setText("—"); return
        self.type_label.setText(AccountModel.type_label(parent["account_type"]))
        try: self.code_label.setText(self.account_model.next_code(parent["id"], self.level_combo.currentData()))
        except ValueError as error: self.code_label.setText(str(error))

    def _load_account(self):
        self.code_label.setText(self.account["code"]); self.name_edit.setText(self.account["name"])
        self.level_combo.setCurrentIndex(self.level_combo.findData(self.account["level"]))
        self.level_combo.setEnabled(False)
        parent = self.account_model.get_by_id(self.account.get("parent_id")) if self.account.get("parent_id") else None
        self.parent_combo.addItem(f"{parent['code']} — {parent['name']}" if parent else "—", self.account.get("parent_id"))
        self.parent_combo.setEnabled(False); self.type_label.setText(AccountModel.type_label(self.account["account_type"]))
        self.description_edit.setPlainText(self.account.get("description") or "")
        self.active_check.setChecked(bool(self.account["is_active"]))

    def _save(self):
        try:
            if self.account:
                self.account_model.update(self.account["id"], self.name_edit.text(), self.active_check.isChecked(), self.description_edit.toPlainText())
            else:
                self.account_model.create(self.name_edit.text(), self.parent_combo.currentData(), self.level_combo.currentData(), self.description_edit.toPlainText())
            self.accept()
        except ValueError as error: show_error(self, str(error))


class AccountsWidget(QWidget):
    def __init__(self, account_model, parent=None):
        super().__init__(parent); self.account_model = account_model; self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        # create title but add it inside content card so table area gets priority
        title = QLabel("کدینگ حساب‌ها")
        title.setObjectName("sectionLabel")
        title.setContentsMargins(0, 0, 0, 2)
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)
        toolbar.addWidget(QLabel("گروه:")); self.group_combo = QComboBox(); self.group_combo.addItem("همه گروه‌ها", None)
        for key, label in ACCOUNT_TYPE_LABELS.items(): self.group_combo.addItem(label, key)
        self.group_combo.currentIndexChanged.connect(self.refresh); toolbar.addWidget(self.group_combo)
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("جستجو بر اساس کد یا نام…")
        self.search_edit.textChanged.connect(self.refresh); toolbar.addWidget(self.search_edit)
        add = QPushButton("➕ حساب جدید"); add.setObjectName("successBtn"); add.clicked.connect(self._add)
        edit = QPushButton("✏ ویرایش"); edit.clicked.connect(self._edit)
        delete = QPushButton("🗑 حذف"); delete.setObjectName("dangerBtn"); delete.clicked.connect(self._delete)
        toolbar.addWidget(add); toolbar.addWidget(edit); toolbar.addWidget(delete)
        splitter = QSplitter(Qt.Horizontal)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["کد", "نام حساب", "سطح", "نوع", "وضعیت"]); self.tree.setColumnWidth(1, 250)
        self.tree.itemDoubleClicked.connect(lambda *_: self._edit())
        self.table = QTableWidget(); self.table.setColumnCount(5); self.table.setHorizontalHeaderLabels(["کد", "نام حساب", "سطح", "نوع", "وضعیت"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(lambda *_: self._edit())

        # Wrap toolbar and content in a card to visually separate from page background
        content_card = QFrame()
        content_card.setObjectName("contentCard")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(2, 2, 2, 4)
        content_layout.setSpacing(6)
        # subtle shadow to lift the card from the background
        try:
            apply_shadow(content_card)
        except Exception:
            pass
        # add smaller title inside content card
        content_layout.addWidget(title)
        content_layout.addLayout(toolbar)
        splitter.addWidget(self.tree); splitter.addWidget(self.table); splitter.setSizes([280, 720])
        # give table more vertical room
        self.table.setMinimumHeight(320)
        content_layout.addWidget(splitter)
        # let splitter expand to take remaining vertical space
        content_layout.setStretch(content_layout.count() - 1, 1)
        layout.addWidget(content_card)

    def refresh(self):
        accounts = self.account_model.get_all(self.search_edit.text().strip(), active_only=False, account_type=self.group_combo.currentData())
        self._fill_tree(accounts); self._fill_table(accounts)

    def _fill_tree(self, accounts):
        self.tree.clear(); children = {}
        ids = {a["id"] for a in accounts}
        for account in accounts: children.setdefault(account["parent_id"] if account["parent_id"] in ids else 0, []).append(account)
        self._add_tree_items(None, 0, children); self.tree.expandToDepth(1)

    def _add_tree_items(self, parent_item, parent_id, children):
        for account in children.get(parent_id, []):
            status = "فعال" if account["is_active"] else "غیرفعال"
            item = QTreeWidgetItem([account["code"], account["name"], AccountModel.level_label(account["level"]), AccountModel.type_label(account["account_type"]), status])
            item.setData(0, Qt.UserRole, account["id"])
            (parent_item.addChild(item) if parent_item else self.tree.addTopLevelItem(item)); self._add_tree_items(item, account["id"], children)

    def _fill_table(self, accounts):
        self.table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            values = [account["code"], account["name"], AccountModel.level_label(account["level"]), AccountModel.type_label(account["account_type"]), "فعال" if account["is_active"] else "غیرفعال"]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 4: item.setData(Qt.UserRole, account["id"])
                self.table.setItem(row, column, item)
        # ensure rows expand to show wrapped text for long names
        self.table.resizeRowsToContents()

    def _selected_id(self):
        if self.table.currentRow() >= 0: return self.table.item(self.table.currentRow(), 4).data(Qt.UserRole)
        item = self.tree.currentItem(); return item.data(0, Qt.UserRole) if item else None

    def _add(self):
        if AccountDialog(self.account_model, parent=self).exec_(): self.refresh(); show_info(self, "حساب با موفقیت ایجاد شد")

    def _edit(self):
        account_id = self._selected_id()
        if not account_id: show_error(self, "لطفاً یک حساب انتخاب کنید"); return
        if AccountDialog(self.account_model, self.account_model.get_by_id(account_id), self).exec_(): self.refresh(); show_info(self, "حساب به‌روزرسانی شد")

    def _delete(self):
        account_id = self._selected_id()
        if not account_id: show_error(self, "لطفاً یک حساب انتخاب کنید"); return
        if show_confirm(self, "آیا از حذف این حساب اطمینان دارید؟"):
            try: self.account_model.delete(account_id); self.refresh(); show_info(self, "حساب حذف شد")
            except ValueError as error: show_error(self, str(error))
