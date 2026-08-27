import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar.jsx";
import { api, ApiError } from "../api.js";

export default function WaiterDashboard() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [activeOrderId, setActiveOrderId] = useState(null);
  const [newCustomerId, setNewCustomerId] = useState("");
  const [selectedProductId, setSelectedProductId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const activeOrder = orders.find((o) => o.order_id === activeOrderId) || null;

  const refreshOrders = async () => {
    const data = await api.openOrders();
    setOrders(data);
    return data;
  };

  useEffect(() => {
    (async () => {
      try {
        const [ordersData, productsData, customersData] = await Promise.all([
          api.openOrders(),
          api.products(),
          api.customers(),
        ]);
        setOrders(ordersData);
        setProducts(productsData);
        setCustomers(customersData);
        if (ordersData.length > 0) setActiveOrderId(ordersData[0].order_id);
        if (productsData.length > 0) setSelectedProductId(String(productsData[0].product_id));
      } catch (err) {
        setError(err.message);
      }
    })();
  }, []);

  const withBusy = (fn) => async (...args) => {
    setError("");
    setBusy(true);
    try {
      await fn(...args);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const handleNewOrder = withBusy(async () => {
    const order = await api.createOrder(newCustomerId ? Number(newCustomerId) : null);
    await refreshOrders();
    setActiveOrderId(order.order_id);
    setNewCustomerId("");
  });

  const handleAddItem = withBusy(async () => {
    if (!activeOrder || !selectedProductId) return;
    await api.addItem(activeOrder.order_id, Number(selectedProductId), Number(quantity) || 1);
    await refreshOrders();
    setQuantity(1);
  });

  const handleRemoveItem = withBusy(async (itemId) => {
    await api.removeItem(activeOrder.order_id, itemId);
    await refreshOrders();
  });

  const handleFinalize = withBusy(async () => {
    const bill = await api.finalizeOrder(activeOrder.order_id);
    const remaining = await refreshOrders();
    setActiveOrderId(remaining[0]?.order_id ?? null);
    navigate(`/bills/${bill.bill_id}`);
  });

  const total = activeOrder
    ? activeOrder.items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0)
    : 0;

  return (
    <>
      <TopBar />
      <div className="page">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>New order</h2>
          <div className="grid-2" style={{ alignItems: "end" }}>
            <div>
              <label className="muted">Customer (optional)</label>
              <select value={newCustomerId} onChange={(e) => setNewCustomerId(e.target.value)}>
                <option value="">Walk-in / not specified</option>
                {customers.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <button onClick={handleNewOrder} disabled={busy} style={{ marginBottom: 14 }}>
                Start order
              </button>
            </div>
          </div>
        </div>

        {orders.length > 0 && (
          <div className="orders-strip">
            {orders.map((o) => (
              <button
                key={o.order_id}
                className={`order-chip ${o.order_id === activeOrderId ? "active" : ""}`}
                onClick={() => setActiveOrderId(o.order_id)}
              >
                #{o.order_id} · {o.customer_name || "Walk-in"}
              </button>
            ))}
          </div>
        )}

        <p className="error">{error}</p>

        {activeOrder ? (
          <div className="grid-2">
            <div className="card">
              <h3 style={{ marginTop: 0 }}>Order #{activeOrder.order_id}</h3>
              <p className="muted">
                Waiter: {activeOrder.waiter_name} · Customer: {activeOrder.customer_name || "Walk-in"}
              </p>
              <ul className="order-list">
                {activeOrder.items.length === 0 && <li className="muted">No items yet</li>}
                {activeOrder.items.map((item) => (
                  <li key={item.item_id}>
                    <span>
                      {item.quantity}x {item.product_name}
                    </span>
                    <span>
                      ${(item.quantity * item.unit_price).toFixed(2)}{" "}
                      <button
                        className="secondary"
                        style={{ padding: "2px 8px", marginLeft: 8 }}
                        onClick={() => handleRemoveItem(item.item_id)}
                        disabled={busy}
                      >
                        ✕
                      </button>
                    </span>
                  </li>
                ))}
              </ul>
              <div className="total-row">
                <span>TOTAL</span>
                <span>${total.toFixed(2)}</span>
              </div>
              <button
                style={{ width: "100%", marginTop: 14 }}
                onClick={handleFinalize}
                disabled={busy || activeOrder.items.length === 0}
              >
                Finalize & print bill
              </button>
            </div>

            <div className="card">
              <h3 style={{ marginTop: 0 }}>Add item</h3>
              <label className="muted">Product</label>
              <select value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
                {products.map((p) => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.name} — ${p.price.toFixed(2)} ({p.category})
                  </option>
                ))}
              </select>
              <label className="muted">Quantity</label>
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
              <button style={{ width: "100%" }} onClick={handleAddItem} disabled={busy}>
                Add to order
              </button>

              <h4>Menu</h4>
              <ul className="product-list">
                {products.map((p) => (
                  <li key={p.product_id}>
                    <span>
                      {p.name}
                      <span className="tag">{p.category}</span>
                    </span>
                    <span>${p.price.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="card muted">No open orders. Start one above.</div>
        )}
      </div>
    </>
  );
}
