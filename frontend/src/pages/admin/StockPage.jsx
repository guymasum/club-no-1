import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAsyncAction } from "./adminShared.jsx";

export default function StockPage() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ name: "", portions_per_container: "1", quantity_on_hand: "0" });
  const [editing, setEditing] = useState(null);
  const [deltas, setDeltas] = useState({});
  const { busy, error, run } = useAsyncAction();

  const load = () => api.stockItems().then(setItems);
  useEffect(() => {
    load();
  }, []);

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
    <div className="page">
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
    </div>
  );
}
