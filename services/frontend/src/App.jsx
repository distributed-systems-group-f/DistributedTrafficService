import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import BookJourneyPage from './pages/BookJourneyPage'
import MyBookingsPage from './pages/MyBookingsPage'
import VerifyPlatePage from './pages/VerifyPlatePage'
import DashboardPage from './pages/DashboardPage'

function PrivateRoute({ children, roles }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/bookings/new" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/bookings/new" element={
            <PrivateRoute><BookJourneyPage /></PrivateRoute>
          } />
          <Route path="/bookings" element={
            <PrivateRoute><MyBookingsPage /></PrivateRoute>
          } />
          <Route path="/verify" element={
            <PrivateRoute roles={['enforcement_agent', 'admin']}><VerifyPlatePage /></PrivateRoute>
          } />
          <Route path="/dashboard" element={
            <PrivateRoute roles={['admin']}><DashboardPage /></PrivateRoute>
          } />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
