import { useEffect, useMemo, useState } from 'react';
import {
  getDashboard,
  getCapacityReport,
  getUsageReport,
  type DashboardStats,
  type CapacityReport,
  type UsageReport,
} from '../api/analytics';

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-[var(--border)] shadow-sm">
      <p className="text-xs uppercase tracking-widest text-[var(--muted-foreground)]" style={{ fontFamily: 'var(--font-mono)' }}>
        {label}
      </p>
      <p className="text-3xl mt-2" style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color }}>
        {value}
      </p>
    </div>
  );
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [capacity, setCapacity] = useState<CapacityReport[]>([]);
  const [usage, setUsage] = useState<UsageReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const [dashboardRes, capacityRes, usageRes] = await Promise.all([
          getDashboard(),
          getCapacityReport(),
          getUsageReport(),
        ]);
        setStats(dashboardRes.data);
        setCapacity(capacityRes.data);
        setUsage(usageRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load analytics dashboard.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const topSegments = useMemo(
    () => [...capacity].sort((a, b) => b.utilization_pct - a.utilization_pct).slice(0, 8),
    [capacity]
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 text-[var(--muted-foreground)]">
        <span className="inline-block w-5 h-5 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
        Loading analytics…
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-[1040px] mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="flex items-end justify-between gap-4 mb-8 flex-wrap">
          <div>
            <p style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--accent)] tracking-widest mb-1">
              ADMIN ANALYTICS
            </p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl">
              Distributed System Dashboard
            </h1>
          </div>
          {stats?.last_updated && (
            <p className="text-xs text-[var(--muted-foreground)]" style={{ fontFamily: 'var(--font-mono)' }}>
              LAST UPDATE {new Date(stats.last_updated).toLocaleString('en-IE')}
            </p>
          )}
        </div>

        {error && (
          <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total Events" value={stats.total_bookings} color="var(--ink)" />
            <StatCard label="Confirmed" value={stats.confirmed} color="var(--green)" />
            <StatCard label="Cancelled" value={stats.cancelled} color="var(--amber)" />
            <StatCard label="Failed" value={stats.failed} color="var(--red)" />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-2xl p-6 border border-[var(--border)] shadow-sm">
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-lg mb-4">
              Events By Region
            </h2>
            {!stats || Object.keys(stats.by_region || {}).length === 0 ? (
              <p className="text-sm text-[var(--muted-foreground)]">No regional events yet.</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(stats.by_region)
                  .sort((a, b) => b[1] - a[1])
                  .map(([region, count]) => (
                    <div key={region} className="grid grid-cols-[1fr_auto] items-center gap-4">
                      <p className="text-sm font-medium">{region}</p>
                      <p className="text-sm" style={{ fontFamily: 'var(--font-mono)' }}>
                        {count}
                      </p>
                    </div>
                  ))}
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl p-6 border border-[var(--border)] shadow-sm">
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-lg mb-4">
              Usage Snapshot
            </h2>
            {!usage ? (
              <p className="text-sm text-[var(--muted-foreground)]">No usage data yet.</p>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">24h Events</p>
                    <p className="text-xl" style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }}>
                      {usage.last_24h_events}
                    </p>
                  </div>
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Total Events</p>
                    <p className="text-xl" style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }}>
                      {usage.total_events}
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  {Object.entries(usage.by_event_type || {}).map(([eventType, count]) => (
                    <div key={eventType} className="flex items-center justify-between text-sm">
                      <span>{eventType}</span>
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{count}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-[var(--border)] shadow-sm">
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-lg mb-4">
            Top Capacity Utilization
          </h2>
          {topSegments.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)]">No segment utilization data yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="text-left border-b border-[var(--border)] text-[var(--muted-foreground)]">
                    <th className="pb-2">Segment</th>
                    <th className="pb-2">Region</th>
                    <th className="pb-2">Slot</th>
                    <th className="pb-2">Booked / Max</th>
                    <th className="pb-2">Utilization</th>
                  </tr>
                </thead>
                <tbody>
                  {topSegments.map((row) => (
                    <tr key={`${row.segment_id}-${row.slot_start}`} className="border-b border-[var(--border)]/60">
                      <td className="py-2" style={{ fontFamily: 'var(--font-mono)' }}>{row.segment_id.slice(0, 8)}…</td>
                      <td className="py-2">{row.region}</td>
                      <td className="py-2">{new Date(row.slot_start).toLocaleString('en-IE', { dateStyle: 'short', timeStyle: 'short' })}</td>
                      <td className="py-2">{row.booked_count} / {row.max_capacity}</td>
                      <td className="py-2 font-semibold" style={{ color: row.utilization_pct >= 90 ? 'var(--red)' : 'var(--ink)' }}>
                        {row.utilization_pct.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}