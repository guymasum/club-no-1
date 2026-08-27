import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import Login from "./pages/Login.jsx";
import WaiterDashboard from "./pages/WaiterDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import BillView from "./pages/BillView.jsx";
import MyAccount from "./pages/MyAccount.jsx";

function RequireAuth({ children, adminOnly = false }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <WaiterDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth adminOnly>
            <AdminDashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/bills/:billId"
        element={
          <RequireAuth>
            <BillView />
          </RequireAuth>
        }
      />
      <Route
        path="/mon-compte"
        element={
          <RequireAuth>
            <MyAccount />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
