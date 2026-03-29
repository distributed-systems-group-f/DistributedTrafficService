import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { register } from '../api/auth'
import FormCard from '../components/FormCard'

const REGIONS = [
  { value: 'EU_WEST_IRELAND', label: '🇮🇪 Ireland' },
  { value: 'EU_WEST_UK',      label: '🇬🇧 United Kingdom' },
  { value: 'EU_WEST_FRANCE',  label: '🇫🇷 France' },
]

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: '', password: '', role: 'driver', plate_number: '', region: 'EU_WEST_IRELAND',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login: authLogin } = useAuth()
  const navigate = useNavigate()

  function onChange(e) { setForm(f => ({ ...f, [e.target.name]: e.target.value })) }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.plate_number) delete payload.plate_number
      const res = await register(payload)
      authLogin(res.data.access_token, { id: res.data.user_id, email: form.email, role: res.data.role })
      navigate('/bookings/new')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard eyebrow="New account" title="Register" subtitle="Join the distributed traffic system">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email address</label>
          <input name="email" type="email" value={form.email} onChange={onChange}
            placeholder="you@example.com" required autoFocus />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input name="password" type="password" value={form.password} onChange={onChange}
            placeholder="••••••••" required />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Role</label>
            <select name="role" value={form.role} onChange={onChange}>
              <option value="driver">Driver</option>
              <option value="enforcement_agent">Enforcement Agent</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="form-group">
            <label>Home Region</label>
            <select name="region" value={form.region} onChange={onChange}>
              {REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>
        </div>
        {form.role === 'driver' && (
          <div className="form-group">
            <label>Plate Number</label>
            <input name="plate_number" value={form.plate_number} onChange={onChange}
              placeholder="e.g. 241-D-12345" />
          </div>
        )}
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account →'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>
      <p style={{ textAlign: 'center', fontSize: '0.88rem', color: 'var(--ink-muted)', marginTop: 8 }}>
        Already registered?{' '}
        <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Sign in</Link>
      </p>
    </FormCard>
  )
}
