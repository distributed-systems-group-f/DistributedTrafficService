import { useEffect, useState } from 'react';
import { getNotifications, type NotificationOut } from '../api/notifications';
import { useAuth } from '../contexts/AuthContext';

const CHANNEL_COLORS: Record<string, { bg: string; fg: string }> = {
  push: { bg: '#eef2ff', fg: '#3730a3' },
  sms: { bg: '#ecfdf5', fg: '#065f46' },
  email: { bg: '#fef2f2', fg: '#991b1b' },
};

export function Notifications() {
  const { user } = useAuth();
  const [items, setItems] = useState<NotificationOut[]>([]);
  const [targetUserId, setTargetUserId] = useState(user?.id ?? '');
  const [limit, setLimit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    if (!targetUserId) return;
    setLoading(true);
    setError('');
    try {
      const res = await getNotifications(targetUserId, limit);
      setItems(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user?.id) {
      setTargetUserId(user.id);
    }
  }, [user?.id]);

  useEffect(() => {
    if (targetUserId) {
      load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetUserId, limit]);

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-[920px] mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="flex items-end justify-between gap-4 mb-8 flex-wrap">
          <div>
            <p style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--accent)] tracking-widest mb-1">
              NOTIFICATION SERVICE
            </p>
            <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl">
              Notifications
            </h1>
          </div>
          <button
            onClick={load}
            style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
            className="bg-[var(--ink)] text-white px-4 py-2.5 rounded-[10px] hover:-translate-y-[1px] transition-transform text-sm"
          >
            Refresh
          </button>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-[var(--border)] mb-6 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-3 items-end">
            <div>
              <label className="block text-xs uppercase tracking-wide text-[var(--muted-foreground)] mb-1">
                User ID
              </label>
              <input
                value={targetUserId}
                onChange={(e) => setTargetUserId(e.target.value)}
                disabled={user?.role !== 'admin'}
                className="w-full px-3 py-2 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)]"
                style={{ fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wide text-[var(--muted-foreground)] mb-1">
                Limit
              </label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="px-3 py-2 bg-white border border-[var(--border)] rounded-[10px]"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
            {user?.role !== 'admin' && (
              <p className="text-xs text-[var(--muted-foreground)] md:text-right">
                Showing your own notifications.
              </p>
            )}
          </div>
        </div>

        {error && (
          <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center gap-3 text-[var(--muted-foreground)] py-10">
            <span className="inline-block w-5 h-5 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin" />
            Loading notifications…
          </div>
        ) : items.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border-2 border-dashed border-[var(--border)]">
            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-lg mb-2">
              No notifications yet
            </h3>
            <p className="text-sm text-[var(--muted-foreground)] max-w-md mx-auto">
              Notifications appear here after booking events are emitted and consumed asynchronously.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((n) => {
              const channel = n.channel?.toLowerCase() || 'push';
              const style = CHANNEL_COLORS[channel] || { bg: '#f3f4f6', fg: '#374151' };
              return (
                <div key={n.id} className="bg-white rounded-2xl p-5 border border-[var(--border)] shadow-sm">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium break-words">{n.message}</p>
                      <p className="text-xs text-[var(--muted-foreground)] mt-2" style={{ fontFamily: 'var(--font-mono)' }}>
                        {new Date(n.sent_at).toLocaleString('en-IE')} • {n.user_id}
                      </p>
                    </div>
                    <span
                      className="text-xs uppercase px-2.5 py-1 rounded-full font-semibold"
                      style={{
                        background: style.bg,
                        color: style.fg,
                        fontFamily: 'var(--font-display)',
                        letterSpacing: '0.04em',
                      }}
                    >
                      {channel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}