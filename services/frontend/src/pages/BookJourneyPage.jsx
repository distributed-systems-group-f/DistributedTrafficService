import { useState } from 'react'
import { Link } from 'react-router-dom'
import { createBooking } from '../api/bookings'
import FormCard from '../components/FormCard'
import './BookJourneyPage.css'

// Coordinate presets that exercise all three region schemas in the DB
const PRESETS = [
  { label: 'Dublin → Cork',          flag: '🇮🇪', olat: 53.3498, olng: -6.2603, dlat: 51.8985, dlng: -8.4756, note: 'Single region' },
  { label: 'Dublin → Birmingham',    flag: '🌍', olat: 53.3498, olng: -6.2603, dlat: 52.4862, dlng: -1.8904, note: 'Cross-region: IE → UK' },
  { label: 'London → Manchester',    flag: '🇬🇧', olat: 51.5074, olng: -0.1278, dlat: 53.4808, dlng: -2.2426, note: 'Single region' },
  { label: 'Paris → Lyon',           flag: '🇫🇷', olat: 48.8566, olng: 2.3522,  dlat: 45.7640, dlng: 4.8357,  note: 'Single region' },
  { label: 'London → Paris',         flag: '🌍', olat: 51.5074, olng: -0.1278, dlat: 48.8566, dlng: 2.3522,  note: 'Cross-region: UK → FR' },
  { label: 'Cork → Paris',           flag: '🌍', olat: 51.8985, olng: -8.4756, dlat: 48.8566, dlng: 2.3522,  note: 'Cross-region: IE → FR' },
]

