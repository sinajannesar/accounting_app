import {
  Activity,
  ArrowDownLeft,
  ArrowUpRight,
  BookOpen,
  Boxes,
  Check,
  ClipboardList,
  CircleAlert,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Plus,
  Printer,
  Receipt,
  Search,
  ShoppingBag,
  ChartNoAxesCombined,
  Users,
  X,
} from "lucide-react";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  api,
  money,
  number,
  paymentLabel,
  type Customer,
  type DashboardData,
  type InventoryData,
  type Invoice,
  type InvoiceItem,
  type InvoicePayment,
  type Product,
  type User,
} from "./api";
import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useNavigate,
  useOutletContext,
  useParams,
} from "react-router-dom";
import {
  FinancialReportsPage,
  GeneralLedgerPage,
  JournalEntriesPage,
} from "./AccountingPages";

type AppContextValue = {
  user: User;
  notify: (message: string, type?: "success" | "error") => void;
  signOut: () => Promise<void>;
};

const AppContext = createContext<AppContextValue | null>(null);

function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("App context is unavailable.");
  return context;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    api<{ authenticated: boolean; user?: User }>("/api/session")
      .then((result) => setUser(result.authenticated ? result.user || null : null))
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  const notify = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    window.setTimeout(() => setToast(null), 4200);
  };
  const signOut = async () => {
    await api("/api/logout", { method: "POST" });
    setUser(null);
  };

  if (checking) {
    return <div className="grid min-h-screen place-items-center text-slate-500">در حال بررسی ورود…</div>;
  }

  return (
    <AppContext.Provider value={{ user: user!, notify, signOut }}>
      {toast && (
        <div
          role="status"
          className={`fixed left-4 top-4 z-[60] flex max-w-sm items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold text-white shadow-xl ${
            toast.type === "error" ? "bg-rose-600" : "bg-emerald-600"
          }`}
        >
          {toast.type === "error" ? <CircleAlert size={18} /> : <Check size={18} />}
          {toast.message}
          <button onClick={() => setToast(null)} aria-label="بستن پیام"><X size={16} /></button>
        </div>
      )}
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage onLogin={setUser} />} />
        <Route element={user ? <AppLayout /> : <Navigate to="/login" replace />}>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="invoices" element={<InvoicesPage />} />
          <Route path="invoices/new" element={<NewInvoicePage />} />
          <Route path="invoices/:invoiceId" element={<InvoiceDetailPage />} />
          <Route path="accounting/entries" element={<JournalEntriesPage />} />
          <Route path="accounting/general-ledger" element={<GeneralLedgerPage />} />
          <Route path="accounting/reports" element={<FinancialReportsPage />} />
        </Route>
        <Route path="*" element={<Navigate to={user ? "/" : "/login"} replace />} />
      </Routes>
    </AppContext.Provider>
  );
}

function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await api<{ user: User }>("/api/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      onLogin(result.user);
      navigate("/", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ورود انجام نشد.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-sky-950 to-sky-800 p-4">
      <form onSubmit={submit} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl">
        <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-sky-600 text-white"><ShoppingBag /></div>
        <h1 className="mt-5 text-center text-2xl font-extrabold">ورود به پنل حسابداری و فروش</h1>
        <p className="mt-2 text-center text-sm text-slate-500">برای ادامه اطلاعات حساب خود را وارد کنید.</p>
        {error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <label className="mt-6 block text-sm font-semibold">
          نام کاربری
          <input required autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-sky-500" />
        </label>
        <label className="mt-4 block text-sm font-semibold">
          رمز عبور
          <input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-sky-500" />
        </label>
        <button disabled={busy} className="mt-6 w-full rounded-xl bg-sky-600 px-4 py-3 font-bold text-white hover:bg-sky-500">{busy ? "در حال ورود…" : "ورود"}</button>
      </form>
    </main>
  );
}

const navItems = [
  { to: "/", label: "داشبورد", icon: LayoutDashboard, end: true },
  { to: "/invoices/new", label: "ثبت فاکتور", icon: Plus },
  { to: "/products", label: "محصولات", icon: Boxes },
  { to: "/inventory", label: "انبار", icon: Activity },
  { to: "/customers", label: "مشتریان", icon: Users },
  { to: "/invoices", label: "فاکتورها", icon: FileText },
  { to: "/accounting/entries", label: "اسناد حسابداری", icon: ClipboardList },
  { to: "/accounting/general-ledger", label: "دفتر کل", icon: BookOpen },
  { to: "/accounting/reports", label: "گزارش‌های مالی", icon: ChartNoAxesCombined },
];

function AppLayout() {
  const { user, signOut } = useApp();
  const [menuOpen, setMenuOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  async function logout() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="min-h-screen lg:flex">
      <aside className="no-print sticky top-0 z-30 bg-slate-950 text-white lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-4 lg:px-5">
          <Link to="/" className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-emerald-500"><ShoppingBag size={21} /></span>
            <span><strong className="block text-base">حسابداری و فروش</strong><small className="text-xs text-slate-400">مدیریت یکپارچه</small></span>
          </Link>
          <button className="rounded-lg p-2 text-slate-300 lg:hidden" onClick={() => setMenuOpen(!menuOpen)} aria-label="باز کردن منو">{menuOpen ? <X /> : <Menu />}</button>
        </div>
        <nav className={`${menuOpen ? "flex" : "hidden"} gap-1 overflow-x-auto p-3 lg:flex lg:flex-col`}>
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} onClick={() => setMenuOpen(false)} className={({ isActive }) =>
              `flex shrink-0 items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${isActive ? "bg-sky-600 text-white" : "text-slate-300 hover:bg-white/10 hover:text-white"}`
            }>
              <Icon size={19} />{label}
            </NavLink>
          ))}
          <button onClick={logout} className="flex shrink-0 items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-slate-300 hover:bg-white/10 hover:text-white lg:hidden"><LogOut size={19} /> خروج</button>
        </nav>
        <div className="mt-auto hidden border-t border-white/10 p-4 lg:block">
          <p className="truncate text-sm font-semibold">{user.full_name}</p>
          <p className="mt-1 text-xs text-slate-400">{user.username}</p>
          <button disabled={signingOut} onClick={logout} className="mt-4 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-white/10"><LogOut size={17} /> خروج</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-4 sm:p-6 lg:h-screen lg:overflow-y-auto lg:p-8">
        <Outlet context={{ user } satisfies { user: User }} />
      </main>
    </div>
  );
}

