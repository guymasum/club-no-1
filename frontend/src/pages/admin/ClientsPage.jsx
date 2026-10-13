import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAsyncAction } from "./adminShared.jsx";

const EMPTY_FORM = { name: "", email: "", phone: "" };

// Blank email/phone must be sent as null, not "" — the backend treats ""
// as "please validate this as a value" and rejects it, while null means
// "no contact info on file".
function toPayload(form) {
  return {
    name: form.name,
    email: form.email.trim() ? form.email.trim() : null,
    phone: form.phone.trim() ? form.phone.trim() : null,
  };
}

export default function ClientsPage() {
  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState(null);
  const { busy, error, run } = useAsyncAction();

  const load = () => api.customers().then(setCustomers);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createCustomer(toPayload(form));
      setForm(EMPTY_FORM);
      await load();
    });
  };

  const startEdit = (c) =>
    setEditing({ id: c.customer_id, name: c.name, email: c.email || "", phone: c.phone || "" });

  const saveEdit = () =>
    run(async () => {
      await api.updateCustomer(editing.id, toPayload(editing));
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
    <div className="page">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Clients</h3>
        <ul className="product-list">
          {customers.map((c) =>
            editing?.id === c.customer_id ? (
              <li key={c.customer_id} style={{ flexDirection: "column", alignItems: "stretch" }}>
                <input
                  placeholder="Nom"
                  value={editing.name}
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                  style={{ marginBottom: 6 }}
                />
                <input
                  placeholder="E-mail"
                  type="email"
                  value={editing.email}
                  onChange={(e) => setEditing({ ...editing, email: e.target.value })}
                  style={{ marginBottom: 6 }}
                />
                <input
                  placeholder="Téléphone (ex: +25779123456)"
                  value={editing.phone}
                  onChange={(e) => setEditing({ ...editing, phone: e.target.value })}
                  style={{ marginBottom: 6 }}
                />
                <p className="error">{error}</p>
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
                <span>
                  {c.name}
                  <br />
                  <span className="muted">{c.email || "—"} · {c.phone || "—"}</span>
                </span>
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
          <input
            placeholder="Nom"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="E-mail (optionnel)"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            placeholder="Téléphone (optionnel, ex: +25779123456)"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <p className="error">{error}</p>
          <button type="submit" disabled={busy}>
            Ajouter le client
          </button>
        </form>
      </div>
    </div>
  );
}
