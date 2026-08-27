import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

export default function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="topbar">
      <h1>CLUB NO. 1</h1>
      <nav>
        <span className="muted">{user?.name}</span>
        <NavLink to="/" end>
          Commandes
        </NavLink>
        {user?.role === "admin" && <NavLink to="/admin">Administration</NavLink>}
        <NavLink to="/mon-compte">Mon compte</NavLink>
        <button className="linklike" onClick={handleLogout}>
          Déconnexion
        </button>
      </nav>
    </div>
  );
}
