import { Plus, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api, money, number } from "./api";

type Account = {
  id: number;
  code: string;
  name: string;
  level: number;
  account_type: string;
  parent_name: string | null;
  is_postable?: number;
};

type JournalEntry = {
  id: number;
  entry_number: number;
  entry_date: string;
  due_date: string | null;
  description: string | null;
  total_debit: number;
  total_credit: number;
};

type JournalLine = {
  id: number;
  account_id: number;
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  line_description: string | null;
};

type DraftLine = {
  key: number;
  account_id: string;
  debit: string;
  credit: string;
  line_description: string;
};

type DateRange = {
  date_from: string;
  date_to: string;
};

type GeneralLedgerAccount = Account & {
  total_debit: number;
  total_credit: number;
  balance: number;
  movements: {
    entry_date: string;
    entry_number: number;
    entry_description: string | null;
    account_code: string;
    account_name: string;
    debit: number;
    credit: number;
    line_description: string | null;
  }[];
};

type TrialBalance = {
  rows: (Account & {
    period_debit: number;
    period_credit: number;
    debit_balance: number;
    credit_balance: number;
  })[];
  total_debit: number;
  total_credit: number;
  total_debit_balance: number;
  total_credit_balance: number;
};

type IncomeStatement = {
  income_items: (Account & { amount: number })[];
  expense_items: (Account & { amount: number })[];
  total_income: number;
  total_expense: number;
  net_profit: number;
};

const fieldClass = "mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm outline-none focus:border-sky-500 focus:ring-4 focus:ring-sky-100";

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>{children}</section>;
}

function PageHeader({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div><h1 className="text-2xl font-extrabold text-slate-950">{title}</h1><p className="mt-2 text-sm text-slate-500">{description}</p></div>
      {children}
    </header>
  );
}

function Table({ children }: { children: ReactNode }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-right text-sm">{children}</table></div>;
}

function Head({ children }: { children: ReactNode }) {
  return <thead className="bg-slate-50 text-xs font-bold text-slate-500"><tr>{children}</tr></thead>;
}

function Cell({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return <td className={`border-t border-slate-100 px-4 py-3 ${className}`}>{children}</td>;
}

function ErrorMessage({ message }: { message: string }) {
  return <div role="alert" className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{message}</div>;
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="py-10 text-center text-sm text-slate-400">{children}</p>;
}

function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label className="relative block sm:max-w-sm">
      <Search size={17} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} className={`${fieldClass} pr-10`} />
    </label>
  );
}

function matchesSearch(text: string, search: string) {
  const normalize = (value: string) => value.toLocaleLowerCase()
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[۰-۹٠-٩]/g, digit => {
      const code = digit.charCodeAt(0);
      return String(code >= 0x6f0 ? code - 0x6f0 : code - 0x660);
    })
    .trim();
  return normalize(text).includes(normalize(search));
}

function DateFilters({ value, onChange, onApply }: { value: DateRange; onChange: (value: DateRange) => void; onApply: () => void }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <label className="text-sm font-semibold">از تاریخ<input type="date" value={value.date_from} onChange={event => onChange({ ...value, date_from: event.target.value })} className={fieldClass} /></label>
      <label className="text-sm font-semibold">تا تاریخ<input type="date" value={value.date_to} onChange={event => onChange({ ...value, date_to: event.target.value })} className={fieldClass} /></label>
      <button onClick={onApply} className="rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white">نمایش گزارش</button>
    </div>
  );
}

function queryForRange(range: DateRange) {
  const query = new URLSearchParams();
  if (range.date_from) query.set("date_from", range.date_from);
  if (range.date_to) query.set("date_to", range.date_to);
  const value = query.toString();
  return value ? `?${value}` : "";
}

function today() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function newDraftLine(key: number): DraftLine {
  return { key, account_id: "", debit: "", credit: "", line_description: "" };
}

