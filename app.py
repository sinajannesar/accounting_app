from __future__ import annotations

import hmac
import math
import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

from database.db_manager import DEFAULT_ACCOUNTS
from models.account import AccountModel
from models.report import ReportModel

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "public"
IS_VERCEL = bool(os.environ.get("VERCEL"))
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)
if IS_VERCEL or USE_POSTGRES:
    required_environment = ("SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD", "DATABASE_URL")
    missing_environment = [name for name in required_environment if not os.environ.get(name)]
    if missing_environment:
        raise RuntimeError(
            "Missing required PostgreSQL environment variables: "
            + ", ".join(missing_environment)
        )

if not USE_POSTGRES:
    DB_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "shop.db")))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456")
LOW_STOCK_THRESHOLD = 5
ID_COLUMN = "BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
FLOAT_TYPE = "DOUBLE PRECISION" if USE_POSTGRES else "REAL"
REFERENCE_ID_TYPE = "BIGINT" if USE_POSTGRES else "INTEGER"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "shop-demo-secret-key")


class DatabaseConnection:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self.connection.__exit__(exc_type, exc_value, traceback)
        finally:
            self.connection.close()

    def execute(self, query, parameters=()):
        if USE_POSTGRES:
            query = query.replace("?", "%s")
        return self.connection.execute(query, parameters)


