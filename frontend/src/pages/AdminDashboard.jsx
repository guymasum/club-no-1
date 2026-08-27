import { useEffect, useState } from "react";
import TopBar from "../components/TopBar.jsx";
import { api, ApiError } from "../api.js";

function useAsyncAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const run = async (fn) => {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, run };
}

function WaitersPanel() {
  const [waiters, setWaiters] = useState([]);
  const [form, setForm] = useState({ name: "", username: "", password: "", role: "waiter" });
  const { busy, error, run } = useAsyncAction();

  const load = () => api.waiters().then(setWaiters);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createWaiter(form);
      setForm({ name: "", username: "", password: "", role: "waiter" });
      await load();
    });
  };

  const toggleRole = (w) =>
    run(async () => {
      await api.updateWaiter(w.waiter_id, { role: w.role === "admin" ? "waiter" : "admin" });
      await load();
    });

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Waiters</h3>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Username</th>
            <th>Role</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {waiters.map((w) => (
            <tr key={w.waiter_id}>
              <td>{w.name}</td>
              <td>{w.username}</td>
              <td>{w.role}</td>
              <td>
                <button className="secondary" onClick={() => toggleRole(w)} disabled={busy}>
                  Make {w.role === "admin" ? "waiter" : "admin"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4>Add waiter</h4>
      <form onSubmit={handleCreate}>
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="Username"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="waiter">waiter</option>
          <option value="admin">admin</option>
        </select>
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Add waiter
        </button>
      </form>
    </div>
  );
}

function ProductsPanel() {
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ name: "", category: "drink", price: "" });
  const { busy, error, run } = useAsyncAction();

  const load = () => api.allProducts().then(setProducts);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createProduct({ ...form, price: Number(form.price) });
      setForm({ name: "", category: "drink", price: "" });
      await load();
    });
  };

  const toggleActive = (p) =>
    run(async () => {
      await api.updateProduct(p.product_id, { active: !p.active });
      await load();
    });

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Products</h3>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.product_id} style={{ opacity: p.active ? 1 : 0.55 }}>
              <td>
                {p.name}
                {!p.active && <span className="tag">inactive</span>}
              </td>
              <td>{p.category}</td>
              <td>${p.price.toFixed(2)}</td>
              <td>
                <button className="secondary" onClick={() => toggleActive(p)} disabled={busy}>
                  {p.active ? "Deactivate" : "Activate"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4>Add product</h4>
      <form onSubmit={handleCreate}>
        <input
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
          <option value="drink">drink</option>
          <option value="food">food</option>
        </select>
        <input
          placeholder="Price"
          type="number"
          step="0.01"
          value={form.price}
          onChange={(e) => setForm({ ...form, price: e.target.value })}
          required
        />
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Add product
        </button>
      </form>
    </div>
  );
}

function CustomersPanel() {
  const [customers, setCustomers] = useState([]);
  const [name, setName] = useState("");
  const { busy, error, run } = useAsyncAction();

  const load = () => api.customers().then(setCustomers);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createCustomer({ name });
      setName("");
      await load();
    });
  };

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Customers</h3>
      <ul className="product-list">
        {customers.map((c) => (
          <li key={c.customer_id}>
            <span>{c.name}</span>
          </li>
        ))}
      </ul>
      <h4>Add customer</h4>
      <form onSubmit={handleCreate}>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Add customer
        </button>
      </form>
    </div>
  );
}

export default function AdminDashboard() {
  return (
    <>
      <TopBar />
      <div className="page">
        <WaitersPanel />
        <ProductsPanel />
        <CustomersPanel />
      </div>
    </>
  );
}
