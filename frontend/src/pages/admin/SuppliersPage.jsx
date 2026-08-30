import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { useAsyncAction } from "./adminShared.jsx";

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState({ name: "", phone: "" });
  const [editing, setEditing] = useState(null);
  const { busy, error, run } = useAsyncAction();

  const load = () => api.suppliers().then(setSuppliers);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createSupplier({ name: form.name, phone: form.phone || null });
      setForm({ name: "", phone: "" });
      await load();
    });
  };

  const startEdit = (s) => setEditing({ id: s.supplier_id, name: s.name, phone: s.phone || "" });

  const saveEdit = () =>
    run(async () => {
      await api.updateSupplier(editing.id, { name: editing.name, phone: editing.phone || null });
      setEditing(null);
      await load();
    });

  const toggleActive = (s) =>
    run(async () => {
      await api.updateSupplier(s.supplier_id, { active: !s.active });
      await load();
    });

  return (
    <div className="page">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Fournisseurs</h3>
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Téléphone</th>
              <th colSpan={2}></th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((s) =>
              editing?.id === s.supplier_id ? (
                <tr key={s.supplier_id}>
                  <td>
                    <input
                      value={editing.name}
                      onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                    />
                  </td>
                  <td colSpan={3}>
                    <input
                      placeholder="Téléphone (optionnel)"
                      value={editing.phone}
                      onChange={(e) => setEditing({ ...editing, phone: e.target.value })}
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
                <tr key={s.supplier_id} style={{ opacity: s.active ? 1 : 0.55 }}>
                  <td>
                    {s.name}
                    {!s.active && <span className="tag">inactif</span>}
                  </td>
                  <td>{s.phone || "-"}</td>
                  <td>
                    <button className="secondary" onClick={() => startEdit(s)} disabled={busy}>
                      Modifier
                    </button>
                  </td>
                  <td>
                    <button
                      className={s.active ? "danger" : "secondary"}
                      onClick={() => toggleActive(s)}
                      disabled={busy}
                    >
                      {s.active ? "Désactiver" : "Réactiver"}
                    </button>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>

        <h4>Ajouter un fournisseur</h4>
        <form onSubmit={handleCreate}>
          <input
            placeholder="Nom"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="Téléphone (optionnel)"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <p className="error">{error}</p>
          <button type="submit" disabled={busy}>
            Ajouter le fournisseur
          </button>
        </form>
      </div>
    </div>
  );
}
