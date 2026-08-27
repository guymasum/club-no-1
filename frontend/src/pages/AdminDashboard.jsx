import { useEffect, useState } from "react";
import TopBar from "../components/TopBar.jsx";
import { api, ApiError } from "../api.js";
import { formatCurrency } from "../format.js";
import { categoryLabel, roleLabel } from "../labels.js";

function useAsyncAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const run = async (fn) => {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue");
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, run };
}

function WaitersPanel() {
  const [waiters, setWaiters] = useState([]);
  const [form, setForm] = useState({ name: "", username: "", password: "", role: "waiter" });
  const [resettingId, setResettingId] = useState(null);
  const [newPassword, setNewPassword] = useState("");
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

  const toggleActive = (w) =>
    run(async () => {
      await api.updateWaiter(w.waiter_id, { active: !w.active });
      await load();
    });

  const saveNewPassword = () =>
    run(async () => {
      await api.updateWaiter(resettingId, { password: newPassword });
      setResettingId(null);
      setNewPassword("");
    });

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Serveurs</h3>
      <table>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Nom d'utilisateur</th>
            <th>Rôle</th>
            <th colSpan={3}></th>
          </tr>
        </thead>
        <tbody>
          {waiters.map((w) =>
            resettingId === w.waiter_id ? (
              <tr key={w.waiter_id}>
                <td>{w.name}</td>
                <td>{w.username}</td>
                <td colSpan={4}>
                  <label className="muted">Nouveau mot de passe pour {w.name}</label>
                  <input
                    type="password"
                    minLength={4}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    autoFocus
                  />
                  <div style={{ marginTop: 10 }}>
                    <button onClick={saveNewPassword} disabled={busy || newPassword.length < 4} style={{ marginRight: 6 }}>
                      Enregistrer
                    </button>
                    <button
                      className="secondary"
                      onClick={() => {
                        setResettingId(null);
                        setNewPassword("");
                      }}
                      disabled={busy}
                    >
                      Annuler
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr key={w.waiter_id} style={{ opacity: w.active ? 1 : 0.55 }}>
                <td>
                  {w.name}
                  {!w.active && <span className="tag">inactif</span>}
                </td>
                <td>{w.username}</td>
                <td>{roleLabel(w.role)}</td>
                <td>
                  <button className="secondary" onClick={() => toggleRole(w)} disabled={busy}>
                    {w.role === "admin" ? "Rétrograder en serveur" : "Promouvoir en admin"}
                  </button>
                </td>
                <td>
                  <button
                    className="secondary"
                    onClick={() => {
                      setResettingId(w.waiter_id);
                      setNewPassword("");
                    }}
                    disabled={busy}
                  >
                    Changer le mot de passe
                  </button>
                </td>
                <td>
                  <button
                    className={w.active ? "danger" : "secondary"}
                    onClick={() => toggleActive(w)}
                    disabled={busy}
                  >
                    {w.active ? "Retirer" : "Réactiver"}
                  </button>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>

      <h4>Ajouter un serveur</h4>
      <form onSubmit={handleCreate}>
        <input
          placeholder="Nom"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="Nom d'utilisateur"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          placeholder="Mot de passe"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="waiter">Serveur</option>
          <option value="admin">Administrateur</option>
        </select>
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Ajouter le serveur
        </button>
      </form>
    </div>
  );
}

const PRODUCT_CATEGORIES = [
  { value: "beer", label: "Bière" },
  { value: "wine", label: "Vin" },
  { value: "whisky", label: "Whisky" },
  { value: "food", label: "Plat" },
];

/** Stock item picker + "portions per sale" input, shared by the create and
 * inline-edit forms. `state`/`setState` hold { stock_item_id, portions_per_sale }
 * where stock_item_id is "" for "no tracking" or a stock_item_id as a string. */
function StockLinkFields({ stockItems, state, setState }) {
  return (
    <>
      <label className="muted">Suivi de stock (optionnel)</label>
      <select
        value={state.stock_item_id}
        onChange={(e) => setState({ ...state, stock_item_id: e.target.value })}
      >
        <option value="">Aucun suivi</option>
        {stockItems.map((s) => (
          <option key={s.stock_item_id} value={s.stock_item_id}>
            {s.name}
          </option>
        ))}
      </select>
      {state.stock_item_id && (
        <>
          <label className="muted">Portions consommées par vente</label>
          <input
            type="number"
            min="1"
            step="1"
            value={state.portions_per_sale}
            onChange={(e) => setState({ ...state, portions_per_sale: e.target.value })}
          />
        </>
      )}
    </>
  );
}

function ProductsPanel({ stockItems }) {
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({
    name: "",
    category: "beer",
    price: "",
    stock_item_id: "",
    portions_per_sale: "1",
  });
  const [editing, setEditing] = useState(null);
  const { busy, error, run } = useAsyncAction();

  const load = () => api.allProducts().then(setProducts);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createProduct({
        name: form.name,
        category: form.category,
        price: Number(form.price),
        stock_item_id: form.stock_item_id ? Number(form.stock_item_id) : null,
        portions_per_sale: form.stock_item_id ? Number(form.portions_per_sale) || 1 : 1,
      });
      setForm({ name: "", category: "beer", price: "", stock_item_id: "", portions_per_sale: "1" });
      await load();
    });
  };

  const toggleActive = (p) =>
    run(async () => {
      await api.updateProduct(p.product_id, { active: !p.active });
      await load();
    });

  const startEdit = (p) =>
    setEditing({
      id: p.product_id,
      name: p.name,
      category: p.category,
      price: String(p.price),
      stock_item_id: p.stock_item_id ? String(p.stock_item_id) : "",
      portions_per_sale: String(p.portions_per_sale),
    });

  const saveEdit = () =>
    run(async () => {
      await api.updateProduct(editing.id, {
        name: editing.name,
        category: editing.category,
        price: Number(editing.price),
        stock_item_id: editing.stock_item_id ? Number(editing.stock_item_id) : null,
        clear_stock_item: !editing.stock_item_id,
        portions_per_sale: editing.stock_item_id ? Number(editing.portions_per_sale) || 1 : 1,
      });
      setEditing(null);
      await load();
    });

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Produits</h3>
      <table>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Catégorie</th>
            <th>Prix</th>
            <th>Stock</th>
            <th colSpan={2}></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) =>
            editing?.id === p.product_id ? (
              <tr key={p.product_id}>
                <td>
                  <input
                    value={editing.name}
                    onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                  />
                </td>
                <td>
                  <select
                    value={editing.category}
                    onChange={(e) => setEditing({ ...editing, category: e.target.value })}
                  >
                    {PRODUCT_CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    value={editing.price}
                    onChange={(e) => setEditing({ ...editing, price: e.target.value })}
                  />
                </td>
                <td colSpan={3}>
                  <StockLinkFields stockItems={stockItems} state={editing} setState={setEditing} />
                  <div style={{ marginTop: 10 }}>
                    <button onClick={saveEdit} disabled={busy} style={{ marginRight: 6 }}>
                      Enregistrer
                    </button>
                    <button className="secondary" onClick={() => setEditing(null)} disabled={busy}>
                      Annuler
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr key={p.product_id} style={{ opacity: p.active ? 1 : 0.55 }}>
                <td>
                  {p.name}
                  {!p.active && <span className="tag">inactif</span>}
                </td>
                <td>{categoryLabel(p.category)}</td>
                <td>{formatCurrency(p.price)}</td>
                <td>{p.stock_remaining === null ? "—" : p.stock_remaining}</td>
                <td>
                  <button className="secondary" onClick={() => startEdit(p)} disabled={busy}>
                    Modifier
                  </button>
                </td>
                <td>
                  <button className="secondary" onClick={() => toggleActive(p)} disabled={busy}>
                    {p.active ? "Désactiver" : "Activer"}
                  </button>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>

      <h4>Ajouter un produit</h4>
      <form onSubmit={handleCreate}>
        <input
          placeholder="Nom"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
          {PRODUCT_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <input
          placeholder="Prix (BIF)"
          type="number"
          step="1"
          min="0"
          value={form.price}
          onChange={(e) => setForm({ ...form, price: e.target.value })}
          required
        />
        <StockLinkFields stockItems={stockItems} state={form} setState={setForm} />
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Ajouter le produit
        </button>
      </form>
    </div>
  );
}

function StockPanel({ stockItems: items, reloadStockItems: load }) {
  const [form, setForm] = useState({ name: "", portions_per_container: "1", quantity_on_hand: "0" });
  const [editing, setEditing] = useState(null);
  const [deltas, setDeltas] = useState({});
  const { busy, error, run } = useAsyncAction();

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createStockItem({
        name: form.name,
        portions_per_container: Number(form.portions_per_container) || 1,
        quantity_on_hand: Number(form.quantity_on_hand) || 0,
      });
      setForm({ name: "", portions_per_container: "1", quantity_on_hand: "0" });
      await load();
    });
  };

  const startEdit = (s) =>
    setEditing({
      id: s.stock_item_id,
      name: s.name,
      portions_per_container: String(s.portions_per_container),
      low_stock_threshold: s.low_stock_threshold === null ? "" : String(s.low_stock_threshold),
    });

  const saveEdit = () =>
    run(async () => {
      await api.updateStockItem(editing.id, {
        name: editing.name,
        portions_per_container: Number(editing.portions_per_container) || 1,
        low_stock_threshold: editing.low_stock_threshold === "" ? null : Number(editing.low_stock_threshold),
      });
      setEditing(null);
      await load();
    });

  const applyRestock = (s) =>
    run(async () => {
      const delta = Number(deltas[s.stock_item_id]);
      if (!delta) return;
      await api.restockItem(s.stock_item_id, delta);
      setDeltas({ ...deltas, [s.stock_item_id]: "" });
      await load();
    });

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Stock</h3>
      <p className="muted">
        Le stock se compte en portions (un verre = 1 portion, une bouteille = plusieurs portions), pas en
        bouteilles, pour que les quantités restent des nombres entiers.
      </p>
      <table>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Portions / contenant</th>
            <th>En stock (portions)</th>
            <th colSpan={2}></th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) =>
            editing?.id === s.stock_item_id ? (
              <tr key={s.stock_item_id}>
                <td>
                  <input
                    value={editing.name}
                    onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="1"
                    value={editing.portions_per_container}
                    onChange={(e) => setEditing({ ...editing, portions_per_container: e.target.value })}
                  />
                </td>
                <td colSpan={3}>
                  <label className="muted">Seuil d'alerte stock bas (optionnel)</label>
                  <input
                    type="number"
                    min="0"
                    value={editing.low_stock_threshold}
                    onChange={(e) => setEditing({ ...editing, low_stock_threshold: e.target.value })}
                  />
                  <div style={{ marginTop: 10 }}>
                    <button onClick={saveEdit} disabled={busy} style={{ marginRight: 6 }}>
                      Enregistrer
                    </button>
                    <button className="secondary" onClick={() => setEditing(null)} disabled={busy}>
                      Annuler
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              <tr
                key={s.stock_item_id}
                style={
                  s.low_stock_threshold !== null && s.quantity_on_hand <= s.low_stock_threshold
                    ? { color: "var(--danger)" }
                    : undefined
                }
              >
                <td>{s.name}</td>
                <td>{s.portions_per_container}</td>
                <td>{s.quantity_on_hand}</td>
                <td>
                  <button className="secondary" onClick={() => startEdit(s)} disabled={busy}>
                    Modifier
                  </button>
                </td>
                <td style={{ display: "flex", gap: 6 }}>
                  <input
                    type="number"
                    placeholder="+/- portions"
                    value={deltas[s.stock_item_id] || ""}
                    onChange={(e) => setDeltas({ ...deltas, [s.stock_item_id]: e.target.value })}
                    style={{ margin: 0, width: 110 }}
                  />
                  <button onClick={() => applyRestock(s)} disabled={busy}>
                    Ajuster
                  </button>
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>

      <h4>Ajouter un article de stock</h4>
      <form onSubmit={handleCreate}>
        <input
          placeholder="Nom (ex. Cabernet Sauvignon)"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <label className="muted">Portions par contenant (1 pour la bière, ex. 5 verres/bouteille pour un vin)</label>
        <input
          type="number"
          min="1"
          value={form.portions_per_container}
          onChange={(e) => setForm({ ...form, portions_per_container: e.target.value })}
        />
        <label className="muted">Stock initial (en portions)</label>
        <input
          type="number"
          min="0"
          value={form.quantity_on_hand}
          onChange={(e) => setForm({ ...form, quantity_on_hand: e.target.value })}
        />
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Ajouter l'article
        </button>
      </form>
    </div>
  );
}

