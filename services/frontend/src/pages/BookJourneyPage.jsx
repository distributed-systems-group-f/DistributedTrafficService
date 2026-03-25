import { useState } from 'react'
import { createBooking } from '../api/bookings'
import FormCard from '../components/FormCard'

const PRESETS = [
  { label: 'Dublin → Cork', olat: 53.3498, olng: -6.2603, dlat: 51.8985, dlng: -8.4756 },
  { label: 'Dublin → Birmingham (Cross-region)', olat: 53.3498, olng: -6.2603, dlat: 52.4862, dlng: -1.8904 },
  { label: 'Paris → Lyon', olat: 48.8566, olng: 2.3522, dlat: 45.7640, dlng: 4.8357 },
  { label: 'London → Manchester', olat: 51.5074, olng: -0.1278, dlat: 53.4808, dlng: -2.2426 },
]

function defaultDeparture() {
  const d = new Date(Date.now() + 3600 * 1000)
  return d.toISOString().slice(0, 16)
}

export default function BookJourneyPage() {
  const [form, setForm] = useState({
    origin_lat: '', origin_lng: '', destination_lat: '', destination_lng: '',
    departure_time: defaultDeparture(), plate_number: '',
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function onChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function applyPreset(p) {
    setForm(f => ({ ...f, origin_lat: p.olat, origin_lng: p.olng, destination_lat: p.dlat, destination_lng: p.dlng }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const payload = {
        origin_lat: parseFloat(form.origin_lat),
        origin_lng: parseFloat(form.origin_lng),
        destination_lat: parseFloat(form.destination_lat),
        destination_lng: parseFloat(form.destination_lng),
        departure_time: new Date(form.departure_time).toISOString(),
        plate_number: form.plate_number || undefined,
      }
      const res = await createBooking(payload)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Booking failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormCard title="Book a Journey">
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: '0.8rem', color: '#666', marginBottom: 8 }}>Quick presets:</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {PRESETS.map(p => (
            <button key={p.label} type="button" onClick={() => applyPreset(p)}
              style={{ fontSize: '0.75rem', padding: '4px 10px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 4, color: '#1d4ed8' }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div className="form-group">
            <label>Origin Lat</label>
            <input name="origin_lat" value={form.origin_lat} onChange={onChange} required placeholder="53.3498" />
          </div>
          <div className="form-group">
            <label>Origin Lng</label>
            <input name="origin_lng" value={form.origin_lng} onChange={onChange} required placeholder="-6.2603" />
          </div>
          <div className="form-group">
            <label>Dest Lat</label>
            <input name="destination_lat" value={form.destination_lat} onChange={onChange} required placeholder="51.8985" />
          </div>
          <div className="form-group">
            <label>Dest Lng</label>
            <input name="destination_lng" value={form.destination_lng} onChange={onChange} required placeholder="-8.4756" />
          </div>
        </div>
        <div className="form-group">
          <label>Departure Time</label>
          <input name="departure_time" type="datetime-local" value={form.departure_time} onChange={onChange} required />
        </div>
        <div className="form-group">
          <label>Plate Number (optional)</label>
          <input name="plate_number" value={form.plate_number} onChange={onChange} placeholder="IRL-001" />
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? 'Booking...' : 'Book Journey'}
        </button>
        {error && <p className="error-msg">{error}</p>}
      </form>
      {result && (
        <div style={{ marginTop: 20, padding: 16, background: result.status === 'CONFIRMED' ? '#f0fdf4' : '#fef2f2', borderRadius: 6, border: `1px solid ${result.status === 'CONFIRMED' ? '#86efac' : '#fca5a5'}` }}>
          <p style={{ fontWeight: 600, color: result.status === 'CONFIRMED' ? '#16a34a' : '#dc2626' }}>
            {result.status}
          </p>
          <p style={{ fontSize: '0.85rem', marginTop: 4, color: '#555' }}>Booking ID: {result.booking_id}</p>
          {result.estimated_duration_minutes && (
            <p style={{ fontSize: '0.85rem', color: '#555' }}>Duration: ~{result.estimated_duration_minutes} min</p>
          )}
        </div>
      )}
    </FormCard>
  )
}