def get_db():
    if USE_POSTGRES:
        return DatabaseConnection(
            psycopg.connect(
                DATABASE_URL,
                row_factory=dict_row,
                connect_timeout=10,
                prepare_threshold=None,
            )
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return DatabaseConnection(conn)


def begin_write_transaction(conn):
    conn.execute("BEGIN" if USE_POSTGRES else "BEGIN IMMEDIATE")


def seed_accounting_accounts(conn):
    account_ids = {}
    for code, name, parent_code, level, account_type in DEFAULT_ACCOUNTS:
        parent_id = account_ids.get(parent_code) if parent_code else None
        conn.execute(
            """
            INSERT INTO accounts (code, name, parent_id, level, account_type)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT (code) DO NOTHING
            """,
            (code, name, parent_id, level, account_type),
        )
        row = conn.execute("SELECT id FROM accounts WHERE code = ?", (code,)).fetchone()
        if row is None:
            raise RuntimeError(f"Failed to initialize accounting account {code}.")
        account_ids[code] = row["id"]


def ensure_db():
    if not USE_POSTGRES:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        begin_write_transaction(conn)
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {ID_COLUMN},
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin'
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS products (
                id {ID_COLUMN},
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                purchase_price {FLOAT_TYPE} DEFAULT 0,
                sale_price {FLOAT_TYPE} DEFAULT 0,
                stock INTEGER DEFAULT 0,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_products_stock_name ON products(stock, name)"
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS customers (
                id {ID_COLUMN},
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                address TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS invoices (
                id {ID_COLUMN},
                invoice_number TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                invoice_date TEXT NOT NULL,
                total_amount {FLOAT_TYPE} NOT NULL,
                paid_amount {FLOAT_TYPE} DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'paid',
                notes TEXT,
                payment_method TEXT NOT NULL DEFAULT 'cash',
                receipt_tracking_number TEXT,
                check_number TEXT,
                check_bank TEXT,
                check_due_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date)"
        )
        if USE_POSTGRES:
            invoice_columns = {
                row["column_name"]
                for row in conn.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = ?",
                    ("invoices",),
                )
            }
        else:
            invoice_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(invoices)")
            }
        invoice_migrations = {
            "payment_method": "TEXT NOT NULL DEFAULT 'cash'",
            "receipt_tracking_number": "TEXT",
            "check_number": "TEXT",
            "check_bank": "TEXT",
            "check_due_date": "TEXT",
        }
        for column, definition in invoice_migrations.items():
            if column not in invoice_columns:
                conn.execute(f"ALTER TABLE invoices ADD COLUMN {column} {definition}")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS invoice_payments (
                id {ID_COLUMN},
                invoice_id {REFERENCE_ID_TYPE} NOT NULL,
                method TEXT NOT NULL,
                amount {FLOAT_TYPE} NOT NULL,
                receipt_tracking_number TEXT,
                check_number TEXT,
                check_bank TEXT,
                check_due_date TEXT,
                is_cleared INTEGER NOT NULL DEFAULT 0,
                cleared_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id_id ON invoice_payments(invoice_id, id)"
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        payment_migration = "backfill_invoice_payments"
        if conn.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?",
            (payment_migration,),
        ).fetchone() is None:
            legacy_invoices = conn.execute(
                """
                SELECT i.* FROM invoices i
                WHERE NOT EXISTS (
                    SELECT 1 FROM invoice_payments p WHERE p.invoice_id = i.id
                )
                """
            ).fetchall()
            for invoice in legacy_invoices:
                method = invoice["payment_method"] or "cash"
                is_check = method == "check"
                amount = float(invoice["paid_amount"] or 0)
                if is_check and amount <= 0 and invoice["check_number"]:
                    amount = float(invoice["total_amount"] or 0)
                if amount <= 0:
                    continue
                conn.execute(
                    """
                    INSERT INTO invoice_payments (
                        invoice_id, method, amount, receipt_tracking_number,
                        check_number, check_bank, check_due_date, is_cleared, cleared_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        invoice["id"], method, amount, invoice["receipt_tracking_number"],
                        invoice["check_number"], invoice["check_bank"], invoice["check_due_date"],
                        None,
                    ),
                )
                if is_check:
                    paid_amount = max(0, float(invoice["paid_amount"] or 0) - amount)
                    status = "paid" if paid_amount >= float(invoice["total_amount"]) else ("partial" if paid_amount else "unpaid")
                    conn.execute(
                        "UPDATE invoices SET paid_amount = ?, status = ? WHERE id = ?",
                        (paid_amount, status, invoice["id"]),
                    )
            conn.execute(
                "INSERT INTO schema_migrations (name) VALUES (?)",
                (payment_migration,),
            )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id {ID_COLUMN},
                invoice_id {REFERENCE_ID_TYPE} NOT NULL,
                product_id {REFERENCE_ID_TYPE} NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price {FLOAT_TYPE} NOT NULL,
                total_amount {FLOAT_TYPE} NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS accounts (
                id {ID_COLUMN},
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                parent_id {REFERENCE_ID_TYPE} REFERENCES accounts(id),
                level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),
                account_type TEXT NOT NULL CHECK(account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
                is_active INTEGER NOT NULL DEFAULT 1,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_parent ON accounts(parent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type)")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id {ID_COLUMN},
                entry_number INTEGER NOT NULL UNIQUE,
                entry_date TEXT NOT NULL,
                due_date TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(entry_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_due ON journal_entries(due_date)")
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS journal_lines (
                id {ID_COLUMN},
                journal_entry_id {REFERENCE_ID_TYPE} NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
                account_id {REFERENCE_ID_TYPE} NOT NULL REFERENCES accounts(id),
                debit {FLOAT_TYPE} NOT NULL DEFAULT 0 CHECK(debit >= 0),
                credit {FLOAT_TYPE} NOT NULL DEFAULT 0 CHECK(credit >= 0),
                line_description TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lines_account ON journal_lines(account_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lines_entry ON journal_lines(journal_entry_id)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounting_counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
            """
        )
        max_entry_number = conn.execute(
            "SELECT COALESCE(MAX(entry_number), 0) AS value FROM journal_entries"
        ).fetchone()["value"]
        conn.execute(
            "INSERT INTO accounting_counters (name, value) VALUES (?, ?) ON CONFLICT (name) DO NOTHING",
            ("journal_entry", max_entry_number),
        )
        seed_accounting_accounts(conn)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id_id ON invoice_items(invoice_id, id)"
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS stock_moves (
                id {ID_COLUMN},
                product_id {REFERENCE_ID_TYPE} NOT NULL,
                direction TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_type TEXT,
                reference_id {REFERENCE_ID_TYPE},
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )
        conn.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?) ON CONFLICT (username) DO NOTHING",
            (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "مدیر سیستم", "admin"),
        )

        currency_migration = "currency_toman_to_rial"
        currency_migrated = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?",
            (currency_migration,),
        ).fetchone()
        if not USE_POSTGRES and not currency_migrated:
            currency_migrated = conn.execute("PRAGMA user_version").fetchone()[0] >= 1
        if not currency_migrated:
            conn.execute("UPDATE products SET purchase_price = purchase_price * 10, sale_price = sale_price * 10")
            conn.execute("UPDATE invoices SET total_amount = total_amount * 10, paid_amount = paid_amount * 10")
            conn.execute("UPDATE invoice_items SET unit_price = unit_price * 10, total_amount = total_amount * 10")
            conn.execute("UPDATE invoice_payments SET amount = amount * 10")
        if USE_POSTGRES or conn.execute("PRAGMA user_version").fetchone()[0] < 1:
            conn.execute(
                "INSERT INTO schema_migrations (name) VALUES (?) ON CONFLICT (name) DO NOTHING",
                (currency_migration,),
            )
        if not USE_POSTGRES and conn.execute("PRAGMA user_version").fetchone()[0] < 1:
            conn.execute("PRAGMA user_version = 1")


