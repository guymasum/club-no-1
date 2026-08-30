import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import TopBar from "../components/TopBar.jsx";

const SECTIONS = [
  { key: "servers", label: "Serveurs", path: "/admin/servers" },
  { key: "products", label: "Produits", path: "/admin/products" },
  { key: "stock", label: "Stock", path: "/admin/stock" },
  { key: "clients", label: "Clients", path: "/admin/clients" },
  { key: "suppliers", label: "Fournisseurs", path: "/admin/suppliers" },
  { key: "purchase-orders", label: "Commandes fournisseurs", path: "/admin/purchase-orders" },
];

export default function AdminDashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const active = SECTIONS.find((s) => s.key === searchParams.get("section")) || SECTIONS[0];
  const [loading, setLoading] = useState(true);

  const selectSection = (key) => {
    if (key === active.key) return;
    setLoading(true);
    setSearchParams({ section: key });
  };

  return (
    <div className="admin-shell-page">
      <TopBar />
      <div className="admin-shell">
        <nav className="admin-sidebar">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              type="button"
              className={"admin-nav-item" + (s.key === active.key ? " active" : "")}
              onClick={() => selectSection(s.key)}
            >
              {s.label}
            </button>
          ))}
        </nav>
        <div className="admin-iframe-wrap">
          {loading && <div className="admin-loading-overlay">Chargement…</div>}
          <iframe key={active.key} src={active.path} title={active.label} onLoad={() => setLoading(false)} />
        </div>
      </div>
    </div>
  );
}
