import { useEffect, useState } from 'react'
import { getDashboard } from '../api/analytics'
import './DashboardPage.css'

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getDashboard()
      .then(res => setStats(res.data))
      .catch(() => setError('Failed to load dashboard'))
  }, [])

  if (error) return <div className="page-center error-msg">{error}</div>
  if (!stats) return <div className="page-center">Loading...</div>

  return (
    <div className="dashboard">
      <h2>Analytics Dashboard</h2>
      <div className="stat-grid">
        <StatCard label="Total Events" value={stats.total_bookings} color="#2563eb" />
        <StatCard label="Confirmed" value={stats.confirmed} color="#16a34a" />
        <StatCard label="Cancelled" value={stats.cancelled} color="#d97706" />
        <StatCard label="Failed" value={stats.failed} color="#dc2626" />
      </div>

      <div className="section">
        <h3>Events by Region</h3>
        {Object.keys(stats.by_region).length === 0 ? (
          <p className="empty">No regional data yet.</p>
        ) : (
          <table className="data-table">
            <thead><tr><th>Region</th><th>Events</th></tr></thead>
            <tbody>
              {Object.entries(stats.by_region).map(([region, count]) => (
                <tr key={region}>
                  <td>{region}</td>
                  <td>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="last-updated">Last updated: {new Date(stats.last_updated).toLocaleTimeString()}</p>
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card">
      <p className="stat-value" style={{ color }}>{value}</p>
      <p className="stat-label">{label}</p>
    </div>
  )
}
