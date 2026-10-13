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
  const [sendingEmail, setSendingEmail] = useState(false);

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

  // The send-email endpoint only queues the send (FastAPI BackgroundTask) —
  // it returns "pending" immediately, before the email has actually gone
  // out. Poll briefly afterwards so the button's status catches up to
  // "sent"/"failed" without the waiter having to manually refresh the page.
  const pollUntilSettled = async (billId, attemptsLeft = 6) => {
    if (attemptsLeft <= 0) return;
    await new Promise((resolve) => setTimeout(resolve, 2000));
    const fresh = await api.bill(billId);
    setBill(fresh);
    if (fresh.email_status === "pending") {
      await pollUntilSettled(billId, attemptsLeft - 1);
    }
  };

  const handleSendEmail = async () => {
    setSendingEmail(true);
    setError("");
    try {
      await api.sendBillEmail(bill.bill_id);
      setBill({ ...bill, email_status: "pending" });
      await pollUntilSettled(bill.bill_id);
    } catch (err) {
      setError(err.message || "L'envoi de l'e-mail a échoué");
    } finally {
      setSendingEmail(false);
    }
  };

  const emailStatusLabel = {
    sent: "E-mail envoyé ✓",
    pending: "Envoi en cours…",
    failed: `Échec de l'envoi${bill?.email_error ? ` : ${bill.email_error}` : ""}`,
  }[bill?.email_status];

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
              <button
                className="secondary"
                onClick={handleSendEmail}
                disabled={sendingEmail || bill.email_status === "pending" || !bill.customer_email}
                title={!bill.customer_email ? "Ce client n'a pas d'adresse e-mail enregistrée" : undefined}
              >
                {bill.email_status === "pending" ? "Envoi en cours..." : "Envoyer par e-mail"}
              </button>
            </>
          )}
        </div>

        {bill && emailStatusLabel && (
          <p className={"no-print " + (bill.email_status === "failed" ? "error" : "muted")}>
            {emailStatusLabel}
          </p>
        )}

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