def find_or_create_customer(conn, customer_name):
    name = (customer_name or "").strip() or "مشتری عمومی"
    inserted = conn.execute(
        "INSERT INTO customers (name, notes) VALUES (?, ?) ON CONFLICT (name) DO NOTHING RETURNING id",
        (name, "ثبت شده از فاکتور"),
    ).fetchone()
    if inserted:
        return inserted["id"]
    return conn.execute("SELECT id FROM customers WHERE name = ?", (name,)).fetchone()["id"]


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "لطفاً دوباره وارد حساب شوید."}), 401
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def serve_react_frontend():
    if request.path.startswith("/api/"):
        return None
    if request.method != "GET":
        return jsonify({"error": "از رابط React یا API استفاده کنید."}), 404
    requested_file = request.path.lstrip("/")
    if requested_file and (FRONTEND_DIR / requested_file).is_file():
        return send_from_directory(FRONTEND_DIR, requested_file)
    if "." in Path(requested_file).name:
        return jsonify({"error": "فایل پیدا نشد."}), 404
    if (FRONTEND_DIR / "index.html").is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"error": "رابط React هنوز ساخته نشده است. ابتدا npm run build را اجرا کنید."}), 503


def api_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None
    return body


@app.get("/api/session")
def api_session():
    if not session.get("user_id"):
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "user": {
            "id": session["user_id"],
            "username": session.get("username"),
            "full_name": session.get("full_name"),
        },
    })


