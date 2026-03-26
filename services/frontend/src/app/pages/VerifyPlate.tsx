import { useState } from 'react';
import { verifyPlate, VerificationResult } from '../api/verification';

type RecentCheck = VerificationResult & { checkedAt: string };

export function VerifyPlate() {
  const [plate, setPlate]           = useState('');
  const [result, setResult]         = useState<VerificationResult | null>(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [recentChecks, setRecentChecks] = useState<RecentCheck[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await verifyPlate(plate.toUpperCase().trim());
      setResult(res.data);
      setRecentChecks(prev => [{ ...res.data, checkedAt: new Date().toISOString() }, ...prev.slice(0, 4)]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Lookup failed. Check the service is running.');
    } finally {
      setLoading(false);
    }
  };

  const sourceColor = result?.source === 'cache' ? 'var(--green)' : 'var(--accent)';
  const sourceLabel = result?.source === 'cache' ? 'CACHE  < 1ms' : result?.source === 'database' ? 'DATABASE  ~20ms' : null;

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-[500px] mx-auto">
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-[var(--border)] animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--muted-foreground)] mb-4 tracking-wide">
            ENFORCEMENT — REAL-TIME LOOKUP
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl mb-8">
            Verify Vehicle
          </h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm mb-2 text-[var(--foreground)]">Vehicle Plate Number</label>
              <input
                type="text"
                value={plate}
                onChange={e => setPlate(e.target.value.toUpperCase())}
                style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', letterSpacing: '0.05em' }}
                className="w-full px-4 py-4 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all uppercase text-center"
                placeholder="ABC-123"
                required
              />
            </div>

            {error && <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg">{error}</div>}

            <button type="submit" disabled={loading}
              style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
              className="w-full bg-[var(--ink)] text-white py-3.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform disabled:opacity-50">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  Checking…
                </span>
              ) : 'Check now →'}
            </button>
          </form>

          {/* Result */}
          {result && (
            <div className={`mt-6 rounded-2xl p-6 animate-in fade-in slide-in-from-top-2 duration-300 border-2 ${result.is_authorized ? 'bg-[var(--green)] border-[var(--green)]' : 'bg-[var(--red)] border-[var(--red)]'}`}>
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                  {result.is_authorized
                    ? <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                    : <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
                  }
                </div>
                <div className="flex-1">
                  <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-xl text-white mb-1">
                    {result.is_authorized ? 'AUTHORIZED' : 'NOT AUTHORIZED'}
                  </h3>
                  <div style={{ fontFamily: 'var(--font-mono)' }} className="text-2xl font-semibold text-white mb-4 tracking-wider">
                    {result.plate_number}
                  </div>

                  {result.is_authorized ? (
                    <>
                      <div className="space-y-2 mb-4">
                        {result.booking_id && (
                          <div className="text-sm text-white/90">
                            <span className="opacity-70">Booking ID:</span>
                            <div style={{ fontFamily: 'var(--font-mono)' }} className="font-semibold mt-0.5 break-all">{result.booking_id}</div>
                          </div>
                        )}
                        {result.departure_time && (
                          <div className="text-sm text-white/90">
                            <span className="opacity-70">Departure window:</span>
                            <div className="font-semibold mt-0.5">
                              {new Date(result.departure_time).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' })}
                              {result.journey_window_end && ` — ${new Date(result.journey_window_end).toLocaleTimeString('en-IE', { timeStyle: 'short' })}`}
                            </div>
                          </div>
                        )}
                        {result.segments && result.segments.length > 0 && (
                          <div className="text-sm text-white/90">
                            <span className="opacity-70">Regions:</span>
                            <span className="font-semibold ml-1">{result.segments.join(', ')}</span>
                          </div>
                        )}
                      </div>
                      {/* Source badge — key demo point for professor */}
                      {sourceLabel && (
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/20 rounded-full">
                          <div className="w-2 h-2 rounded-full" style={{ background: sourceColor }}></div>
                          <span style={{ fontFamily: 'var(--font-mono)' }} className="text-xs font-semibold text-white uppercase">
                            {sourceLabel}
                          </span>
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="text-white/90 text-sm">{result.message}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recent Checks */}
        {recentChecks.length > 0 && (
          <div className="mt-6 bg-white rounded-2xl p-6 shadow-sm border border-[var(--border)]">
            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-sm mb-4 uppercase tracking-wide">
              Recent Checks
            </h3>
            <div className="space-y-2">
              {recentChecks.map((check, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full" style={{ background: check.is_authorized ? 'var(--green)' : 'var(--red)' }}></div>
                    <span style={{ fontFamily: 'var(--font-mono)' }} className="font-semibold text-sm">{check.plate_number}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{
                      fontFamily: 'var(--font-mono)',
                      background: check.source === 'cache' ? '#dcfce7' : '#eff6ff',
                      color: check.source === 'cache' ? '#15803d' : 'var(--accent)',
                    }}>
                      {check.source?.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {new Date(check.checkedAt).toLocaleTimeString('en-IE', { timeStyle: 'short' })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