export function JournalEntriesPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [search, setSearch] = useState("");
  const [range, setRange] = useState<DateRange>({ date_from: "", date_to: "" });
  const [showForm, setShowForm] = useState(false);
  const [selected, setSelected] = useState<{ entry: JournalEntry; lines: JournalLine[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [lines, setLines] = useState<DraftLine[]>([newDraftLine(1), newDraftLine(2)]);
  const nextLineKey = useRef(3);

  async function loadEntries() {
    setLoading(true);
    setError("");
    try {
      const [accountResult, entryResult] = await Promise.all([
        api<{ accounts: Account[] }>("/api/accounting/accounts?postable=1"),
        api<{ entries: JournalEntry[] }>(`/api/accounting/entries${queryForRange(range)}`),
      ]);
      setAccounts(accountResult.accounts);
      setEntries(entryResult.entries);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "دریافت اسناد انجام نشد.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadEntries(); }, []);

  const filtered = entries.filter(entry => matchesSearch(
    `${entry.entry_number} ${entry.entry_date} ${entry.description || ""}`,
    search,
  ));
  const totalDebit = lines.reduce((sum, line) => sum + Number(line.debit || 0), 0);
  const totalCredit = lines.reduce((sum, line) => sum + Number(line.credit || 0), 0);

  function updateLine(key: number, patch: Partial<DraftLine>) {
    setLines(current => current.map(line => line.key === key ? { ...line, ...patch } : line));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const result = await api<{ entry_number: number }>("/api/accounting/entries", {
        method: "POST",
        body: JSON.stringify({
          entry_date: form.get("entry_date"),
          due_date: form.get("due_date"),
          description: form.get("description"),
          lines: lines.map(line => ({
            account_id: Number(line.account_id),
            debit: Number(line.debit || 0),
            credit: Number(line.credit || 0),
            line_description: line.line_description,
          })),
        }),
      });
      setShowForm(false);
      setLines([newDraftLine(nextLineKey.current++), newDraftLine(nextLineKey.current++)]);
      setNotice(`سند شماره ${number(result.entry_number)} ثبت شد.`);
      await loadEntries();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "ثبت سند انجام نشد.");
    } finally {
      setSaving(false);
    }
  }

  async function openEntry(entry: JournalEntry) {
    setError("");
    try {
      const result = await api<{ entry: JournalEntry; lines: JournalLine[] }>(`/api/accounting/entries/${entry.id}`);
      setSelected({ entry: result.entry, lines: result.lines });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "نمایش سند انجام نشد.");
    }
  }

  return (
    <>
      <PageHeader title="اسناد حسابداری" description="ثبت اسناد دوطرفه با کنترل توازن بدهکار و بستانکار">
        <button onClick={() => { setShowForm(value => !value); setSelected(null); }} className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white"><Plus size={18} /> سند جدید</button>
      </PageHeader>
      {error && <ErrorMessage message={error} />}
      {notice && <p role="status" className="mb-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">{notice}</p>}
      {showForm && <Card className="mb-5">
        <h2 className="mb-4 font-bold">ثبت سند جدید</h2>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="text-sm font-semibold">تاریخ سند<input required type="date" name="entry_date" defaultValue={today()} className={fieldClass} /></label>
            <label className="text-sm font-semibold">تاریخ سررسید (اختیاری)<input type="date" name="due_date" className={fieldClass} /></label>
            <label className="text-sm font-semibold sm:col-span-1">شرح سند<input name="description" className={fieldClass} /></label>
          </div>
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-bold">سطرهای سند</h3>
            <button type="button" onClick={() => setLines(current => [...current, newDraftLine(nextLineKey.current++)])} className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-bold">افزودن سطر</button>
          </div>
          <div className="space-y-3">
            {lines.map((line, index) => <div key={line.key} className="grid gap-3 rounded-xl bg-slate-50 p-3 sm:grid-cols-2 lg:grid-cols-[minmax(220px,2fr)_1fr_1fr_minmax(140px,1fr)_auto] lg:items-end">
              <label className="text-sm font-semibold">حساب<select required value={line.account_id} onChange={event => updateLine(line.key, { account_id: event.target.value })} className={fieldClass}><option value="">انتخاب حساب معین/تفصیلی</option>{accounts.map(account => <option key={account.id} value={account.id}>{account.code} — {account.name}</option>)}</select></label>
              <label className="text-sm font-semibold">بدهکار (ریال)<input min="0" type="number" value={line.debit} onChange={event => updateLine(line.key, { debit: event.target.value, credit: event.target.value ? "" : line.credit })} className={fieldClass} /></label>
              <label className="text-sm font-semibold">بستانکار (ریال)<input min="0" type="number" value={line.credit} onChange={event => updateLine(line.key, { credit: event.target.value, debit: event.target.value ? "" : line.debit })} className={fieldClass} /></label>
              <label className="text-sm font-semibold">شرح سطر<input value={line.line_description} onChange={event => updateLine(line.key, { line_description: event.target.value })} className={fieldClass} /></label>
              <button type="button" disabled={lines.length <= 2} onClick={() => setLines(current => current.filter(item => item.key !== line.key))} aria-label={`حذف سطر ${index + 1}`} className="rounded-xl p-3 text-rose-600 hover:bg-rose-100 disabled:opacity-40"><X size={18} /></button>
            </div>)}
          </div>
          <div className="flex flex-wrap justify-between gap-2 rounded-xl bg-slate-50 p-4 text-sm">
            <span>جمع بدهکار: <strong>{money(totalDebit)}</strong></span>
            <span>جمع بستانکار: <strong>{money(totalCredit)}</strong></span>
            <span className={Math.abs(totalDebit - totalCredit) < 0.01 ? "font-bold text-emerald-700" : "font-bold text-rose-700"}>{Math.abs(totalDebit - totalCredit) < 0.01 ? "سند تراز است" : "سند تراز نیست"}</span>
          </div>
          <button disabled={saving || lines.length < 2} className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">{saving ? "در حال ثبت…" : "ثبت سند"}</button>
        </form>
      </Card>}
      {selected && <Card className="mb-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div><h2 className="font-bold">سند شماره {number(selected.entry.entry_number)}</h2><p className="mt-1 text-sm text-slate-500">{selected.entry.entry_date} — {selected.entry.description || "بدون شرح"}</p></div>
          <button onClick={() => setSelected(null)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="بستن"><X size={18} /></button>
        </div>
        <Table><Head><th className="px-4 py-3">حساب</th><th className="px-4 py-3">شرح</th><th className="px-4 py-3">بدهکار</th><th className="px-4 py-3">بستانکار</th></Head><tbody>{selected.lines.map(line => <tr key={line.id}><Cell>{line.account_code} — {line.account_name}</Cell><Cell>{line.line_description || "—"}</Cell><Cell>{money(line.debit)}</Cell><Cell>{money(line.credit)}</Cell></tr>)}</tbody></Table>
      </Card>}
      <Card>
        <div className="mb-4 grid gap-3 sm:grid-cols-[minmax(220px,1fr)_auto_auto] sm:items-end">
          <div><h2 className="mb-3 font-bold">فهرست اسناد</h2><SearchBox value={search} onChange={setSearch} placeholder="شماره، تاریخ یا شرح سند…" /></div>
          <label className="text-sm font-semibold">از تاریخ<input type="date" value={range.date_from} onChange={event => setRange({ ...range, date_from: event.target.value })} className={fieldClass} /></label>
          <label className="text-sm font-semibold">تا تاریخ<input type="date" value={range.date_to} onChange={event => setRange({ ...range, date_to: event.target.value })} className={fieldClass} /></label>
          <button onClick={() => void loadEntries()} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-bold sm:col-start-3">اعمال بازه</button>
        </div>
        {loading ? <Empty>در حال دریافت اسناد…</Empty> : filtered.length ? <Table><Head><th className="px-4 py-3">شماره</th><th className="px-4 py-3">تاریخ</th><th className="px-4 py-3">شرح</th><th className="px-4 py-3">جمع بدهکار</th><th className="px-4 py-3">جمع بستانکار</th></Head><tbody>{filtered.map(entry => <tr key={entry.id} onClick={() => void openEntry(entry)} className="cursor-pointer hover:bg-sky-50"><Cell className="font-bold text-sky-700">{number(entry.entry_number)}</Cell><Cell>{entry.entry_date}</Cell><Cell>{entry.description || "—"}</Cell><Cell>{money(entry.total_debit)}</Cell><Cell>{money(entry.total_credit)}</Cell></tr>)}</tbody></Table> : <Empty>سندی برای این جست‌وجو پیدا نشد.</Empty>}
      </Card>
    </>
  );
}

export function GeneralLedgerPage() {
  const [range, setRange] = useState<DateRange>({ date_from: "", date_to: "" });
  const [accounts, setAccounts] = useState<GeneralLedgerAccount[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const result = await api<{ accounts: GeneralLedgerAccount[] }>(`/api/accounting/general-ledger${queryForRange(range)}`);
      setAccounts(result.accounts);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "گزارش دفتر کل دریافت نشد.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);
  const filtered = accounts.filter(account => matchesSearch(`${account.code} ${account.name} ${account.account_type}`, search));
  return (
    <>
      <PageHeader title="دفتر کل" description="گردش بدهکار و بستانکار حساب‌های کل در بازهٔ انتخابی" />
      {error && <ErrorMessage message={error} />}
      <Card className="mb-5"><DateFilters value={range} onChange={setRange} onApply={() => void load()} /></Card>
      <div className="mb-4"><SearchBox value={search} onChange={setSearch} placeholder="جست‌وجوی کد یا نام حساب کل…" /></div>
      {loading ? <Card><Empty>در حال دریافت دفتر کل…</Empty></Card> : filtered.length ? <div className="space-y-4">{filtered.map(account => <Card key={account.id}>
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div><h2 className="font-extrabold">{account.code} — {account.name}</h2><p className="mt-1 text-xs text-slate-500">{account.movements.length} گردش</p></div>
          <div className="flex flex-wrap gap-3 text-sm"><span>بدهکار: <strong>{money(account.total_debit)}</strong></span><span>بستانکار: <strong>{money(account.total_credit)}</strong></span><span>مانده: <strong>{money(account.balance)}</strong></span></div>
        </div>
        {account.movements.length ? <Table><Head><th className="px-4 py-3">تاریخ</th><th className="px-4 py-3">شماره سند</th><th className="px-4 py-3">حساب معین/تفصیلی</th><th className="px-4 py-3">شرح</th><th className="px-4 py-3">بدهکار</th><th className="px-4 py-3">بستانکار</th></Head><tbody>{account.movements.map((movement, index) => <tr key={`${movement.entry_number}-${index}`}><Cell>{movement.entry_date}</Cell><Cell>{number(movement.entry_number)}</Cell><Cell>{movement.account_code} — {movement.account_name}</Cell><Cell>{movement.line_description || movement.entry_description || "—"}</Cell><Cell>{money(movement.debit)}</Cell><Cell>{money(movement.credit)}</Cell></tr>)}</tbody></Table> : <Empty>در این بازه گردش ثبت نشده است.</Empty>}
      </Card>)}</div> : <Card><Empty>در این بازه گردش دفتر کلی وجود ندارد.</Empty></Card>}
    </>
  );
}

export function FinancialReportsPage() {
  const [range, setRange] = useState<DateRange>({ date_from: "", date_to: "" });
  const [report, setReport] = useState<"trial" | "income">("trial");
  const [trial, setTrial] = useState<TrialBalance | null>(null);
  const [income, setIncome] = useState<IncomeStatement | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const suffix = queryForRange(range);
      const [trialResult, incomeResult] = await Promise.all([
        api<TrialBalance>(`/api/accounting/reports/trial-balance${suffix}`),
        api<IncomeStatement>(`/api/accounting/reports/income-statement${suffix}`),
      ]);
      setTrial(trialResult);
      setIncome(incomeResult);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "گزارش مالی دریافت نشد.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);
  const filteredTrial = useMemo(
    () => trial?.rows.filter(row => matchesSearch(`${row.code} ${row.name}`, search)) || [],
    [trial, search],
  );
  const filteredIncome = useMemo(() => ({
    income: income?.income_items.filter(row => matchesSearch(`${row.code} ${row.name}`, search)) || [],
    expense: income?.expense_items.filter(row => matchesSearch(`${row.code} ${row.name}`, search)) || [],
  }), [income, search]);

  return (
    <>
      <PageHeader title="گزارش‌های مالی" description="تراز آزمایشی و صورت سود و زیان بر مبنای اسناد ثبت‌شده" />
      {error && <ErrorMessage message={error} />}
      <Card className="mb-5"><DateFilters value={range} onChange={setRange} onApply={() => void load()} /></Card>
      <div className="mb-4 flex flex-wrap gap-2">
        <button onClick={() => setReport("trial")} className={`rounded-xl px-4 py-3 text-sm font-bold ${report === "trial" ? "bg-sky-600 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200"}`}>تراز آزمایشی</button>
        <button onClick={() => setReport("income")} className={`rounded-xl px-4 py-3 text-sm font-bold ${report === "income" ? "bg-sky-600 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200"}`}>سود و زیان</button>
      </div>
      <div className="mb-4"><SearchBox value={search} onChange={setSearch} placeholder="جست‌وجوی کد یا نام حساب…" /></div>
      {loading ? <Card><Empty>در حال محاسبه گزارش…</Empty></Card> : report === "trial" && trial ? <Card>
        <h2 className="mb-4 font-bold">تراز آزمایشی</h2>
        {filteredTrial.length ? <Table><Head><th className="px-4 py-3">کد</th><th className="px-4 py-3">حساب</th><th className="px-4 py-3">گردش بدهکار</th><th className="px-4 py-3">گردش بستانکار</th><th className="px-4 py-3">مانده بدهکار</th><th className="px-4 py-3">مانده بستانکار</th></Head><tbody>{filteredTrial.map(row => <tr key={row.id}><Cell>{row.code}</Cell><Cell>{row.name}</Cell><Cell>{money(row.period_debit)}</Cell><Cell>{money(row.period_credit)}</Cell><Cell>{money(row.debit_balance)}</Cell><Cell>{money(row.credit_balance)}</Cell></tr>)}</tbody><tfoot className="bg-slate-50 font-extrabold"><tr><Cell /><Cell>جمع کل</Cell><Cell>{money(trial.total_debit)}</Cell><Cell>{money(trial.total_credit)}</Cell><Cell>{money(trial.total_debit_balance)}</Cell><Cell>{money(trial.total_credit_balance)}</Cell></tr></tfoot></Table> : <Empty>گردشی برای این بازه ثبت نشده است.</Empty>}
        <p className={`mt-4 text-sm font-bold ${Math.abs(trial.total_debit - trial.total_credit) <= 0.01 ? "text-emerald-700" : "text-rose-700"}`}>{Math.abs(trial.total_debit - trial.total_credit) <= 0.01 ? "جمع گردش بدهکار و بستانکار برابر است." : "هشدار: جمع گردش بدهکار و بستانکار برابر نیست."}</p>
      </Card> : income ? <div className="space-y-4">
        <Card><h2 className="mb-4 font-bold">درآمدها</h2>{filteredIncome.income.length ? <Table><Head><th className="px-4 py-3">کد</th><th className="px-4 py-3">حساب</th><th className="px-4 py-3">مبلغ</th></Head><tbody>{filteredIncome.income.map(row => <tr key={row.id}><Cell>{row.code}</Cell><Cell>{row.name}</Cell><Cell>{money(row.amount)}</Cell></tr>)}</tbody></Table> : <Empty>درآمدی برای این بازه ثبت نشده است.</Empty>}<p className="mt-4 text-left font-extrabold">جمع درآمد: {money(income.total_income)}</p></Card>
        <Card><h2 className="mb-4 font-bold">هزینه‌ها</h2>{filteredIncome.expense.length ? <Table><Head><th className="px-4 py-3">کد</th><th className="px-4 py-3">حساب</th><th className="px-4 py-3">مبلغ</th></Head><tbody>{filteredIncome.expense.map(row => <tr key={row.id}><Cell>{row.code}</Cell><Cell>{row.name}</Cell><Cell>{money(row.amount)}</Cell></tr>)}</tbody></Table> : <Empty>هزینه‌ای برای این بازه ثبت نشده است.</Empty>}<p className="mt-4 text-left font-extrabold">جمع هزینه: {money(income.total_expense)}</p></Card>
        <Card className="flex flex-wrap items-center justify-between gap-3"><strong>{income.net_profit >= 0 ? "سود خالص" : "زیان خالص"}</strong><strong className={income.net_profit >= 0 ? "text-emerald-700" : "text-rose-700"}>{money(Math.abs(income.net_profit))}</strong></Card>
      </div> : <Card><Empty>اطلاعات گزارش آماده نیست.</Empty></Card>}
    </>
  );
}
