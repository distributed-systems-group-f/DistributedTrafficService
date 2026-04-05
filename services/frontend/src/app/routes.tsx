import { createBrowserRouter, Navigate } from 'react-router';
import type { ReactNode } from 'react';
import { SignIn }      from './pages/SignIn';
import { Register }    from './pages/Register';
import { BookJourney } from './pages/BookJourney';
import { MyJourneys }  from './pages/MyJourneys';
import { VerifyPlate } from './pages/VerifyPlate';
import { Dashboard }   from './pages/Dashboard';
import { Notifications } from './pages/Notifications';
import { Root }        from './Root';
import { useAuth, type UserRole } from './contexts/AuthContext';

function defaultRedirect(role: UserRole): string {
  if (role === 'enforcement') return '/verify';
  if (role === 'admin') return '/dashboard';
  return '/book';
}

function RoleGuard({ roles, children }: { roles: UserRole[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/signin" replace />;
  if (!roles.includes(user.role)) {
    return <Navigate to={defaultRedirect(user.role)} replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Root />,
    children: [
      { index: true,       element: <Navigate to="/signin" replace /> },
      { path: 'signin',    element: <SignIn /> },
      { path: 'register',  element: <Register /> },
      {
        path: 'book',
        element: (
          <RoleGuard roles={['driver', 'admin']}>
            <BookJourney />
          </RoleGuard>
        ),
      },
      {
        path: 'journeys',
        element: (
          <RoleGuard roles={['driver', 'admin']}>
            <MyJourneys />
          </RoleGuard>
        ),
      },
      {
        path: 'verify',
        element: (
          <RoleGuard roles={['enforcement', 'admin']}>
            <VerifyPlate />
          </RoleGuard>
        ),
      },
      {
        path: 'dashboard',
        element: (
          <RoleGuard roles={['admin']}>
            <Dashboard />
          </RoleGuard>
        ),
      },
      {
        path: 'notifications',
        element: (
          <RoleGuard roles={['driver', 'enforcement', 'admin']}>
            <Notifications />
          </RoleGuard>
        ),
      },
    ],
  },
]);
