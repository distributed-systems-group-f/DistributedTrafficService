import { useState } from 'react'
import { verifyPlate } from '../api/verification'
import FormCard from '../components/FormCard'

export default function VerifyPlatePage() {
  const [plate, setPlate] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const res = await verifyPlate(plate.toUpperCase())
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard title="Verify Plate Number">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Plate Number</label>
          <input
            value={plate}
            onChange={e => setPlate(e.target.value)}
            required
            placeholder="e.g. IRL-001"
            style={{ textTransform: 'uppercase' }}
          />
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? 'Checking...' : 'Verify'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>

      {result && (
        <div style={{
          marginTop: 20, padding: 16, borderRadius: 6,
          background: result.is_authorized ? '#f0fdf4' : '#fef2f2',
          border: `1px solid ${result.is_authorized ? '#86efac' : '#fca5a5'}`
        }}>
          <p style={{ fontSize: '1.1rem', fontWeight: 700, color: result.is_authorized ? '#15803d' : '#b91c1c' }}>
            {result.is_authorized ? 'AUTHORIZED' : 'NOT AUTHORIZED'}
          </p>
          <p style={{ fontSize: '0.85rem', marginTop: 6, color: '#555' }}>{result.message}</p>
          {result.booking_id && (
            <p style={{ fontSize: '0.8rem', marginTop: 4, color: '#666', fontFamily: 'monospace' }}>
              Booking: {result.booking_id}
            </p>
          )}
          <p style={{ fontSize: '0.75rem', marginTop: 6, color: '#94a3b8' }}>
            Checked at {new Date(result.checked_at).toLocaleTimeString()}
          </p>
        </div>
      )}
    </FormCard>
  )
}
