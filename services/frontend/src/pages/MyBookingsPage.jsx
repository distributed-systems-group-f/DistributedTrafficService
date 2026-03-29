import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getMyJourneys, cancelBooking } from '../api/bookings'
import './MyBookingsPage.css'

const STATUS_META = {
  CONFIRMED:        { label: 'Confirmed',    color: '#15803d', bg: '#dcfce7', dot: '#00c26f' },
  PENDING:          { label: 'Pending',      color: '#92400e', bg: '#fef3c7', dot: '#f59e0b' },
  SAGA_IN_PROGRESS: { label: 'Processing',  color: '#6d28d9', bg: '#ede9fe', dot: '#7c3aed' },
  REJECTED:         { label: 'Rejected',     color: '#991b1b', bg: '#fee2e2', dot: '#f03e3e' },
  CANCELLED:        { label: 'Cancelled',    color: '#374151', bg: '#f3f4f6', dot: '#9ca3af' },
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, color: '#374151', bg: '#f3f4f6', dot: '#9ca3af' }
  return (
    <span className="status-badge" style={{ color: meta.color, background: meta.bg }}>
      <span className="status-dot" style={{ background: meta.dot }} />
      {meta.label}
    </span>
  )
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">🗺️</div>
      <h3>No journeys yet</h3>
      <p>Your booked journeys will appear here. You need a confirmed booking before you can start a journey.</p>
      <Link to="/bookings/new" className="btn-primary" style={{ display: 'inline-block', width: 'auto', marginTop: 8, padding: '10px 24px', textDecoration: 'none' }}>
        Book your first journey →
      </Link>
    </div>
  )
}

export default function MyBookingsPage() {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cancelling, setCancelling] = useState(null)
  const [filter, setFilter] = useState('all')

  const load = useCallback(async () => {
    try {
      const res = await getMyJourneys()
      // Sort: newest first
      const sorted = [...res.data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      setBookings(sorted)
    } catch {
      setError('Failed to load your journeys. Check that the booking service is running.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCancel(id) {
    if (!window.confirm('Cancel this booking? This cannot be undone.')) return
    setCancelling(id)
    try {
      await cancelBooking(id)
      await load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Cancellation failed')
    } finally {
      setCancelling(null)
    }
  }

  const filtered = filter === 'all'
    ? bookings
    : bookings.filter(b => b.status === filter)

  const counts = bookings.reduce((acc, b) => {
    acc[b.status] = (acc[b.status] || 0) + 1
    return acc
  }, {})

  if (loading) return (
    <div className="page-center">
      <div className="spinner" /> Loading journeys…
    </div>
  )

  if (error) return (
    <div className="bookings-page">
      <p className="error-msg">{error}</p>
    </div>
  )

  return (
    <div className="bookings-page">
      <div className="bookings-header">
        <div>
          <p className="bookings-eyebrow">Driver portal</p>
          <h1 className="bookings-title">My Journeys</h1>
        </div>
        <Link to="/bookings/new" className="btn-primary"
          style={{ width: 'auto', padding: '10px 20px', textDecoration: 'none', fontSize: '0.85rem' }}>
          + New booking
        </Link>
      </div>

      {bookings.length > 0 && (
        <div className="stats-row">
          {Object.entries(STATUS_META).map(([key, meta]) =>
            counts[key] ? (
              <div key={key} className="stat-chip" style={{ borderColor: meta.dot + '44', background: meta.bg }}>
                <span className="stat-num" style={{ color: meta.color }}>{counts[key]}</span>
                <span className="stat-label" style={{ color: meta.color }}>{meta.label}</span>
              </div>
            ) : null
          )}
        </div>
      )}

      {bookings.length > 0 && (
        <div className="filter-row">
          {['all', 'CONFIRMED', 'PENDING', 'CANCELLED', 'REJECTED'].map(f => (
            <button key={f} className={`filter-btn ${filter === f ? 'filter-btn--active' : ''}`}
              onClick={() => setFilter(f)}>
              {f === 'all' ? 'All' : STATUS_META[f]?.label || f}
              {f === 'all' ? ` (${bookings.length})` : counts[f] ? ` (${counts[f]})` : ''}
            </button>
          ))}
        </div>
      )}

      {filtered.length === 0 && bookings.length === 0 && <EmptyState />}
      {filtered.length === 0 && bookings.length > 0 && (
        <p style={{ color: 'var(--ink-muted)', padding: '32px 0' }}>No bookings match this filter.</p>
      )}

      {filtered.length > 0 && (
        <div className="bookings-list">
          {filtered.map(b => (
            <div key={b.booking_id} className="booking-card">
              <div className="booking-card-left">
                <StatusBadge status={b.status} />
                <div className="booking-id">
                  <span className="booking-id-label">Booking ID</span>
                  <code className="booking-id-value">{b.booking_id}</code>
                </div>
              </div>
              <div className="booking-card-center">
                {b.estimated_duration_minutes && (
                  <div className="booking-meta-item">
                    <span>Est. duration</span>
                    <strong>{b.estimated_duration_minutes} min</strong>
                  </div>
                )}
                <div className="booking-meta-item">
                  <span>Booked</span>
                  <strong>{new Date(b.created_at).toLocaleString('en-IE', {
                    day: 'numeric', month: 'short', year: 'numeric',
                    hour: '2-digit', minute: '2-digit',
                  })}</strong>
                </div>
              </div>
              <div className="booking-card-right">
                {['CONFIRMED', 'PENDING'].includes(b.status) && (
                  <button
                    className="btn-cancel"
                    disabled={cancelling === b.booking_id}
                    onClick={() => handleCancel(b.booking_id)}>
                    {cancelling === b.booking_id ? 'Cancelling…' : 'Cancel'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