@app.post("/api/login")
def api_login():
    body = api_body()
    if body is None:
        return jsonify({"error": "درخواست نامعتبر است."}), 400
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, full_name, password FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None:
            return jsonify({"error": "نام کاربری یا رمز عبور اشتباه است."}), 401
        stored_password = user["password"]
        if stored_password.startswith(("scrypt:", "pbkdf2:sha256:")):
            password_matches = check_password_hash(stored_password, password)
        else:
            password_matches = hmac.compare_digest(stored_password, password)
            if password_matches:
                conn.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (generate_password_hash(password), user["id"]),
                )
    if not password_matches:
        return jsonify({"error": "نام کاربری یا رمز عبور اشتباه است."}), 401
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    return jsonify({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
        }
    })


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.get("/api/dashboard")
@login_required
def api_dashboard():
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    with get_db() as conn:
        summary = conn.execute(
            """
            SELECT COUNT(*) AS total_products, COALESCE(SUM(stock),0) AS total_stock,
                COALESCE(SUM(stock * sale_price),0) AS inventory_value,
                COUNT(CASE WHEN stock < ? THEN 1 END) AS low_stock_count
            FROM products
            """,
            (LOW_STOCK_THRESHOLD,),
        ).fetchone()
        latest_invoices = conn.execute(
            "SELECT id, invoice_number, customer_name, total_amount, invoice_date, status, payment_method FROM invoices ORDER BY id DESC LIMIT 5"
        ).fetchall()
        sales_today = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) AS total FROM invoices WHERE invoice_date = ?",
            (today,),
        ).fetchone()["total"]
        sales_month = conn.execute(
            "SELECT COALESCE(SUM(total_amount),0) AS total FROM invoices WHERE substr(invoice_date, 1, 7) = ?",
            (month,),
        ).fetchone()["total"]
        low_stock_items = conn.execute(
            "SELECT id, name, stock, sale_price FROM products WHERE stock < ? ORDER BY stock ASC LIMIT 5",
            (LOW_STOCK_THRESHOLD,),
        ).fetchall()
    return jsonify({
        "summary": dict(summary),
        "latest_invoices": [dict(row) for row in latest_invoices],
        "sales_today": sales_today,
        "sales_month": sales_month,
        "low_stock_items": [dict(row) for row in low_stock_items],
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


@app.route("/api/products", methods=["GET", "POST"])
@login_required
def api_products():
    if request.method == "POST":
        body = api_body()
        if body is None:
            return jsonify({"error": "اطلاعات محصول نامعتبر است."}), 400
        try:
            code = str(body.get("code", "")).strip()
            name = str(body.get("name", "")).strip()
            category = str(body.get("category", "")).strip()
            unit = str(body.get("unit", "عدد")).strip() or "عدد"
            purchase_price = float(body.get("purchase_price") or 0)
            sale_price = float(body.get("sale_price") or 0)
            stock = int(body.get("stock") or 0)
            description = str(body.get("description", "")).strip()
            if not all((code, name, category)) or min(purchase_price, sale_price, stock) < 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({"error": "نام، کد و دسته‌بندی کالا را وارد کنید؛ قیمت و موجودی نمی‌تواند منفی باشد."}), 400
        try:
            with get_db() as conn:
                cursor = conn.execute(
                    "INSERT INTO products (code, name, category, unit, purchase_price, sale_price, stock, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
                    (code, name, category, unit, purchase_price, sale_price, stock, description),
                )
                product_id = cursor.fetchone()["id"]
        except sqlite3.IntegrityError:
            return jsonify({"error": "کالایی با این کد از قبل ثبت شده است."}), 409
        return jsonify({"success": True, "id": product_id}), 201

    with get_db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY stock ASC, name ASC").fetchall()
    return jsonify({"products": [dict(row) for row in rows]})


@app.post("/api/stock-movements")
@login_required
def api_adjust_stock():
    body = api_body()
    if body is None:
        return jsonify({"error": "اطلاعات تغییر موجودی نامعتبر است."}), 400
    try:
        product_id = int(body.get("product_id"))
        quantity = int(body.get("quantity"))
        direction = body.get("direction")
        if quantity < 1 or direction not in {"in", "out"}:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "نوع تغییر و تعداد معتبر را وارد کنید."}), 400
    with get_db() as conn:
        product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            return jsonify({"error": "کالا پیدا نشد."}), 404
        next_stock = int(product["stock"]) + quantity if direction == "in" else int(product["stock"]) - quantity
        if next_stock < 0:
            return jsonify({"error": "موجودی کالا نمی‌تواند منفی شود."}), 400
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (next_stock, product_id))
        conn.execute(
            "INSERT INTO stock_moves (product_id, direction, quantity, reference_type, reference_id, note) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, direction, quantity, "manual", product_id, str(body.get("note") or "اصلاح موجودی")),
        )
    warning = f"موجودی «{product['name']}» کمتر از {LOW_STOCK_THRESHOLD} است." if next_stock < LOW_STOCK_THRESHOLD else None
    return jsonify({"success": True, "stock": next_stock, "warning": warning})


