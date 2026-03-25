import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <span className="navbar-brand">Traffic Service</span>
      {user && (
        <div className="navbar-links">
          {(user.role === 'driver') && (
            <>
              <Link to="/bookings/new">Book Journey</Link>
              <Link to="/bookings">My Bookings</Link>
            </>
          )}
          {(user.role === 'enforcement_agent' || user.role === 'admin') && (
            <Link to="/verify">Verify Plate</Link>
          )}
          {user.role === 'admin' && (
            <Link to="/dashboard">Dashboard</Link>
          )}
          <span className="navbar-user">{user.email}</span>
          <button className="btn-link" onClick={handleLogout}>Logout</button>
        </div>
      )}
    </nav>
  )
}