type LayoutContext = { user: User };

function PageHeader({ title, description, children }: { title: string; description?: string; children?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-950">{title}</h1>
        {description && <p className="mt-2 text-sm text-slate-500">{description}</p>}
      </div>
      {children}
    </header>
  );
}

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>{children}</section>;
}

function Loading() {
  return <div className="py-12 text-center text-sm text-slate-500">در حال دریافت اطلاعات…</div>;
}

function ErrorMessage({ message }: { message: string }) {
  return <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{message}</div>;
}

function Table({ children }: { children: ReactNode }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-right text-sm">{children}</table></div>;
}

function TableHead({ children }: { children: ReactNode }) {
  return <thead className="bg-slate-50 text-xs font-bold text-slate-500"><tr>{children}</tr></thead>;
}

function TH({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3">{children}</th>;
}

function TD({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`border-t border-slate-100 px-4 py-3 ${className}`}>{children}</td>;
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="py-10 text-center text-sm text-slate-400">{children}</p>;
}

function Metric({ label, value, icon: Icon, tone }: { label: string; value: ReactNode; icon: typeof Boxes; tone: string }) {
  return (
    <Card className="flex items-center gap-4">
      <span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${tone}`}><Icon size={22} /></span>
      <span className="min-w-0"><span className="block text-sm text-slate-500">{label}</span><strong className="mt-1 block truncate text-xl font-extrabold text-slate-900">{value}</strong></span>
    </Card>
  );
}

function DashboardPage() {
  const { user } = useOutletContext<LayoutContext>();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [invoiceSearch, setInvoiceSearch] = useState("");
  const [stockSearch, setStockSearch] = useState("");
  useEffect(() => {
    api<DashboardData>("/api/dashboard").then(setData).catch((reason) => setError(reason.message));
  }, []);
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <Loading />;
  const filteredInvoices = data.latest_invoices.filter(invoice =>
    matchesSearch(`${invoice.invoice_number} ${invoice.customer_name} ${invoice.invoice_date}`, invoiceSearch),
  );
  const filteredLowStock = data.low_stock_items.filter(item =>
    matchesSearch(`${item.name} ${item.code} ${item.category}`, stockSearch),
  );
  return (
    <>
      <PageHeader title={`سلام ${user.full_name}`} description="خلاصه فروش و موجودی فروشگاه">
        <div className="flex flex-wrap gap-2">
          <Link to="/invoices/new" className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white hover:bg-sky-500"><Plus size={18} /> ثبت فاکتور</Link>
          <Link to="/products" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50"><Plus size={18} /> افزودن کالا</Link>
        </div>
      </PageHeader>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="فروش امروز" value={money(data.sales_today)} icon={Receipt} tone="bg-sky-50 text-sky-600" />
        <Metric label="فروش این ماه" value={money(data.sales_month)} icon={ArrowUpRight} tone="bg-emerald-50 text-emerald-600" />
        <Metric label="تعداد کالاها" value={number(data.summary.total_products)} icon={Boxes} tone="bg-violet-50 text-violet-600" />
        <Metric label="کمبود موجودی" value={number(data.summary.low_stock_count)} icon={CircleAlert} tone="bg-rose-50 text-rose-600" />
      </div>
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><h2 className="font-bold">آخرین فاکتورها</h2><Link to="/invoices" className="text-sm font-semibold text-sky-700">همه فاکتورها</Link></div>
          {data.latest_invoices.length > 0 && <ListSearch value={invoiceSearch} onChange={setInvoiceSearch} placeholder="جست‌وجوی شماره یا مشتری…" />}
          {filteredInvoices.length ? <Table><TableHead><TH>شماره</TH><TH>مشتری</TH><TH>مبلغ (ریال)</TH><TH>تاریخ</TH></TableHead><tbody>{filteredInvoices.map(invoice => <tr key={invoice.id}><TD><Link className="font-semibold text-sky-700" to={`/invoices/${invoice.id}`}>{invoice.invoice_number}</Link></TD><TD>{invoice.customer_name}</TD><TD>{money(invoice.total_amount)}</TD><TD>{invoice.invoice_date}</TD></tr>)}</tbody></Table> : <Empty>{data.latest_invoices.length ? "فاکتوری پیدا نشد." : "هنوز فاکتوری ثبت نشده است."}</Empty>}
        </Card>
        <Card>
          <div className="mb-4 flex items-center justify-between"><h2 className="font-bold">نیاز به شارژ انبار</h2><Link to="/inventory" className="text-sm font-semibold text-sky-700">گزارش انبار</Link></div>
          {data.low_stock_items.length > 0 && <ListSearch value={stockSearch} onChange={setStockSearch} placeholder="جست‌وجوی کالای کم‌موجود…" />}
          {filteredLowStock.length ? <ul className="space-y-2">{filteredLowStock.map(item => <li key={item.id} className="flex items-center justify-between rounded-xl bg-rose-50 px-4 py-3"><span className="font-medium">{item.name}</span><span className="text-sm font-bold text-rose-700">{number(item.stock)} موجود</span></li>)}</ul> : <Empty>{data.low_stock_items.length ? "کالایی پیدا نشد." : "همه کالاها موجودی کافی دارند."}</Empty>}
        </Card>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <Metric label="تعداد کل موجودی" value={number(data.summary.total_stock)} icon={Boxes} tone="bg-indigo-50 text-indigo-600" />
        <Metric label="ارزش تقریبی انبار" value={money(data.summary.inventory_value)} icon={ShoppingBag} tone="bg-amber-50 text-amber-600" />
      </div>
    </>
  );
}

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const { notify } = useApp();
  const load = () => api<{ products: Product[] }>("/api/products").then(result => setProducts(result.products)).catch(reason => setError(reason.message)).finally(() => setLoading(false));
  useEffect(() => { void load(); }, []);
  const filtered = products.filter(product => matchesSearch(`${product.name} ${product.code} ${product.category} ${product.description || ""}`, search));

  async function addProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const body = Object.fromEntries(form.entries());
    try {
      await api("/api/products", { method: "POST", body: JSON.stringify(body) });
      formElement.reset();
      setShowAdd(false);
      notify("کالا با موفقیت اضافه شد.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ثبت کالا ناموفق بود.");
    }
  }

  if (loading) return <Loading />;
  return (
    <>
      <PageHeader title="محصولات" description="کالاهای فروشگاه و قیمت‌های آن‌ها">
        <button onClick={() => setShowAdd(!showAdd)} className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white"><Plus size={18} /> کالای جدید</button>
      </PageHeader>
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      {showAdd && <Card className="mb-5">
        <h2 className="mb-4 font-bold">مشخصات کالای جدید</h2>
        <form onSubmit={addProduct} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="کد کالا" name="code" required />
          <Field label="نام کالا" name="name" required />
          <Field label="دسته‌بندی" name="category" required />
          <Field label="واحد" name="unit" defaultValue="عدد" />
          <Field label="قیمت خرید (ریال)" name="purchase_price" type="number" min="0" required />
          <Field label="قیمت فروش (ریال)" name="sale_price" type="number" min="0" required />
          <Field label="موجودی اولیه" name="stock" type="number" min="0" required />
          <div className="flex items-end"><button className="w-full rounded-xl bg-emerald-600 px-4 py-3 font-bold text-white">ذخیره کالا</button></div>
          <label className="text-sm font-semibold sm:col-span-2 lg:col-span-4">توضیحات<input name="description" className={inputClass} /></label>
        </form>
      </Card>}
      <Card>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-bold">فهرست کالاها <span className="text-sm font-normal text-slate-400">({number(products.length)})</span></h2>
          <ListSearch value={search} onChange={setSearch} placeholder="نام، کد یا دسته کالا…" />
        </div>
        {filtered.length ? <Table><TableHead><TH>کالا</TH><TH>کد</TH><TH>دسته</TH><TH>قیمت فروش (ریال)</TH><TH>موجودی</TH></TableHead><tbody>{filtered.map(product => <tr key={product.id}><TD className="font-semibold">{product.name}</TD><TD>{product.code}</TD><TD>{product.category}</TD><TD>{money(product.sale_price)}</TD><TD><StockBadge stock={product.stock} /></TD></tr>)}</tbody></Table> : <Empty>کالایی پیدا نشد.</Empty>}
      </Card>
    </>
  );
}

const inputClass = "mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100";

function matchesSearch(text: string, query: string) {
  const normalize = (value: string) => value.toLocaleLowerCase()
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[۰-۹٠-٩]/g, digit => {
      const code = digit.charCodeAt(0);
      return String(code >= 0x6f0 ? code - 0x6f0 : code - 0x660);
    })
    .trim();
  return normalize(text).includes(normalize(query));
}

function ListSearch({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label className="relative mb-4 block sm:max-w-sm">
      <Search size={17} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} className={`${inputClass} pr-10`} />
    </label>
  );
}

function Field({ label, name, type = "text", required = false, defaultValue, min }: { label: string; name: string; type?: string; required?: boolean; defaultValue?: string; min?: string }) {
  return <label className="block text-sm font-semibold">{label}<input name={name} type={type} required={required} min={min} defaultValue={defaultValue} className={inputClass} /></label>;
}

function StockBadge({ stock }: { stock: number }) {
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${stock < 5 ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>{number(stock)} عدد</span>;
}

function InventoryPage() {
  const [data, setData] = useState<InventoryData | null>(null);
  const [error, setError] = useState("");
  const [adjusting, setAdjusting] = useState(false);
  const [productSearch, setProductSearch] = useState("");
  const [lowStockSearch, setLowStockSearch] = useState("");
  const [movementSearch, setMovementSearch] = useState("");
  const [stockProductSearch, setStockProductSearch] = useState("");
  const [stockProductId, setStockProductId] = useState("");
  const { notify } = useApp();
  const load = () => api<InventoryData>("/api/inventory").then(setData).catch(reason => setError(reason.message));
  useEffect(() => { void load(); }, []);
  async function adjustStock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form).entries());
    setAdjusting(true);
    setError("");
    try {
      const result = await api<{ warning: string | null }>("/api/stock-movements", {
        method: "POST",
        body: JSON.stringify(body),
      });
      form.reset();
      setStockProductId("");
      setStockProductSearch("");
      notify(result.warning || "موجودی انبار به‌روزرسانی شد.", result.warning ? "error" : "success");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تغییر موجودی انجام نشد.");
    } finally {
      setAdjusting(false);
    }
  }
  if (!data && error) return <ErrorMessage message={error} />;
  if (!data) return <Loading />;
  const filteredProducts = data.products.filter(product =>
    matchesSearch(`${product.name} ${product.code} ${product.category}`, productSearch),
  );
  const filteredLowStock = data.low_stock_items.filter(product =>
    matchesSearch(`${product.name} ${product.code}`, lowStockSearch),
  );
  const filteredMovements = data.stock_moves.filter(move =>
    matchesSearch(`${move.product_name} ${move.direction === "in" ? "ورود" : "خروج"} ${move.quantity} ${move.note || ""} ${move.created_at}`, movementSearch),
  );
  const availableProducts = data.products.filter(product =>
    String(product.id) === stockProductId || matchesSearch(`${product.name} ${product.code} ${product.category}`, stockProductSearch),
  );
  return (
    <>
      <PageHeader title="انبار" description={`هشدار خودکار برای موجودی کمتر از ${data.low_stock_threshold} عدد`}>
        <button onClick={() => setAdjusting(!adjusting)} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold"><Activity size={17} /> اصلاح موجودی</button>
      </PageHeader>
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      {adjusting && <Card className="mb-5">
        <h2 className="mb-4 font-bold">ورود یا خروج دستی کالا</h2>
        <form onSubmit={adjustStock} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-sm font-semibold">جست‌وجوی کالا<input value={stockProductSearch} onChange={event => setStockProductSearch(event.target.value)} placeholder="نام یا کد کالا…" className={inputClass} /><select required name="product_id" value={stockProductId} onChange={event => setStockProductId(event.target.value)} className={inputClass}><option value="">انتخاب کالا</option>{availableProducts.map(product => <option key={product.id} value={product.id}>{product.name} — موجودی {number(product.stock)}</option>)}</select></label>
          <label className="text-sm font-semibold">عملیات<select name="direction" className={inputClass}><option value="in">افزودن به انبار</option><option value="out">کسر از انبار</option></select></label>
          <Field label="تعداد" name="quantity" type="number" min="1" required />
          <div className="flex items-end"><button disabled={!data.products.length} className="w-full rounded-xl bg-sky-600 px-4 py-3 font-bold text-white">ذخیره تغییر</button></div>
          <label className="text-sm font-semibold sm:col-span-2 lg:col-span-4">توضیح (اختیاری)<input name="note" className={inputClass} /></label>
        </form>
      </Card>}
      {data.low_stock_items.length > 0 && <Card className="mb-5 border-rose-200 bg-rose-50/60">
        <h2 className="mb-3 flex items-center gap-2 font-bold text-rose-800"><CircleAlert size={19} /> کالاهای نیازمند شارژ</h2>
        <ListSearch value={lowStockSearch} onChange={setLowStockSearch} placeholder="جست‌وجوی کالای کم‌موجود…" />
        {filteredLowStock.length ? <div className="flex flex-wrap gap-2">{filteredLowStock.map(item => <span key={item.id} className="rounded-xl bg-white px-3 py-2 text-sm font-semibold text-rose-700">{item.name} — {number(item.stock)} موجود</span>)}</div> : <Empty>کالایی پیدا نشد.</Empty>}
      </Card>}
      <Card>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><h2 className="font-bold">موجودی کالاها</h2><ListSearch value={productSearch} onChange={setProductSearch} placeholder="نام، کد یا دسته کالا…" /></div>
        {filteredProducts.length ? <Table><TableHead><TH>نام کالا</TH><TH>کد</TH><TH>موجودی</TH><TH>قیمت فروش (ریال)</TH></TableHead><tbody>{filteredProducts.map(product => <tr key={product.id}><TD className="font-semibold">{product.name}</TD><TD>{product.code}</TD><TD><StockBadge stock={product.stock} /></TD><TD>{money(product.sale_price)}</TD></tr>)}</tbody></Table> : <Empty>{data.products.length ? "کالایی پیدا نشد." : "هنوز کالایی ثبت نشده است."}</Empty>}
      </Card>
      <Card className="mt-5">
        <h2 className="mb-4 font-bold">آخرین تغییرات انبار</h2>
        {data.stock_moves.length > 0 && <ListSearch value={movementSearch} onChange={setMovementSearch} placeholder="نام کالا، ورود/خروج، یادداشت…" />}
        {filteredMovements.length ? <Table><TableHead><TH>کالا</TH><TH>نوع تغییر</TH><TH>تعداد</TH><TH>یادداشت</TH><TH>زمان</TH></TableHead><tbody>{filteredMovements.map(move => <tr key={move.id}><TD>{move.product_name}</TD><TD><span className={`inline-flex items-center gap-1 ${move.direction === "in" ? "text-emerald-700" : "text-rose-700"}`}>{move.direction === "in" ? <ArrowDownLeft size={15} /> : <ArrowUpRight size={15} />}{move.direction === "in" ? "ورود" : "خروج"}</span></TD><TD>{number(move.quantity)}</TD><TD>{move.note || "—"}</TD><TD>{move.created_at}</TD></tr>)}</tbody></Table> : <Empty>{data.stock_moves.length ? "تغییری پیدا نشد." : "تغییری ثبت نشده است."}</Empty>}
      </Card>
    </>
  );
}

function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { notify } = useApp();
  const load = () => api<{ customers: Customer[] }>("/api/customers").then(result => setCustomers(result.customers)).catch(reason => setError(reason.message)).finally(() => setLoading(false));
  useEffect(() => { void load(); }, []);
  const filteredCustomers = customers.filter(customer =>
    matchesSearch(`${customer.name} ${customer.phone || ""} ${customer.address || ""} ${customer.notes || ""}`, search),
  );
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/api/customers", { method: "POST", body: JSON.stringify(body) });
      form.reset();
      notify("مشتری ذخیره شد.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ثبت مشتری ناموفق بود.");
    }
  }
  if (loading) return <Loading />;
  return (
    <>
      <PageHeader title="مشتریان" description="ثبت و دسترسی سریع به اطلاعات مشتریان" />
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
        <Card><h2 className="mb-4 font-bold">افزودن مشتری</h2><form onSubmit={submit} className="space-y-3"><Field label="نام مشتری" name="name" required /><Field label="شماره تلفن" name="phone" type="tel" /><Field label="آدرس" name="address" /><button className="w-full rounded-xl bg-sky-600 px-4 py-3 font-bold text-white">ذخیره مشتری</button></form></Card>
        <Card><div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><h2 className="font-bold">فهرست مشتریان</h2>{customers.length > 0 && <ListSearch value={search} onChange={setSearch} placeholder="نام، تلفن یا آدرس…" />}</div>{filteredCustomers.length ? <Table><TableHead><TH>نام</TH><TH>تلفن</TH><TH>آدرس</TH></TableHead><tbody>{filteredCustomers.map(customer => <tr key={customer.id}><TD className="font-semibold">{customer.name}</TD><TD>{customer.phone || "—"}</TD><TD>{customer.address || "—"}</TD></tr>)}</tbody></Table> : <Empty>{customers.length ? "مشتری پیدا نشد." : "مشتری ثبت نشده است."}</Empty>}</Card>
      </div>
    </>
  );
}

function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api<{ invoices: Invoice[] }>("/api/invoices").then(result => setInvoices(result.invoices)).catch(reason => setError(reason.message)); }, []);
  const filtered = invoices.filter(invoice => matchesSearch(`${invoice.invoice_number} ${invoice.customer_name} ${invoice.invoice_date} ${invoice.receipt_tracking_number || ""} ${(invoice.payments || []).map(payment => `${payment.check_number || ""} ${payment.check_bank || ""} ${payment.check_due_date || ""} ${payment.receipt_tracking_number || ""}`).join(" ")}`, search));
  if (error) return <ErrorMessage message={error} />;
  return <><PageHeader title="فاکتورها" description="جست‌وجو و مشاهده فاکتورهای فروش"><Link to="/invoices/new" className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white"><Plus size={18} /> فاکتور جدید</Link></PageHeader><Card><ListSearch value={search} onChange={setSearch} placeholder="شماره، مشتری، چک یا پیگیری…" />{filtered.length ? <Table><TableHead><TH>شماره فاکتور</TH><TH>مشتری</TH><TH>مبلغ کل (ریال)</TH><TH>پرداخت‌شده</TH><TH>روش‌ها و سررسید چک</TH><TH>تاریخ</TH><TH>جزئیات</TH></TableHead><tbody>{filtered.map(invoice => <tr key={invoice.id}><TD className="font-semibold">{invoice.invoice_number}</TD><TD>{invoice.customer_name}</TD><TD>{money(invoice.total_amount)}</TD><TD>{money(invoice.paid_amount)}</TD><TD><div className="space-y-1">{invoice.payments?.length ? invoice.payments.map(payment => <p key={payment.id}>{paymentLabel(payment.method)}: {money(payment.amount)}{payment.method === "check" && <span className="block text-xs text-slate-500">{payment.check_number} · سررسید {payment.check_due_date} · {payment.is_cleared ? "پاس شده" : "در انتظار پاس شدن"}</span>}</p>) : paymentLabel(invoice.payment_method)}</div></TD><TD>{invoice.invoice_date}</TD><TD><Link className="font-bold text-sky-700" to={`/invoices/${invoice.id}`}>نمایش</Link></TD></tr>)}</tbody></Table> : <Empty>فاکتوری پیدا نشد.</Empty>}</Card></>;
}

type InvoiceDraftItem = { product_id: string; product_search: string; quantity: number; unit_price: number | "" };
type PaymentDraft = {
  method: "cash" | "card" | "transfer" | "check";
  amount: string;
  receipt_tracking_number: string;
  check_number: string;
  check_bank: string;
  check_due_date: string;
};
const emptyDraftItem = (): InvoiceDraftItem => ({ product_id: "", product_search: "", quantity: 1, unit_price: "" });
const emptyPayment = (): PaymentDraft => ({
  method: "cash",
  amount: "",
  receipt_tracking_number: "",
  check_number: "",
  check_bank: "",
  check_due_date: "",
});

function NewInvoicePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [items, setItems] = useState<InvoiceDraftItem[]>([emptyDraftItem()]);
  const [payments, setPayments] = useState<PaymentDraft[]>([emptyPayment()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { notify } = useApp();
  const navigate = useNavigate();
  useEffect(() => { api<{ products: Product[] }>("/api/products").then(result => setProducts(result.products)).catch(reason => setError(reason.message)); }, []);
  const total = useMemo(() => items.reduce((sum, item) => sum + item.quantity * Number(item.unit_price || 0), 0), [items]);
  const paymentAmount = (payment: PaymentDraft, index: number) =>
    Number(payment.amount || (payments.length === 1 && index === 0 ? total : 0));
  const paymentsTotal = payments.reduce((sum, payment, index) => sum + paymentAmount(payment, index), 0);
  const stockIssues = useMemo(() => {
    const totals = new Map<string, number>();
    items.forEach(item => item.product_id && totals.set(item.product_id, (totals.get(item.product_id) || 0) + item.quantity));
    return Array.from(totals.entries()).flatMap(([id, quantity]) => {
      const product = products.find(candidate => String(candidate.id) === id);
      return product && quantity > product.stock ? [product.name] : [];
    });
  }, [items, products]);

  function updateItem(index: number, patch: Partial<InvoiceDraftItem>) {
    setItems(current => current.map((item, currentIndex) => {
      if (currentIndex !== index) return item;
      const next = { ...item, ...patch };
      if (patch.product_id) {
        const product = products.find(candidate => String(candidate.id) === patch.product_id);
        if (product) next.unit_price = product.sale_price;
      }
      return next;
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (stockIssues.length) return setError(`موجودی کافی نیست: ${stockIssues.join("، ")}`);
    if (payments.some((payment, index) => paymentAmount(payment, index) <= 0)) {
      return setError("مبلغ هر روش پرداخت باید بیشتر از صفر باشد.");
    }
    if (paymentsTotal > total) return setError("جمع پرداخت‌ها نمی‌تواند از مبلغ فاکتور بیشتر باشد.");
    if (payments.some(payment => payment.method === "check" && (!payment.check_number.trim() || !payment.check_bank.trim() || !payment.check_due_date))) {
      return setError("برای هر چک، شماره، بانک و تاریخ سررسید را وارد کنید.");
    }
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const body = Object.fromEntries(form.entries());
    try {
      const result = await api<{ invoice_id: number; low_stock_items: { name: string }[] }>("/api/invoices", {
        method: "POST",
        body: JSON.stringify({
          ...body,
          payments: payments.map((payment, index) => ({
            ...payment,
            amount: paymentAmount(payment, index),
          })),
          items: items.map(item => ({
            product_id: Number(item.product_id),
            quantity: item.quantity,
            unit_price: Number(item.unit_price || 0),
          })),
        }),
      });
      notify(result.low_stock_items.length ? `فاکتور ثبت شد؛ موجودی ${result.low_stock_items.map(item => item.name).join("، ")} کم است.` : "فاکتور با موفقیت ثبت شد.");
      navigate(`/invoices/${result.invoice_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ثبت فاکتور ناموفق بود.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="ثبت فاکتور" description="کالاها را انتخاب کنید؛ قیمت و جمع فاکتور خودکار محاسبه می‌شود." />
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      <form onSubmit={submit} className="space-y-5">
        <Card><label className="block text-sm font-semibold sm:max-w-md">نام مشتری<input name="customer_name" defaultValue="مشتری عمومی" className={inputClass} /></label></Card>
        <Card>
          <div className="mb-4 flex items-center justify-between"><h2 className="font-bold">کالاهای فاکتور</h2><button type="button" onClick={() => setItems(current => [...current, emptyDraftItem()])} className="inline-flex items-center gap-1 rounded-xl bg-slate-100 px-3 py-2 text-sm font-bold"><Plus size={16} /> افزودن کالا</button></div>
          <div className="space-y-3">{items.map((item, index) => <div key={index} className="grid gap-3 rounded-2xl bg-slate-50 p-4 md:grid-cols-[minmax(0,2fr)_120px_minmax(150px,1fr)_auto] md:items-end">
            <label className="text-sm font-semibold">جست‌وجوی کالا<input value={item.product_search} onChange={event => updateItem(index, { product_search: event.target.value })} placeholder="نام، کد یا دسته کالا…" className={inputClass} /><select required value={item.product_id} onChange={event => updateItem(index, { product_id: event.target.value, product_search: "" })} className={inputClass}><option value="">انتخاب کالا</option>{products.filter(product => product.id.toString() === item.product_id || matchesSearch(`${product.name} ${product.code} ${product.category}`, item.product_search)).map(product => <option key={product.id} value={product.id} disabled={product.stock <= 0}>{product.name} — موجودی {number(product.stock)}</option>)}</select></label>
            <label className="text-sm font-semibold">تعداد<input required min="1" type="number" value={item.quantity} onChange={event => updateItem(index, { quantity: Number(event.target.value) })} className={inputClass} /></label>
            <label className="text-sm font-semibold">قیمت هر واحد (ریال)<input required min="0" type="number" value={item.unit_price} onChange={event => updateItem(index, { unit_price: event.target.value === "" ? "" : Number(event.target.value) })} className={inputClass} /></label>
            <button type="button" disabled={items.length === 1} onClick={() => setItems(current => current.filter((_, currentIndex) => currentIndex !== index))} aria-label="حذف کالا" className="rounded-xl p-3 text-rose-600 hover:bg-rose-100"><X size={19} /></button>
            <p className="text-sm text-slate-500 md:col-span-4">جمع ردیف: <strong className="text-slate-800">{money(item.quantity * Number(item.unit_price || 0))}</strong></p>
          </div>)}</div>
          {stockIssues.length > 0 && <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm font-semibold text-rose-700">موجودی کافی نیست: {stockIssues.join("، ")}</p>}
        </Card>
        <Card>
          <div className="mb-4 flex items-center justify-between gap-3"><h2 className="font-bold">روش‌های پرداخت</h2><button type="button" onClick={() => setPayments(current => [...current.map((payment, index) => current.length === 1 && index === 0 && !payment.amount && total > 0 ? { ...payment, amount: String(total) } : payment), emptyPayment()])} className="inline-flex items-center gap-1 rounded-xl bg-slate-100 px-3 py-2 text-sm font-bold"><Plus size={16} /> افزودن پرداخت یا چک</button></div>
          <div className="space-y-3">
            {payments.map((payment, index) => <div key={index} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
                <label className="text-sm font-semibold">روش پرداخت<select value={payment.method} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, method: event.target.value as PaymentDraft["method"] } : row))} className={inputClass}><option value="cash">نقدی</option><option value="card">کارت‌خوان</option><option value="transfer">کارت‌به‌کارت / واریز</option><option value="check">چک</option></select></label>
                <label className="text-sm font-semibold">مبلغ (ریال)<input min="1" type="number" value={payment.amount || (payments.length === 1 && index === 0 && total > 0 ? String(total) : "")} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, amount: event.target.value } : row))} className={inputClass} /></label>
                <button type="button" disabled={payments.length === 1} onClick={() => setPayments(current => current.filter((_, rowIndex) => rowIndex !== index))} aria-label="حذف روش پرداخت" className="mt-2 self-end rounded-xl p-3 text-rose-600 hover:bg-rose-100 disabled:opacity-40"><X size={19} /></button>
                {payment.method !== "cash" && <label className="text-sm font-semibold md:col-span-2">شماره پیگیری رسید (اختیاری)<input value={payment.receipt_tracking_number} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, receipt_tracking_number: event.target.value } : row))} className={inputClass} /></label>}
                {payment.method === "check" && <>
                  <label className="text-sm font-semibold">شماره چک<input required value={payment.check_number} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, check_number: event.target.value } : row))} className={inputClass} /></label>
                  <label className="text-sm font-semibold">بانک<input required value={payment.check_bank} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, check_bank: event.target.value } : row))} className={inputClass} /></label>
                  <label className="text-sm font-semibold">تاریخ سررسید چک<input required type="date" value={payment.check_due_date} onChange={event => setPayments(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, check_due_date: event.target.value } : row))} className={inputClass} /></label>
                </>}
              </div>
            </div>)}
          </div>
          <div className="mt-4 flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-4 text-sm">
            <p>جمع پرداخت‌ها: <strong>{money(paymentsTotal)}</strong></p>
            <p>مانده فاکتور: <strong className={paymentsTotal > total ? "text-rose-700" : "text-slate-800"}>{money(Math.max(0, total - paymentsTotal))}</strong></p>
          </div>
          <label className="mt-4 block text-sm font-semibold">توضیحات (اختیاری)<textarea name="notes" rows={2} className={inputClass} /></label>
        </Card>
        <div className="sticky bottom-3 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <p className="text-lg font-extrabold">مبلغ کل: <span className="text-sky-700">{money(total)}</span></p>
          <button disabled={busy || stockIssues.length > 0 || products.length === 0} className="rounded-xl bg-sky-600 px-8 py-3 font-bold text-white hover:bg-sky-500">{busy ? "در حال ثبت…" : "ثبت و نمایش فاکتور"}</button>
        </div>
      </form>
    </>
  );
}