@app.get("/api/inventory")
@login_required
def api_inventory():
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products ORDER BY stock ASC, name ASC").fetchall()
        low_stock = conn.execute(
            "SELECT id, name, stock FROM products WHERE stock < ? ORDER BY stock ASC",
            (LOW_STOCK_THRESHOLD,),
        ).fetchall()
        movements = conn.execute(
            """
            SELECT sm.id, p.name AS product_name, sm.direction, sm.quantity,
                sm.note, sm.reference_type, sm.created_at
            FROM stock_moves sm JOIN products p ON p.id = sm.product_id
            ORDER BY sm.id DESC LIMIT 50
            """
        ).fetchall()
    return jsonify({
        "products": [dict(row) for row in products],
        "low_stock_items": [dict(row) for row in low_stock],
        "stock_moves": [dict(row) for row in movements],
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


@app.route("/api/customers", methods=["GET", "POST"])
@login_required
def api_customers():
    if request.method == "POST":
        body = api_body()
        name = str(body.get("name", "")).strip() if body else ""
        if not name:
            return jsonify({"error": "نام مشتری الزامی است."}), 400
        with get_db() as conn:
            conn.execute(
                "INSERT INTO customers (name, phone, address, notes) VALUES (?, ?, ?, ?) ON CONFLICT (name) DO NOTHING",
                (name, str(body.get("phone", "")).strip(), str(body.get("address", "")).strip(), str(body.get("notes", "")).strip()),
            )
        return jsonify({"success": True}), 201
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    return jsonify({"customers": [dict(row) for row in rows]})


@app.get("/api/invoices")
@login_required
def api_invoices():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        payments = conn.execute(
            "SELECT * FROM invoice_payments ORDER BY invoice_id DESC, id ASC"
        ).fetchall()
    payments_by_invoice = {}
    for payment in payments:
        payments_by_invoice.setdefault(payment["invoice_id"], []).append(dict(payment))
    invoices = []
    for row in rows:
        invoice = dict(row)
        invoice["payments"] = payments_by_invoice.get(row["id"], [])
        invoices.append(invoice)
    return jsonify({"invoices": invoices})


@app.route("/api/invoices", methods=["POST"])
@login_required
def api_create_invoice():
    body = api_body()
    if body is None:
        return jsonify({"error": "اطلاعات فاکتور نامعتبر است."}), 400
    raw_payments = body.get("payments")
    if not isinstance(raw_payments, list) or not raw_payments:
        return jsonify({"error": "حداقل یک روش پرداخت وارد کنید."}), 400
    try:
        payments = []
        payment_total = 0
        initially_paid = 0
        for payment in raw_payments:
            method = str(payment.get("method", "")).strip()
            amount = float(payment.get("amount", 0))
            if method not in {"cash", "card", "transfer", "check"} or not math.isfinite(amount) or amount <= 0:
                raise ValueError
            check_number = str(payment.get("check_number", "")).strip()
            check_bank = str(payment.get("check_bank", "")).strip()
            check_due_date = str(payment.get("check_due_date", "")).strip()
            if method == "check" and not all((check_number, check_bank, check_due_date)):
                return jsonify({"error": "برای هر چک، شماره، بانک و تاریخ سررسید الزامی است."}), 400
            if method == "check":
                try:
                    datetime.strptime(check_due_date, "%Y-%m-%d")
                except ValueError:
                    return jsonify({"error": "تاریخ سررسید هر چک را به‌درستی وارد کنید."}), 400
            payment_total += amount
            if not math.isfinite(payment_total):
                raise ValueError
            if method != "check":
                initially_paid += amount
            payments.append({
                "method": method,
                "amount": amount,
                "receipt_tracking_number": str(payment.get("receipt_tracking_number", "")).strip() or None,
                "check_number": check_number or None,
                "check_bank": check_bank or None,
                "check_due_date": check_due_date or None,
            })
    except (AttributeError, TypeError, ValueError):
        return jsonify({"error": "روش و مبلغ تمام ردیف‌های پرداخت را بررسی کنید."}), 400
    raw_items = body.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        return jsonify({"error": "حداقل یک کالا به فاکتور اضافه کنید."}), 400
    try:
        items = []
        quantities = {}
        for item in raw_items:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
            price = float(item["unit_price"])
            if quantity < 1 or not math.isfinite(price) or price < 0:
                raise ValueError
            items.append({"product_id": product_id, "quantity": quantity, "unit_price": price})
            quantities[product_id] = quantities.get(product_id, 0) + quantity
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "کالا، تعداد و قیمت ردیف‌های فاکتور را بررسی کنید."}), 400

    low_stock_items = []
    with get_db() as conn:
        begin_write_transaction(conn)
        product_by_id = {}
        for product_id, quantity in quantities.items():
            lock_clause = " FOR UPDATE" if USE_POSTGRES else ""
            product = conn.execute(
                f"SELECT id, name, stock FROM products WHERE id = ?{lock_clause}",
                (product_id,),
            ).fetchone()
            if product is None:
                return jsonify({"error": "یکی از کالاهای انتخاب‌شده پیدا نشد."}), 404
            if quantity > int(product["stock"]):
                return jsonify({"error": f"موجودی کالای «{product['name']}» کافی نیست."}), 400
            product_by_id[product_id] = product
        total = sum(item["quantity"] * item["unit_price"] for item in items)
        if not math.isfinite(total):
            return jsonify({"error": "مبلغ فاکتور معتبر نیست."}), 400
        if payment_total > total:
            return jsonify({"error": "جمع پرداخت‌ها نمی‌تواند از مبلغ فاکتور بیشتر باشد."}), 400
        now = datetime.now()
        invoice_number = f"INV-{now.strftime('%Y%m%d%H%M%S%f')}"
        customer_name = str(body.get("customer_name", "")).strip() or "مشتری عمومی"
        find_or_create_customer(conn, customer_name)
        methods = {payment["method"] for payment in payments}
        legacy_method = next(iter(methods)) if len(methods) == 1 else "mixed"
        check_payments = [payment for payment in payments if payment["method"] == "check"]
        receipt_numbers = [payment["receipt_tracking_number"] for payment in payments if payment["receipt_tracking_number"]]
        cursor = conn.execute(
            """
            INSERT INTO invoices (
                invoice_number, customer_name, invoice_date, total_amount, paid_amount,
                status, notes, payment_method, receipt_tracking_number,
                check_number, check_bank, check_due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id
            """,
            (
                invoice_number, customer_name, now.strftime("%Y-%m-%d"), total, initially_paid,
                "paid" if initially_paid >= total else ("partial" if initially_paid else "unpaid"),
                str(body.get("notes", "")).strip(), legacy_method,
                ", ".join(receipt_numbers) or None,
                check_payments[0]["check_number"] if len(check_payments) == 1 else None,
                check_payments[0]["check_bank"] if len(check_payments) == 1 else None,
                check_payments[0]["check_due_date"] if len(check_payments) == 1 else None,
            ),
        )
        invoice_id = cursor.fetchone()["id"]
        for payment in payments:
            conn.execute(
                """
                INSERT INTO invoice_payments (
                    invoice_id, method, amount, receipt_tracking_number,
                    check_number, check_bank, check_due_date, is_cleared
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id, payment["method"], payment["amount"],
                    payment["receipt_tracking_number"], payment["check_number"],
                    payment["check_bank"], payment["check_due_date"],
                    int(payment["method"] != "check"),
                ),
            )
        for item in items:
            conn.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price, total_amount) VALUES (?, ?, ?, ?, ?)",
                (invoice_id, item["product_id"], item["quantity"], item["unit_price"], item["quantity"] * item["unit_price"]),
            )
        for product_id, quantity in quantities.items():
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
            conn.execute(
                "INSERT INTO stock_moves (product_id, direction, quantity, reference_type, reference_id, note) VALUES (?, 'out', ?, 'invoice', ?, ?)",
                (product_id, quantity, invoice_id, f"فاکتور {invoice_number}"),
            )
            stock_after = int(product_by_id[product_id]["stock"]) - quantity
            if stock_after < LOW_STOCK_THRESHOLD:
                low_stock_items.append({"name": product_by_id[product_id]["name"], "stock": stock_after})
    return jsonify({"success": True, "invoice_id": invoice_id, "invoice_number": invoice_number, "total_amount": total, "low_stock_items": low_stock_items}), 201


@app.get("/api/invoices/<int:invoice_id>")
@login_required
def api_invoice_detail(invoice_id):
    with get_db() as conn:
        invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if invoice is None:
            return jsonify({"error": "فاکتور پیدا نشد."}), 404
        items = conn.execute(
            """
            SELECT ii.id, ii.quantity, ii.unit_price, ii.total_amount, p.name, p.unit
            FROM invoice_items ii JOIN products p ON p.id = ii.product_id
            WHERE ii.invoice_id = ? ORDER BY ii.id
            """,
            (invoice_id,),
        ).fetchall()
        payments = conn.execute(
            "SELECT * FROM invoice_payments WHERE invoice_id = ? ORDER BY id",
            (invoice_id,),
        ).fetchall()
    return jsonify({
        "invoice": dict(invoice),
        "items": [dict(row) for row in items],
        "payments": [dict(row) for row in payments],
    })


def accounting_date_filters():
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    try:
        if date_from:
            datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        return None, None, (jsonify({"error": "بازهٔ تاریخ معتبر نیست."}), 400)
    if date_from and date_to and date_from > date_to:
        return None, None, (jsonify({"error": "تاریخ شروع باید قبل از تاریخ پایان باشد."}), 400)
    return date_from, date_to, None


def accounting_report_model(conn):
    database = SimpleNamespace(conn=conn)
    return ReportModel(database, AccountModel(database))


@app.get("/api/accounting/accounts")
@login_required
def api_accounting_accounts():
    search = request.args.get("search", "").strip()
    postable_only = request.args.get("postable") == "1"
    query = """
        SELECT a.*, parent.name AS parent_name,
            CASE WHEN NOT EXISTS (
                SELECT 1 FROM accounts child
                WHERE child.parent_id = a.id AND child.is_active = 1
            ) THEN 1 ELSE 0 END AS is_postable
        FROM accounts a
        LEFT JOIN accounts parent ON parent.id = a.parent_id
        WHERE a.is_active = 1
    """
    params = []
    if postable_only:
        query += """
            AND a.level >= 3
            AND NOT EXISTS (
                SELECT 1 FROM accounts child
                WHERE child.parent_id = a.id AND child.is_active = 1
            )
        """
    if search:
        query += " AND (a.code LIKE ? OR a.name LIKE ?)"
        params.extend((f"%{search}%", f"%{search}%"))
    query += " ORDER BY a.code"
    with get_db() as conn:
        accounts = conn.execute(query, params).fetchall()
    return jsonify({"accounts": [dict(row) for row in accounts]})


@app.get("/api/accounting/entries")
@login_required
def api_accounting_entries():
    date_from, date_to, error = accounting_date_filters()
    if error:
        return error
    search = request.args.get("search", "").strip()
    query = """
        SELECT je.*, COALESCE(SUM(jl.debit), 0) AS total_debit,
            COALESCE(SUM(jl.credit), 0) AS total_credit
        FROM journal_entries je
        LEFT JOIN journal_lines jl ON jl.journal_entry_id = je.id
        WHERE 1=1
    """
    params = []
    if date_from:
        query += " AND je.entry_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND je.entry_date <= ?"
        params.append(date_to)
    if search:
        query += " AND (je.description LIKE ? OR CAST(je.entry_number AS TEXT) LIKE ?)"
        params.extend((f"%{search}%", f"%{search}%"))
    query += " GROUP BY je.id ORDER BY je.entry_date DESC, je.entry_number DESC"
    with get_db() as conn:
        entries = conn.execute(query, params).fetchall()
    return jsonify({"entries": [dict(row) for row in entries]})


@app.get("/api/accounting/entries/<int:entry_id>")
@login_required
def api_accounting_entry_detail(entry_id):
    with get_db() as conn:
        entry = conn.execute(
            "SELECT * FROM journal_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if entry is None:
            return jsonify({"error": "سند پیدا نشد."}), 404
        lines = conn.execute(
            """
            SELECT jl.*, a.code AS account_code, a.name AS account_name
            FROM journal_lines jl
            JOIN accounts a ON a.id = jl.account_id
            WHERE jl.journal_entry_id = ?
            ORDER BY jl.id
            """,
            (entry_id,),
        ).fetchall()
    return jsonify({
        "entry": dict(entry),
        "lines": [dict(line) for line in lines],
    })


@app.post("/api/accounting/entries")
@login_required
def api_create_accounting_entry():
    body = api_body()
    if body is None:
        return jsonify({"error": "اطلاعات سند نامعتبر است."}), 400
    entry_date = str(body.get("entry_date", "")).strip()
    due_date = str(body.get("due_date", "")).strip() or None
    description = str(body.get("description", "")).strip()
    try:
        datetime.strptime(entry_date, "%Y-%m-%d")
        if due_date:
            datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "تاریخ سند یا سررسید معتبر نیست."}), 400
    raw_lines = body.get("lines")
    if not isinstance(raw_lines, list) or len(raw_lines) < 2:
        return jsonify({"error": "هر سند باید حداقل دو سطر داشته باشد."}), 400
    lines = []
    total_debit = 0.0
    total_credit = 0.0
    try:
        for raw_line in raw_lines:
            account_id = int(raw_line["account_id"])
            debit = float(raw_line.get("debit") or 0)
            credit = float(raw_line.get("credit") or 0)
            if not math.isfinite(debit) or not math.isfinite(credit) or debit < 0 or credit < 0:
                raise ValueError
            if debit > 0 and credit > 0:
                return jsonify({"error": "هر سطر فقط می‌تواند بدهکار یا بستانکار داشته باشد."}), 400
            if debit == 0 and credit == 0:
                return jsonify({"error": "مبلغ سطر نمی‌تواند صفر باشد."}), 400
            total_debit += debit
            total_credit += credit
            lines.append({
                "account_id": account_id,
                "debit": debit,
                "credit": credit,
                "line_description": str(raw_line.get("line_description", "")).strip(),
            })
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "حساب و مبلغ تمام سطرهای سند را بررسی کنید."}), 400
    if not math.isfinite(total_debit) or not math.isfinite(total_credit):
        return jsonify({"error": "جمع مبالغ سند معتبر نیست."}), 400
    if abs(total_debit - total_credit) > 0.01:
        return jsonify({"error": f"جمع بدهکار ({total_debit:,.0f}) با بستانکار ({total_credit:,.0f}) برابر نیست."}), 400

    with get_db() as conn:
        begin_write_transaction(conn)
        for line in lines:
            account = conn.execute(
                "SELECT id, level, is_active FROM accounts WHERE id = ?",
                (line["account_id"],),
            ).fetchone()
            if account is None or not account["is_active"]:
                return jsonify({"error": "حساب انتخاب‌شده معتبر یا فعال نیست."}), 400
            if account["level"] < 3:
                return jsonify({"error": "ثبت سند فقط روی حساب معین یا تفصیلی مجاز است."}), 400
            active_child = conn.execute(
                "SELECT 1 FROM accounts WHERE parent_id = ? AND is_active = 1",
                (account["id"],),
            ).fetchone()
            previously_used = conn.execute(
                "SELECT 1 FROM journal_lines WHERE account_id = ?",
                (account["id"],),
            ).fetchone()
            if active_child and not previously_used:
                return jsonify({"error": "برای ثبت سند باید حساب برگ (معین یا تفصیلی) انتخاب شود."}), 400

        number_row = conn.execute(
            """
            UPDATE accounting_counters SET value = value + 1
            WHERE name = ? RETURNING value
            """,
            ("journal_entry",),
        ).fetchone()
        if number_row is None:
            raise RuntimeError("شمارنده شماره اسناد حسابداری ایجاد نشده است.")
        entry_number = number_row["value"]
        cursor = conn.execute(
            """
            INSERT INTO journal_entries (entry_number, entry_date, due_date, description, updated_at)
            VALUES (?, ?, ?, ?, ?) RETURNING id
            """,
            (
                entry_number,
                entry_date,
                due_date,
                description,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        entry_id = cursor.fetchone()["id"]
        for line in lines:
            conn.execute(
                """
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, line_description
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    line["account_id"],
                    line["debit"],
                    line["credit"],
                    line["line_description"],
                ),
            )
    return jsonify({
        "success": True,
        "entry_id": entry_id,
        "entry_number": entry_number,
        "total_debit": total_debit,
        "total_credit": total_credit,
    }), 201


