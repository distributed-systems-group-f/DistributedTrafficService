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
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard eyebrow="CS7NS6 Distributed Systems" title="Sign in" subtitle="Access the traffic booking system">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email address</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com" autoFocus required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••" required />
        </div>
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in →'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>
      <p style={{ textAlign: 'center', fontSize: '0.88rem', color: 'var(--ink-muted)', marginTop: 8 }}>
        No account?{' '}
        <Link to="/register" style={{ color: 'var(--accent)', fontWeight: 600 }}>Create one</Link>
      </p>
    </FormCard>
  )
}