function InvoiceDetailPage() {
  const { invoiceId } = useParams();
  const [data, setData] = useState<{ invoice: Invoice; items: InvoiceItem[]; payments: InvoicePayment[] } | null>(null);
  const [error, setError] = useState("");
  const [updatingPayment, setUpdatingPayment] = useState<number | null>(null);
  const [itemSearch, setItemSearch] = useState("");
  const [paymentSearch, setPaymentSearch] = useState("");
  const { notify } = useApp();
  const load = () => api<{ invoice: Invoice; items: InvoiceItem[]; payments: InvoicePayment[] }>(`/api/invoices/${invoiceId}`).then(setData).catch(reason => setError(reason.message));
  useEffect(() => { void load(); }, [invoiceId]);
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <Loading />;
  const { invoice, items, payments } = data;
  const filteredItems = items.filter(item =>
    matchesSearch(`${item.name} ${item.unit} ${item.quantity}`, itemSearch),
  );
  const filteredPayments = payments.filter(payment =>
    matchesSearch(`${payment.method} ${payment.amount} ${payment.receipt_tracking_number || ""} ${payment.check_number || ""} ${payment.check_bank || ""} ${payment.check_due_date || ""} ${payment.is_cleared ? "پاس شده" : "در انتظار پاس شدن"}`, paymentSearch),
  );
  async function clearCheck(paymentId: number) {
    setUpdatingPayment(paymentId);
    setError("");
    try {
      await api(`/api/invoices/${invoice.id}/payments/${paymentId}/clear`, { method: "POST" });
      notify("پاس‌شدن چک تایید شد و مبلغ به پرداخت‌شده اضافه شد.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تایید چک انجام نشد.");
    } finally {
      setUpdatingPayment(null);
    }
  }
  return (
    <>
      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}
      <PageHeader title="جزئیات فاکتور" description={invoice.invoice_number}>
        <button onClick={() => window.print()} className="no-print inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold"><Printer size={18} /> چاپ فاکتور</button>
      </PageHeader>
      <Card className="mx-auto max-w-4xl p-6 sm:p-8">
        <div className="flex flex-col justify-between gap-5 border-b border-slate-200 pb-5 sm:flex-row">
          <div><h2 className="text-xl font-extrabold">فروشگاه</h2><p className="mt-2 text-sm text-slate-500">رسید فروش کالا</p></div>
          <div className="space-y-1 text-sm"><p>شماره: <strong>{invoice.invoice_number}</strong></p><p>تاریخ: {invoice.invoice_date}</p><p>مشتری: {invoice.customer_name}</p></div>
        </div>
        <div className="mt-5">{items.length > 0 && <ListSearch value={itemSearch} onChange={setItemSearch} placeholder="جست‌وجوی کالای فاکتور…" />}{filteredItems.length ? <Table><TableHead><TH>کالا</TH><TH>تعداد</TH><TH>قیمت واحد (ریال)</TH><TH>جمع (ریال)</TH></TableHead><tbody>{filteredItems.map(item => <tr key={item.id}><TD className="font-semibold">{item.name}</TD><TD>{number(item.quantity)} {item.unit}</TD><TD>{money(item.unit_price)}</TD><TD>{money(item.total_amount)}</TD></tr>)}</tbody></Table> : <Empty>{items.length ? "کالایی پیدا نشد." : "ردیفی ثبت نشده است."}</Empty>}</div>
        <div className="mt-5 grid gap-3 border-t border-slate-200 pt-4 sm:grid-cols-3">
          <div className="rounded-xl bg-slate-50 p-4"><p className="text-sm text-slate-500">مبلغ کل</p><p className="mt-1 font-extrabold">{money(invoice.total_amount)}</p></div>
          <div className="rounded-xl bg-emerald-50 p-4"><p className="text-sm text-emerald-700">پرداخت‌شده و چک‌های پاس‌شده</p><p className="mt-1 font-extrabold text-emerald-800">{money(invoice.paid_amount)}</p></div>
          <div className="rounded-xl bg-amber-50 p-4"><p className="text-sm text-amber-700">مانده (با احتساب چک‌های پاس‌نشده)</p><p className="mt-1 font-extrabold text-amber-800">{money(Math.max(0, invoice.total_amount - invoice.paid_amount))}</p></div>
        </div>
        <div className="mt-5 rounded-xl border border-slate-200 p-4">
          <h3 className="mb-3 font-bold">جزئیات پرداخت‌ها و وضعیت چک‌ها</h3>
          {payments.length > 0 && <ListSearch value={paymentSearch} onChange={setPaymentSearch} placeholder="روش، شماره چک، بانک یا سررسید…" />}
          {filteredPayments.length ? <div className="space-y-3">{filteredPayments.map(payment => <div key={payment.id} className="flex flex-col justify-between gap-3 rounded-xl bg-slate-50 p-4 sm:flex-row sm:items-center">
            <div className="grid flex-1 gap-2 text-sm sm:grid-cols-2">
              <p>روش: <strong>{paymentLabel(payment.method)}</strong></p>
              <p>مبلغ: <strong>{money(payment.amount)}</strong></p>
              {payment.receipt_tracking_number && <p>شماره پیگیری رسید: <strong>{payment.receipt_tracking_number}</strong></p>}
              {payment.method === "check" && <>
                <p>شماره چک: <strong>{payment.check_number}</strong></p>
                <p>بانک: <strong>{payment.check_bank}</strong></p>
                <p>تاریخ سررسید: <strong>{payment.check_due_date}</strong></p>
                {payment.is_cleared && payment.cleared_at && <p className="text-emerald-700">تاریخ پاس‌شدن: <strong>{new Date(payment.cleared_at).toLocaleDateString("fa-IR")}</strong></p>}
              </>}
            </div>
            {payment.method === "check" && (payment.is_cleared
              ? <span className="inline-flex items-center gap-2 self-start rounded-full bg-emerald-100 px-3 py-2 text-sm font-bold text-emerald-800 sm:self-center"><Check size={16} /> پاس شده</span>
              : <button disabled={updatingPayment === payment.id} onClick={() => void clearCheck(payment.id)} className="no-print inline-flex items-center justify-center gap-2 self-start rounded-xl bg-emerald-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-60 sm:self-center">{updatingPayment === payment.id ? "در حال ثبت…" : "تایید پاس‌شدن چک"}</button>)}
          </div>)}</div> : <p className="text-sm text-slate-500">{payments.length ? "پرداختی پیدا نشد." : "جزئیات پرداخت برای این فاکتور ثبت نشده است."}</p>}
        </div>
        {invoice.notes && <p className="mt-4 rounded-xl border border-slate-100 p-4 text-sm text-slate-600">{invoice.notes}</p>}
      </Card>
    </>
  );
}

export default App;
