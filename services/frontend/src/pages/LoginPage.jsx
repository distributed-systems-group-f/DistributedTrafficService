import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { login } from '../api/auth'
import FormCard from '../components/FormCard'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login: authLogin } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await login({ email, password })
      authLogin(res.data.access_token, {
        id: res.data.user_id,
        email,
        role: res.data.role,
      })
      if (res.data.role === 'admin') navigate('/dashboard')
      else if (res.data.role === 'enforcement_agent') navigate('/verify')
      else navigate('/bookings/new')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard title="Sign In">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>
      <p style={{ marginTop: 16, fontSize: '0.9rem', textAlign: 'center' }}>
        No account? <Link to="/register">Register</Link>
      </p>
    </FormCard>
  )
}