function defaultDeparture() {
  const d = new Date(Date.now() + 3600 * 1000)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`
}

function RegionBadge({ lat, lng }) {
  if (!lat || !lng) return null
  const fLat = parseFloat(lat), fLng = parseFloat(lng)
  let region = null
  if (51.0 <= fLat && fLat <= 55.5 && -10.5 <= fLng && fLng <= -6.0) region = { label: 'Ireland', color: '#00c26f' }
  else if (49.9 <= fLat && fLat <= 58.7 && -5.7 <= fLng && fLng <= 1.8) region = { label: 'UK', color: '#2563eb' }
  else if (!isNaN(fLat) && !isNaN(fLng)) region = { label: 'France', color: '#7c3aed' }
  if (!region) return null
  return (
    <span style={{
      fontSize: '0.68rem', fontWeight: 700, letterSpacing: '.06em',
      textTransform: 'uppercase', color: region.color, background: region.color + '18',
      padding: '2px 7px', borderRadius: 4, fontFamily: 'var(--font-display)',
    }}>{region.label}</span>
  )
}

function StatusCard({ result }) {
  const ok = result.status === 'CONFIRMED'
  return (
    <div className={`booking-result ${ok ? 'booking-result--ok' : 'booking-result--fail'}`}>
      <div className="booking-result-header">
        <span className="booking-result-icon">{ok ? '✓' : '✕'}</span>
        <span className="booking-result-status">{result.status}</span>
      </div>
      <div className="booking-result-body">
        <div className="booking-result-row">
          <span>Booking ID</span>
          <code>{result.booking_id}</code>
        </div>
        {result.estimated_duration_minutes && (
          <div className="booking-result-row">
            <span>Est. duration</span>
            <code>{result.estimated_duration_minutes} min</code>
          </div>
        )}
        {result.segments?.length > 0 && (
          <div className="booking-result-row">
            <span>Regions</span>
            <code>{result.segments.map(s => s.region || s).join(', ')}</code>
          </div>
        )}
      </div>
      {ok && (
        <p style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: 10 }}>
          Your journey is confirmed. You may depart at the scheduled time.{' '}
          <Link to="/bookings">View all journeys →</Link>
        </p>
      )}
    </div>
  )
}

export default function BookJourneyPage() {
  const [form, setForm] = useState({
    origin_lat: '', origin_lng: '',
    destination_lat: '', destination_lng: '',
    departure_time: defaultDeparture(),
    plate_number: '',
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [activePreset, setActivePreset] = useState(null)

  function onChange(e) { setForm(f => ({ ...f, [e.target.name]: e.target.value })) }

  function applyPreset(p, idx) {
    setForm(f => ({ ...f, origin_lat: p.olat, origin_lng: p.olng, destination_lat: p.dlat, destination_lng: p.dlng }))
    setActivePreset(idx)
    setResult(null)
    setError('')
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
        ...(form.plate_number ? { plate_number: form.plate_number.toUpperCase() } : {}),
      }
      const res = await createBooking(payload)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Booking request failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isMultiRegion = (() => {
    const getRegion = (lat, lng) => {
      const fLat = parseFloat(lat), fLng = parseFloat(lng)
      if (isNaN(fLat) || isNaN(fLng)) return null
      if (51.0 <= fLat && fLat <= 55.5 && -10.5 <= fLng && fLng <= -6.0) return 'IE'
      if (49.9 <= fLat && fLat <= 58.7 && -5.7 <= fLng && fLng <= 1.8) return 'UK'
      return 'FR'
    }
    const o = getRegion(form.origin_lat, form.origin_lng)
    const d = getRegion(form.destination_lat, form.destination_lng)
    return o && d && o !== d
  })()

  return (
    <div className="book-page">
      <FormCard eyebrow="Journey booking" title="Book a journey" maxWidth={560}>
        {/* Presets */}
        <div className="preset-grid">
          {PRESETS.map((p, i) => (
            <button key={i} type="button"
              className={`preset-btn ${activePreset === i ? 'preset-btn--active' : ''}`}
              onClick={() => applyPreset(p, i)}>
              <span className="preset-flag">{p.flag}</span>
              <span className="preset-label">{p.label}</span>
              <span className="preset-note">{p.note}</span>
            </button>
          ))}
        </div>

        {isMultiRegion && (
          <div className="saga-notice">
            <span>⚡</span>
            <div>
              <strong>Cross-region journey detected</strong>
              <p>This booking spans multiple regional schemas. The SAGA pattern will acquire distributed locks and reserve capacity in each region atomically.</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Origin */}
          <div className="coords-section">
            <div className="coords-label">
              <span className="coords-dot coords-dot--origin" />
              Origin
              <RegionBadge lat={form.origin_lat} lng={form.origin_lng} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Latitude</label>
                <input name="origin_lat" value={form.origin_lat} onChange={onChange}
                  required placeholder="53.3498" />
              </div>
              <div className="form-group">
                <label>Longitude</label>
                <input name="origin_lng" value={form.origin_lng} onChange={onChange}
                  required placeholder="-6.2603" />
              </div>
            </div>
          </div>

          {/* Destination */}
          <div className="coords-section">
            <div className="coords-label">
              <span className="coords-dot coords-dot--dest" />
              Destination
              <RegionBadge lat={form.destination_lat} lng={form.destination_lng} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Latitude</label>
                <input name="destination_lat" value={form.destination_lat} onChange={onChange}
                  required placeholder="51.8985" />
              </div>
              <div className="form-group">
                <label>Longitude</label>
                <input name="destination_lng" value={form.destination_lng} onChange={onChange}
                  required placeholder="-8.4756" />
              </div>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label>Departure time</label>
              <input name="departure_time" type="datetime-local"
                value={form.departure_time} onChange={onChange} required />
            </div>
          </div>

          <div className="form-group">
            <label>Plate number <span style={{ color: 'var(--ink-faint)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>(optional — required for enforcement check)</span></label>
            <input name="plate_number" value={form.plate_number} onChange={onChange}
              placeholder="241-D-12345" style={{ textTransform: 'uppercase' }} />
          </div>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? 'Submitting via SAGA…' : 'Request booking →'}
          </button>
          {error && <p className="error-msg">{error}</p>}
        </form>

        {result && <StatusCard result={result} />}
      </FormCard>
    </div>
  )
}
