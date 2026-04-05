import { Outlet, Navigate, useLocation } from 'react-router';
import { useAuth } from './contexts/AuthContext';
import { Navbar } from './components/Navbar';

const PUBLIC_ROUTES = ['/signin', '/register'];

function defaultRedirect(role: string): string {
  if (role === 'enforcement') return '/verify';
  if (role === 'admin') return '/dashboard';
  return '/book'; // driver lands on Book first
}

export function Root() {
  const { user } = useAuth();
  const location = useLocation();
  const isPublic = PUBLIC_ROUTES.includes(location.pathname);

  if (!user && !isPublic) return <Navigate to="/signin" replace />;
  if (user && isPublic) return <Navigate to={defaultRedirect(user.role)} replace />;

  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
}
