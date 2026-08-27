import { useState } from "react";
import TopBar from "../components/TopBar.jsx";
import { api, ApiError } from "../api.js";

export default function MyAccount() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError("Les deux mots de passe ne correspondent pas");
      return;
    }

    setBusy(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      setSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <TopBar />
      <div className="page">
        <div className="card" style={{ maxWidth: 360 }}>
          <h2 style={{ marginTop: 0 }}>Mon compte</h2>
          <h3>Changer mon mot de passe</h3>
          <form onSubmit={handleSubmit}>
            <label className="muted">Mot de passe actuel</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <label className="muted">Nouveau mot de passe</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={4}
              required
            />
            <label className="muted">Confirmer le nouveau mot de passe</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              minLength={4}
              required
            />
            <p className="error">{error}</p>
            {success && <p style={{ color: "var(--ok)", fontSize: "0.9rem" }}>Mot de passe mis à jour.</p>}
            <button type="submit" disabled={busy} style={{ width: "100%" }}>
              Enregistrer
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
