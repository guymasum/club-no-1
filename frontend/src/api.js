const API_URL = import.meta.env.VITE_API_URL || "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  login: (username, password) =>
    request("/auth/login", { method: "POST", body: { username, password }, auth: false }),
  changePassword: (current_password, new_password) =>
    request("/auth/password", { method: "PUT", body: { current_password, new_password } }),
  customers: () => request("/customers"),
  products: () => request("/products"),
  openOrders: () => request("/orders"),
  order: (id) => request(`/orders/${id}`),
  createOrder: (customer_id) => request("/orders", { method: "POST", body: { customer_id } }),
  addItem: (orderId, product_id, quantity) =>
    request(`/orders/${orderId}/items`, { method: "POST", body: { product_id, quantity } }),
  removeItem: (orderId, itemId) =>
    request(`/orders/${orderId}/items/${itemId}`, { method: "DELETE" }),
  finalizeOrder: (orderId) => request(`/orders/${orderId}/bill`, { method: "POST" }),
  bills: () => request("/bills"),
  bill: (billId) => request(`/bills/${billId}`),
  // The PDF route needs the same Bearer token as everything else, so it
  // can't be a plain <a href>: a browser navigation never attaches the
  // Authorization header. Fetch it as a blob instead.
  billPdf: async (billId) => {
    const token = getToken();
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_URL}/bills/${billId}/pdf`, { headers });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || detail;
      } catch {
        // response had no JSON body
      }
      throw new ApiError(detail, res.status);
    }
    return res.blob();
  },

  // admin
  waiters: () => request("/admin/waiters"),
  createWaiter: (data) => request("/admin/waiters", { method: "POST", body: data }),
  updateWaiter: (id, data) => request(`/admin/waiters/${id}`, { method: "PUT", body: data }),
  allProducts: () => request("/admin/products"),
  createProduct: (data) => request("/admin/products", { method: "POST", body: data }),
  updateProduct: (id, data) => request(`/admin/products/${id}`, { method: "PUT", body: data }),
  createCustomer: (data) => request("/admin/customers", { method: "POST", body: data }),
  updateCustomer: (id, data) => request(`/admin/customers/${id}`, { method: "PUT", body: data }),
  deleteCustomer: (id) => request(`/admin/customers/${id}`, { method: "DELETE" }),
  stockItems: () => request("/admin/stock-items"),
  createStockItem: (data) => request("/admin/stock-items", { method: "POST", body: data }),
  updateStockItem: (id, data) => request(`/admin/stock-items/${id}`, { method: "PUT", body: data }),
  restockItem: (id, delta) =>
    request(`/admin/stock-items/${id}/restock`, { method: "POST", body: { delta } }),
};

export { ApiError, getToken };
