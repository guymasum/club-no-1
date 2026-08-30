import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAsyncAction } from "./adminShared.jsx";

export default function ClientsPage() {
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
    <div className="page">
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
    </div>
  );
}
