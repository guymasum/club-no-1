import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { todayIso, useAsyncAction } from "./adminShared.jsx";

export default function PurchaseOrdersPage() {
  const emptyForm = () => ({
    supplier_id: "",
    invoice_number: "",
    order_date: todayIso(),
    items: [{ stock_item_id: "", quantity_received: "" }],
  });
  const [suppliers, setSuppliers] = useState([]);
  const [stockItems, setStockItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [filterSupplierId, setFilterSupplierId] = useState("");
  const [orders, setOrders] = useState([]);
  const { busy, error, run } = useAsyncAction();

  const loadOrders = () => api.purchaseOrders(filterSupplierId || undefined).then(setOrders);
  const loadStockItems = () => api.stockItems().then(setStockItems);

  useEffect(() => {
    api.suppliers().then(setSuppliers);
    loadStockItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterSupplierId]);

  const setItem = (index, patch) =>
    setForm({
      ...form,
      items: form.items.map((it, i) => (i === index ? { ...it, ...patch } : it)),
    });

  const addItemRow = () =>
    setForm({ ...form, items: [...form.items, { stock_item_id: "", quantity_received: "" }] });

  const removeItemRow = (index) =>
    setForm({ ...form, items: form.items.filter((_, i) => i !== index) });

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      const items = form.items
        .filter((it) => it.stock_item_id && Number(it.quantity_received) > 0)
        .map((it) => ({
          stock_item_id: Number(it.stock_item_id),
          quantity_received: Number(it.quantity_received),
        }));
      if (items.length === 0) {
        throw new Error("Ajoutez au moins un article avec une quantité");
      }
      await api.createPurchaseOrder({
        supplier_id: Number(form.supplier_id),
        invoice_number: form.invoice_number,
        order_date: form.order_date,
        items,
      });
      setForm(emptyForm());
      await Promise.all([loadOrders(), loadStockItems()]);
    });
  };

  return (
    <div className="page">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Commandes fournisseurs</h3>
        <p className="muted">
          Enregistrer une livraison ajoute directement la quantité reçue (en portions) au stock de chaque
          article.
        </p>

        <label className="muted">Filtrer par fournisseur</label>
        <select value={filterSupplierId} onChange={(e) => setFilterSupplierId(e.target.value)}>
          <option value="">Tous les fournisseurs</option>
          {suppliers.map((s) => (
            <option key={s.supplier_id} value={s.supplier_id}>
              {s.name}
            </option>
          ))}
        </select>

        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Fournisseur</th>
              <th>N° de facture</th>
              <th>Articles reçus</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((po) => (
              <tr key={po.purchase_order_id}>
                <td>{po.order_date}</td>
                <td>{po.supplier_name}</td>
                <td>{po.invoice_number}</td>
                <td>
                  {po.items.map((it) => `${it.quantity_received}x ${it.stock_item_name}`).join(", ")}
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  Aucune commande enregistrée.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <h4>Enregistrer une livraison</h4>
        <form onSubmit={handleCreate}>
          <select
            value={form.supplier_id}
            onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
            required
          >
            <option value="" disabled>
              Fournisseur
            </option>
            {suppliers
              .filter((s) => s.active)
              .map((s) => (
                <option key={s.supplier_id} value={s.supplier_id}>
                  {s.name}
                </option>
              ))}
          </select>
          <input
            placeholder="N° de facture"
            value={form.invoice_number}
            onChange={(e) => setForm({ ...form, invoice_number: e.target.value })}
            required
          />
          <label className="muted">Date</label>
          <input
            type="date"
            value={form.order_date}
            onChange={(e) => setForm({ ...form, order_date: e.target.value })}
            required
          />

          <label className="muted">Articles reçus</label>
          {form.items.map((item, index) => (
            <div key={index} style={{ display: "flex", gap: 6, marginBottom: 6 }}>
              <select
                value={item.stock_item_id}
                onChange={(e) => setItem(index, { stock_item_id: e.target.value })}
                style={{ flex: 2 }}
              >
                <option value="" disabled>
                  Article de stock
                </option>
                {stockItems.map((s) => (
                  <option key={s.stock_item_id} value={s.stock_item_id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                placeholder="Quantité (portions)"
                value={item.quantity_received}
                onChange={(e) => setItem(index, { quantity_received: e.target.value })}
                style={{ flex: 1, margin: 0 }}
              />
              {form.items.length > 1 && (
                <button type="button" className="secondary" onClick={() => removeItemRow(index)}>
                  Retirer
                </button>
              )}
            </div>
          ))}
          <button type="button" className="secondary" onClick={addItemRow} style={{ marginBottom: 14 }}>
            + Ajouter un article
          </button>

          <p className="error">{error}</p>
          <button type="submit" disabled={busy}>
            Enregistrer la livraison
          </button>
        </form>
      </div>
    </div>
  );
}
