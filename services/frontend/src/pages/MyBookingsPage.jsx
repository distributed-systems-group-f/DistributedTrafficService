import { useEffect, useState } from 'react'
import { getMyJourneys, cancelBooking } from '../api/bookings'
import './MyBookingsPage.css'

const STATUS_COLOR = {
  CONFIRMED: '#16a34a',
  PENDING: '#d97706',
  REJECTED: '#dc2626',
  CANCELLED: '#6b7280',
  SAGA_IN_PROGRESS: '#7c3aed',
}

export default function MyBookingsPage() {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    try {
      const res = await getMyJourneys()
      setBookings(res.data)
    } catch (err) {
      setError('Failed to load bookings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleCancel(id) {
    if (!confirm('Cancel this booking?')) return
    try {
      await cancelBooking(id)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Cancel failed')
    }
  }

  if (loading) return <div className="page-center">Loading...</div>
  if (error) return <div className="page-center error-msg">{error}</div>

  return (
    <div className="bookings-page">
      <h2>My Journeys</h2>
      {bookings.length === 0 ? (
        <p className="empty">No bookings yet.</p>
      ) : (
        <table className="bookings-table">
          <thead>
            <tr>
              <th>Booking ID</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {bookings.map(b => (
              <tr key={b.booking_id}>
                <td className="mono">{b.booking_id.slice(0, 8)}…</td>
                <td>
                  <span className="status-badge" style={{ color: STATUS_COLOR[b.status] || '#333' }}>
                    {b.status}
                  </span>
                </td>
                <td>{b.estimated_duration_minutes ? `${b.estimated_duration_minutes} min` : '—'}</td>
                <td>{new Date(b.created_at).toLocaleString()}</td>
                <td>
                  {['CONFIRMED', 'PENDING'].includes(b.status) && (
                    <button className="btn-cancel" onClick={() => handleCancel(b.booking_id)}>Cancel</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
