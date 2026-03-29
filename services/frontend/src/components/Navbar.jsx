import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <span className="navbar-brand">RoutePass</span>
      {user && (
        <div className="navbar-links">
          {user.role === 'driver' && (
            <>
              <Link to="/bookings/new" className={pathname === '/bookings/new' ? 'active' : ''}>Book</Link>
              <Link to="/bookings" className={pathname === '/bookings' ? 'active' : ''}>My Journeys</Link>
            </>
          )}
          {(user.role === 'enforcement_agent' || user.role === 'admin') && (
            <Link to="/verify" className={pathname === '/verify' ? 'active' : ''}>Verify</Link>
          )}
          {user.role === 'admin' && (
            <Link to="/dashboard" className={pathname === '/dashboard' ? 'active' : ''}>Dashboard</Link>
          )}
          <div className="navbar-sep" />
          <span className="navbar-user">{user.email}</span>
          <button className="btn-link" onClick={handleLogout}>Logout</button>
        </div>
      )}
    </nav>
  )
}