@app.get("/api/accounting/general-ledger")
@login_required
def api_accounting_general_ledger():
    date_from, date_to, error = accounting_date_filters()
    if error:
        return error
    with get_db() as conn:
        report_model = accounting_report_model(conn)
        accounts = report_model.general_ledger(date_from, date_to)
    return jsonify({"accounts": accounts})


@app.get("/api/accounting/reports/trial-balance")
@login_required
def api_accounting_trial_balance():
    date_from, date_to, error = accounting_date_filters()
    if error:
        return error
    with get_db() as conn:
        report_model = accounting_report_model(conn)
        result = report_model.trial_balance(date_from, date_to, eight_column=True)
    return jsonify(result)


@app.get("/api/accounting/reports/income-statement")
@login_required
def api_accounting_income_statement():
    date_from, date_to, error = accounting_date_filters()
    if error:
        return error
    with get_db() as conn:
        report_model = accounting_report_model(conn)
        result = report_model.income_statement(date_from, date_to)
    return jsonify(result)


@app.post("/api/invoices/<int:invoice_id>/payments/<int:payment_id>/clear")
@login_required
def api_clear_invoice_check(invoice_id, payment_id):
    with get_db() as conn:
        begin_write_transaction(conn)
        payment = conn.execute(
            """
            SELECT id, method, amount, is_cleared FROM invoice_payments
            WHERE id = ? AND invoice_id = ?
            """,
            (payment_id, invoice_id),
        ).fetchone()
        if payment is None:
            return jsonify({"error": "پرداخت یا چک پیدا نشد."}), 404
        if payment["method"] != "check":
            return jsonify({"error": "فقط وضعیت چک را می‌توان تایید کرد."}), 400
        if payment["is_cleared"]:
            return jsonify({"error": "این چک قبلاً پاس‌شدنش تایید شده است."}), 409
        cleared_at = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE invoice_payments SET is_cleared = 1, cleared_at = ? WHERE id = ?",
            (cleared_at, payment_id),
        )
        invoice = conn.execute(
            "SELECT total_amount, paid_amount FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        paid_amount = min(
            float(invoice["total_amount"]),
            float(invoice["paid_amount"] or 0) + float(payment["amount"]),
        )
        status = "paid" if paid_amount >= float(invoice["total_amount"]) else "partial"
        conn.execute(
            "UPDATE invoices SET paid_amount = ?, status = ? WHERE id = ?",
            (paid_amount, status, invoice_id),
        )
    return jsonify({
        "success": True,
        "paid_amount": paid_amount,
        "status": status,
        "cleared_at": cleared_at,
    })


ensure_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
