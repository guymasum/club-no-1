import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import TopBar from "../components/TopBar.jsx";
import { api } from "../api.js";
import { formatCurrency } from "../format.js";

export default function BillView() {
  const { billId } = useParams();
  const [bill, setBill] = useState(null);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    api
      .bill(billId)
      .then(setBill)
      .catch((err) => setError(err.message));
  }, [billId]);

  const handleDownload = async () => {
    setDownloading(true);
    setError("");
    try {
      const blob = await api.billPdf(bill.bill_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `facture-${bill.transaction_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Le téléchargement du PDF a échoué");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      <TopBar />
      <div className="page">
        <div className="no-print" style={{ marginBottom: 16, display: "flex", gap: 10 }}>
          <Link to="/">
            <button className="secondary">← Retour aux commandes</button>
          </Link>
          {bill && (
            <>
              <button onClick={() => window.print()}>Imprimer</button>
              <button className="secondary" onClick={handleDownload} disabled={downloading}>
                {downloading ? "Téléchargement..." : "Télécharger le PDF"}
              </button>
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
            <p>Date : {new Date(bill.generated_at).toISOString().slice(0, 10)}</p>
            <p>N° de transaction : {bill.transaction_id}</p>
            <p>Serveur : {bill.waiter_name}</p>
            <p>Client : {bill.customer_name || "-"}</p>
            <hr />
            {bill.items.map((item) => (
              <p className="line" key={item.item_id}>
                <span>
                  {item.quantity}x {item.product_name}
                </span>
                <span>{formatCurrency(item.quantity * item.unit_price)}</span>
              </p>
            ))}
            <hr />
            <p className="line">
              <strong>TOTAL :</strong>
              <strong>{formatCurrency(bill.total)}</strong>
            </p>
            <p className="center">=============================</p>
            <p className="center">Merci et à bientôt !</p>
            <p className="center">=============================</p>
          </div>
        )}
      </div>
    </>
  );
}
