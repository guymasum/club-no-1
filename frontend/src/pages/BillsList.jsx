import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import TopBar from "../components/TopBar.jsx";
import { api } from "../api.js";
import { formatCurrency } from "../format.js";

export default function BillsList() {
  const [bills, setBills] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .bills()
      .then(setBills)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <>
      <TopBar />
      <div className="page">
        <h2>Factures</h2>
        {error && <p className="error">{error}</p>}

        {bills && bills.length === 0 && <p className="muted">Aucune facture pour le moment.</p>}

        {bills && bills.length > 0 && (
          <div className="card">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>N° de transaction</th>
                  <th>Serveur</th>
                  <th>Client</th>
                  <th>Total</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bills.map((bill) => (
                  <tr key={bill.bill_id}>
                    <td>{new Date(bill.generated_at).toLocaleString("fr-BI")}</td>
                    <td>{bill.transaction_id}</td>
                    <td>{bill.waiter_name}</td>
                    <td>{bill.customer_name || "-"}</td>
                    <td>{formatCurrency(bill.total)}</td>
                    <td>
                      <Link to={`/bills/${bill.bill_id}`}>
                        <button className="secondary">Voir / Imprimer</button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
