import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { formatCurrency } from "../../format.js";
import { categoryLabel } from "../../labels.js";
import { PRODUCT_CATEGORIES, StockLinkFields, useAsyncAction } from "./adminShared.jsx";

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [stockItems, setStockItems] = useState([]);
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
    api.stockItems().then(setStockItems);
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
    <div className="page">
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
    </div>
  );
}
