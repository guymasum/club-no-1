import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import TopBar from "../components/TopBar.jsx";
import { api } from "../api.js";

export default function BillView() {
  const { billId } = useParams();
  const [bill, setBill] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .bill(billId)
      .then(setBill)
      .catch((err) => setError(err.message));
  }, [billId]);

  return (
    <>
      <TopBar />
      <div className="page">
        <div className="no-print" style={{ marginBottom: 16, display: "flex", gap: 10 }}>
          <Link to="/">
            <button className="secondary">← Back to orders</button>
          </Link>
          {bill && (
            <>
              <button onClick={() => window.print()}>Print</button>
              <a href={api.billPdfUrl(bill.bill_id)} target="_blank" rel="noreferrer">
                <button className="secondary">Download PDF</button>
              </a>
            </>
          )}
        </div>

        {error && <p className="error">{error}</p>}

        {bill && (
          <div className="receipt">
            <p className="center">=============================</p>
            <p className="center">
              <strong>CLUB NO. 1</strong>
            </p>
            <p className="center">=============================</p>
            <p>Date: {new Date(bill.generated_at).toISOString().slice(0, 10)}</p>
            <p>Transaction ID: {bill.transaction_id}</p>
            <p>Waiter: {bill.waiter_name}</p>
            <p>Customer: {bill.customer_name || "-"}</p>
            <hr />
            {bill.items.map((item) => (
              <p className="line" key={item.item_id}>
                <span>
                  {item.quantity}x {item.product_name}
                </span>
                <span>${(item.quantity * item.unit_price).toFixed(2)}</span>
              </p>
            ))}
            <hr />
            <p className="line">
              <strong>TOTAL:</strong>
              <strong>${bill.total.toFixed(2)}</strong>
            </p>
            <p className="center">=============================</p>
            <p className="center">Merci et à bientôt!</p>
            <p className="center">=============================</p>
          </div>
        )}
      </div>
    </>
  );
}