function CustomersPanel() {
  const [customers, setCustomers] = useState([]);
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(null);
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

  const startEdit = (c) => setEditing({ id: c.customer_id, name: c.name });

  const saveEdit = () =>
    run(async () => {
      await api.updateCustomer(editing.id, { name: editing.name });
      setEditing(null);
      await load();
    });

  const handleDelete = (c) => {
    const confirmed = window.confirm(
      `Supprimer ${c.name} ? Ses commandes passées seront conservées mais affichées comme "Client de passage".`
    );
    if (!confirmed) return;
    run(async () => {
      await api.deleteCustomer(c.customer_id);
      await load();
    });
  };

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Clients</h3>
      <ul className="product-list">
        {customers.map((c) =>
          editing?.id === c.customer_id ? (
            <li key={c.customer_id}>
              <input
                value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                style={{ margin: 0, flex: 1, marginRight: 8 }}
              />
              <span>
                <button onClick={saveEdit} disabled={busy} style={{ marginRight: 6 }}>
                  Enregistrer
                </button>
                <button className="secondary" onClick={() => setEditing(null)} disabled={busy}>
                  Annuler
                </button>
              </span>
            </li>
          ) : (
            <li key={c.customer_id}>
              <span>{c.name}</span>
              <span>
                <button
                  className="secondary"
                  onClick={() => startEdit(c)}
                  disabled={busy}
                  style={{ marginRight: 6 }}
                >
                  Modifier
                </button>
                <button className="danger" onClick={() => handleDelete(c)} disabled={busy}>
                  Supprimer
                </button>
              </span>
            </li>
          )
        )}
      </ul>
      <h4>Ajouter un client</h4>
      <form onSubmit={handleCreate}>
        <input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} required />
        <p className="error">{error}</p>
        <button type="submit" disabled={busy}>
          Ajouter le client
        </button>
      </form>
    </div>
  );
}

export default function AdminDashboard() {
  // Shared between StockPanel (which mutates it) and ProductsPanel (which
  // only reads it, to populate the "link this product to a stock item"
  // dropdown) — a single source of truth so a newly created/edited stock
  // item shows up immediately in both places instead of two stale copies.
  const [stockItems, setStockItems] = useState([]);
  const reloadStockItems = () => api.stockItems().then(setStockItems);
  useEffect(() => {
    reloadStockItems();
  }, []);

  return (
    <>
      <TopBar />
      <div className="page">
        <WaitersPanel />
        <StockPanel stockItems={stockItems} reloadStockItems={reloadStockItems} />
        <ProductsPanel stockItems={stockItems} />
        <CustomersPanel />
      </div>
    </>
  );
}
