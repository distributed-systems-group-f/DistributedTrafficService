import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router';
import { getMyJourneys, cancelBooking, BookingOut } from '../api/bookings';

type FilterType = 'all' | 'CONFIRMED' | 'PENDING' | 'CANCELLED' | 'REJECTED';

const STATUS_META: Record<string, { label: string; color: string; bg: string; dot: string }> = {
  CONFIRMED:        { label: 'Confirmed',   color: '#15803d', bg: '#dcfce7', dot: '#00c26f' },
  PENDING:          { label: 'Pending',     color: '#92400e', bg: '#fef3c7', dot: '#f59e0b' },
  SAGA_IN_PROGRESS: { label: 'Processing', color: '#6d28d9', bg: '#ede9fe', dot: '#7c3aed' },
  REJECTED:         { label: 'Rejected',   color: '#991b1b', bg: '#fee2e2', dot: '#f03e3e' },
  CANCELLED:        { label: 'Cancelled',  color: '#374151', bg: '#f3f4f6', dot: '#9ca3af' },
};

export function MyJourneys() {
  const [bookings, setBookings] = useState<BookingOut[]>([]);
  const [filter, setFilter] = useState<FilterType>('all');
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await getMyJourneys();
      const sorted = [...res.data].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setBookings(sorted);
    } catch {
      setError('Failed to load journeys. Check that the booking service is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCancel = async (id: string) => {
    if (!window.confirm('Cancel this booking? This cannot be undone.')) return;
    setCancelling(id);
    try {
      await cancelBooking(id);
      await load();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Cancellation failed');
    } finally {
      setCancelling(null);
    }
  };

  const filtered = filter === 'all' ? bookings : bookings.filter(b => b.status === filter);
  const counts = bookings.reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] || 0) + 1;
    return acc;
  }, {});

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center gap-3 text-[var(--muted-foreground)]">
      <span className="inline-block w-5 h-5 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
      Loading journeys…
    </div>
  );

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-[820px] mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="flex items-center justify-between mb-8 gap-4 flex-wrap">
          <div>
            <p style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--accent)] tracking-widest mb-1">DRIVER PORTAL</p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl">My Journeys</h1>
          </div>
          <Link to="/book" style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
            className="bg-[var(--ink)] text-white px-5 py-2.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform text-sm">
            + New booking
          </Link>
        </div>

        {error && <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg mb-6">{error}</div>}

        {/* Stats */}
        {bookings.length > 0 && (
          <div className="flex gap-3 mb-6 flex-wrap">
            {Object.entries(STATUS_META).map(([key, meta]) =>
              counts[key] ? (
                <div key={key} className="px-4 py-2 rounded-full border flex items-center gap-2"
                  style={{ borderColor: meta.dot + '44', background: meta.bg }}>
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: meta.dot }} />
                  <span className="text-sm font-semibold" style={{ color: meta.color, fontFamily: 'var(--font-display)' }}>
                    {counts[key]} {meta.label}
                  </span>
                </div>
              ) : null
            )}
          </div>
        )}

        {/* Filter Pills */}
        {bookings.length > 0 && (
          <div className="flex gap-2 mb-6 flex-wrap">
            {(['all', 'CONFIRMED', 'PENDING', 'CANCELLED', 'REJECTED'] as FilterType[]).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
                className={`px-4 py-2 rounded-full text-xs uppercase tracking-wide transition-all ${filter === f ? 'bg-[var(--ink)] text-white' : 'bg-white border border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--accent)]'}`}>
                {f === 'all' ? `All (${bookings.length})` : STATUS_META[f]?.label ?? f}
                {f !== 'all' && counts[f] ? ` (${counts[f]})` : ''}
              </button>
            ))}
          </div>
        )}

        {/* List */}
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center border-2 border-dashed border-[var(--border)]">
              <div className="text-5xl mb-4">🗺️</div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-lg mb-2">No journeys yet</h3>
              <p className="text-[var(--muted-foreground)] text-sm max-w-xs mx-auto mb-5 leading-relaxed">
                You must have a confirmed booking before you can start any journey.
              </p>
              <Link to="/book" style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
                className="bg-[var(--ink)] text-white px-5 py-2.5 rounded-[10px] text-sm hover:-translate-y-[1px] transition-transform">
                Book your first journey →
              </Link>
            </div>
          ) : filtered.map(b => {
            const meta = STATUS_META[b.status] ?? STATUS_META['CANCELLED'];
            return (
              <div key={b.booking_id}
                className="bg-white rounded-2xl p-5 border border-[var(--border)] flex items-center gap-6 hover:shadow-md hover:-translate-y-[2px] transition-all group flex-wrap">
                {/* Status + ID */}
                <div className="flex-shrink-0 min-w-[140px]">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wide"
                    style={{ background: meta.bg, color: meta.color, fontFamily: 'var(--font-display)' }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: meta.dot }} />
                    {meta.label}
                  </span>
                  <div style={{ fontFamily: 'var(--font-mono)' }} className="text-[10px] text-[var(--muted-foreground)] mt-2 break-all leading-relaxed">
                    {b.booking_id}
                  </div>
                </div>

                {/* Meta */}
                <div className="flex gap-6 flex-1 flex-wrap">
                  {b.estimated_duration_minutes && (
                    <div>
                      <p style={{ fontFamily: 'var(--font-display)' }} className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-1">Duration</p>
                      <p className="text-sm font-medium">{b.estimated_duration_minutes} min</p>
                    </div>
                  )}
                  <div>
                    <p style={{ fontFamily: 'var(--font-display)' }} className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted-foreground)] mb-1">Booked</p>
                    <p className="text-sm font-medium">
                      {new Date(b.created_at).toLocaleString('en-IE', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                {/* Cancel */}
                {['CONFIRMED', 'PENDING'].includes(b.status) && (
                  <button onClick={() => handleCancel(b.booking_id)}
                    disabled={cancelling === b.booking_id}
                    style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
                    className="px-4 py-2 text-sm text-[var(--muted-foreground)] hover:text-[var(--red)] hover:bg-red-50 rounded-[10px] border border-[var(--border)] hover:border-[var(--red)]/30 transition-all opacity-0 group-hover:opacity-100 disabled:opacity-40 disabled:cursor-not-allowed">
                    {cancelling === b.booking_id ? 'Cancelling…' : 'Cancel'}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
