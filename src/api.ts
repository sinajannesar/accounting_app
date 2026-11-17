export type User = {
  id: number;
  username: string;
  full_name: string;
};

export type Product = {
  id: number;
  code: string;
  name: string;
  category: string;
  unit: string;
  purchase_price: number;
  sale_price: number;
  stock: number;
  description: string | null;
};

export type Customer = {
  id: number;
  name: string;
  phone: string | null;
  address: string | null;
  notes: string | null;
};

export type Invoice = {
  id: number;
  invoice_number: string;
  customer_name: string;
  invoice_date: string;
  total_amount: number;
  paid_amount: number;
  status: string;
  payment_method: string;
  receipt_tracking_number: string | null;
  check_number: string | null;
  check_bank: string | null;
  check_due_date: string | null;
  notes: string | null;
  payments?: InvoicePayment[];
};

export type InvoicePayment = {
  id: number;
  invoice_id: number;
  method: string;
  amount: number;
  receipt_tracking_number: string | null;
  check_number: string | null;
  check_bank: string | null;
  check_due_date: string | null;
  is_cleared: number;
  cleared_at: string | null;
};

export type InvoiceItem = {
  id: number;
  name: string;
  unit: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
};

export type DashboardData = {
  summary: {
    total_products: number;
    total_stock: number;
    inventory_value: number;
    low_stock_count: number;
  };
  latest_invoices: Invoice[];
  sales_today: number;
  sales_month: number;
  low_stock_items: Product[];
  low_stock_threshold: number;
};

export type InventoryData = {
  products: Product[];
  low_stock_items: Product[];
  stock_moves: {
    id: number;
    product_name: string;
    direction: "in" | "out";
    quantity: number;
    note: string | null;
    created_at: string;
  }[];
  low_stock_threshold: number;
};

export async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    credentials: "same-origin",
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  const data = (await response.json().catch(() => ({}))) as T & {
    error?: string;
  };
  if (!response.ok) {
    throw new Error(data.error || "ارتباط با سرور برقرار نشد.");
  }
  return data;
}

export const money = (value: number) =>
  `${new Intl.NumberFormat("fa-IR").format(Math.round(value || 0))} ریال`;

export const number = (value: number) =>
  new Intl.NumberFormat("fa-IR").format(value || 0);

export const paymentLabel = (method: string) =>
  ({
    cash: "نقدی",
    card: "کارت‌خوان",
    transfer: "واریز بانکی",
    check: "چک",
    mixed: "ترکیبی",
  })[method] || method;
