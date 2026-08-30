import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import Login from "./pages/Login.jsx";
import WaiterDashboard from "./pages/WaiterDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import ServersPage from "./pages/admin/ServersPage.jsx";
import ProductsPage from "./pages/admin/ProductsPage.jsx";
import StockPage from "./pages/admin/StockPage.jsx";
import ClientsPage from "./pages/admin/ClientsPage.jsx";
import SuppliersPage from "./pages/admin/SuppliersPage.jsx";
import PurchaseOrdersPage from "./pages/admin/PurchaseOrdersPage.jsx";
import BillView from "./pages/BillView.jsx";
import BillsList from "./pages/BillsList.jsx";
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
        path="/admin/servers"
        element={
          <RequireAuth adminOnly>
            <ServersPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/products"
        element={
          <RequireAuth adminOnly>
            <ProductsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/stock"
        element={
          <RequireAuth adminOnly>
            <StockPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/clients"
        element={
          <RequireAuth adminOnly>
            <ClientsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/suppliers"
        element={
          <RequireAuth adminOnly>
            <SuppliersPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin/purchase-orders"
        element={
          <RequireAuth adminOnly>
            <PurchaseOrdersPage />
          </RequireAuth>
        }
      />
      <Route
        path="/factures"
        element={
          <RequireAuth>
            <BillsList />
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
