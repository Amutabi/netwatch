import { Navigate, Outlet } from 'react-router-dom';
import { getToken } from '../api';
import Layout from '../components/Layout';

export default function ProtectedRoute() {
  if (!getToken()) return <Navigate to="/auth" replace />;
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}
