import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { register } from '../api/auth'
import FormCard from '../components/FormCard'

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: '', password: '', role: 'driver', plate_number: '', region: 'EU_WEST_IRELAND',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login: authLogin } = useAuth()
  const navigate = useNavigate()

  function onChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.plate_number) delete payload.plate_number
      const res = await register(payload)
      authLogin(res.data.access_token, {
        id: res.data.user_id,
        email: form.email,
        role: res.data.role,
      })
      navigate('/bookings/new')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard title="Create Account">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Email</label>
          <input name="email" type="email" value={form.email} onChange={onChange} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input name="password" type="password" value={form.password} onChange={onChange} required />
        </div>
        <div className="form-group">
          <label>Role</label>
          <select name="role" value={form.role} onChange={onChange}>
            <option value="driver">Driver</option>
            <option value="enforcement_agent">Enforcement Agent</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        {form.role === 'driver' && (
          <div className="form-group">
            <label>Plate Number</label>
            <input name="plate_number" value={form.plate_number} onChange={onChange} placeholder="e.g. IRL-001" />
          </div>
        )}
        <div className="form-group">
          <label>Region</label>
          <select name="region" value={form.region} onChange={onChange}>
            <option value="EU_WEST_IRELAND">Ireland</option>
            <option value="EU_WEST_UK">UK</option>
            <option value="EU_WEST_FRANCE">France</option>
          </select>
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? 'Creating account...' : 'Register'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>
      <p style={{ marginTop: 16, fontSize: '0.9rem', textAlign: 'center' }}>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </FormCard>
  )
}
