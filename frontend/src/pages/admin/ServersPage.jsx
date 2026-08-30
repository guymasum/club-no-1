import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { roleLabel } from "../../labels.js";
import { useAsyncAction } from "./adminShared.jsx";

export default function ServersPage() {
  const [waiters, setWaiters] = useState([]);
  const [form, setForm] = useState({ name: "", username: "", password: "", role: "waiter" });
  const [resettingId, setResettingId] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const { busy, error, run } = useAsyncAction();

  const load = () => api.waiters().then(setWaiters);
  useEffect(() => {
    load();
  }, []);

  const handleCreate = (e) => {
    e.preventDefault();
    run(async () => {
      await api.createWaiter(form);
      setForm({ name: "", username: "", password: "", role: "waiter" });
      await load();
    });
  };

  const toggleRole = (w) =>
    run(async () => {
      await api.updateWaiter(w.waiter_id, { role: w.role === "admin" ? "waiter" : "admin" });
      await load();
    });

  const toggleActive = (w) =>
    run(async () => {
      await api.updateWaiter(w.waiter_id, { active: !w.active });
      await load();
    });

  const saveNewPassword = () =>
    run(async () => {
      await api.updateWaiter(resettingId, { password: newPassword });
      setResettingId(null);
      setNewPassword("");
    });

  return (
    <div className="page">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Serveurs</h3>
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Nom d'utilisateur</th>
              <th>Rôle</th>
              <th colSpan={3}></th>
            </tr>
          </thead>
          <tbody>
            {waiters.map((w) =>
              resettingId === w.waiter_id ? (
                <tr key={w.waiter_id}>
                  <td>{w.name}</td>
                  <td>{w.username}</td>
                  <td colSpan={4}>
                    <label className="muted">Nouveau mot de passe pour {w.name}</label>
                    <input
                      type="password"
                      minLength={4}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      autoFocus
                    />
                    <div style={{ marginTop: 10 }}>
                      <button onClick={saveNewPassword} disabled={busy || newPassword.length < 4} style={{ marginRight: 6 }}>
                        Enregistrer
                      </button>
                      <button
                        className="secondary"
                        onClick={() => {
                          setResettingId(null);
                          setNewPassword("");
                        }}
                        disabled={busy}
                      >
                        Annuler
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                <tr key={w.waiter_id} style={{ opacity: w.active ? 1 : 0.55 }}>
                  <td>
                    {w.name}
                    {!w.active && <span className="tag">inactif</span>}
                  </td>
                  <td>{w.username}</td>
                  <td>{roleLabel(w.role)}</td>
                  <td>
                    <button className="secondary" onClick={() => toggleRole(w)} disabled={busy}>
                      {w.role === "admin" ? "Rétrograder en serveur" : "Promouvoir en admin"}
                    </button>
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() => {
                        setResettingId(w.waiter_id);
                        setNewPassword("");
                      }}
                      disabled={busy}
                    >
                      Changer le mot de passe
                    </button>
                  </td>
                  <td>
                    <button
                      className={w.active ? "danger" : "secondary"}
                      onClick={() => toggleActive(w)}
                      disabled={busy}
                    >
                      {w.active ? "Retirer" : "Réactiver"}
                    </button>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>

        <h4>Ajouter un serveur</h4>
        <form onSubmit={handleCreate}>
          <input
            placeholder="Nom"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            placeholder="Nom d'utilisateur"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            placeholder="Mot de passe"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="waiter">Serveur</option>
            <option value="admin">Administrateur</option>
          </select>
          <p className="error">{error}</p>
          <button type="submit" disabled={busy}>
            Ajouter le serveur
          </button>
        </form>
      </div>
    </div>
  );
}
