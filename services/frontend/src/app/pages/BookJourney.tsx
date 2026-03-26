import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '../contexts/AuthContext';
import { createBooking, BookingOut } from '../api/bookings';

type RoutePreset = {
  id: string; label: string; flag: string;
  originRegion: string; destRegion: string; note: string; isCrossRegion: boolean;
  olat: number; olng: number; dlat: number; dlng: number;
};

const ROUTE_PRESETS: RoutePreset[] = [
  { id: 'ie-dublin-cork',      label: 'Dublin → Cork',        flag: '🇮🇪',    originRegion: 'IE', destRegion: 'IE', note: 'Single region',      isCrossRegion: false, olat: 53.3498, olng: -6.2603, dlat: 51.8969, dlng: -8.4863 },
  { id: 'ie-dublin-london',    label: 'Dublin → London',      flag: '🇮🇪🇬🇧', originRegion: 'IE', destRegion: 'GB', note: 'Cross-region: IE→GB', isCrossRegion: true,  olat: 53.3498, olng: -6.2603, dlat: 51.5074, dlng: -0.1278 },
  { id: 'gb-london-manchester',label: 'London → Manchester',  flag: '🇬🇧',    originRegion: 'GB', destRegion: 'GB', note: 'Single region',      isCrossRegion: false, olat: 51.5074, olng: -0.1278, dlat: 53.4808, dlng: -2.2426 },
  { id: 'gb-london-paris',     label: 'London → Paris',       flag: '🇬🇧🇫🇷', originRegion: 'GB', destRegion: 'FR', note: 'Cross-region: GB→FR', isCrossRegion: true,  olat: 51.5074, olng: -0.1278, dlat: 48.8566, dlng:  2.3522 },
  { id: 'fr-paris-lyon',       label: 'Paris → Lyon',         flag: '🇫🇷',    originRegion: 'FR', destRegion: 'FR', note: 'Single region',      isCrossRegion: false, olat: 48.8566, olng:  2.3522, dlat: 45.7640, dlng:  4.8357 },
  { id: 'fr-paris-dublin',     label: 'Paris → Dublin',       flag: '🇫🇷🇮🇪', originRegion: 'FR', destRegion: 'IE', note: 'Cross-region: FR→IE', isCrossRegion: true,  olat: 48.8566, olng:  2.3522, dlat: 53.3498, dlng: -6.2603 },
];

function defaultDeparture() {
  const d = new Date(Date.now() + 3600 * 1000);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
}

export function BookJourney() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedRoute, setSelectedRoute] = useState<RoutePreset | null>(null);
  const [originLat, setOriginLat] = useState('53.3498');
  const [originLng, setOriginLng] = useState('-6.2603');
  const [destLat, setDestLat]   = useState('51.8969');
  const [destLng, setDestLng]   = useState('-8.4863');
  const [datetime, setDatetime] = useState(defaultDeparture());
  const [plateNumber, setPlateNumber] = useState(user?.plateNumber || '');
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState<BookingOut | null>(null);
  const [error, setError]       = useState('');

  const handleRouteSelect = (route: RoutePreset) => {
    setSelectedRoute(route);
    setOriginLat(String(route.olat));
    setOriginLng(String(route.olng));
    setDestLat(String(route.dlat));
    setDestLng(String(route.dlng));
    setResult(null);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await createBooking({
        origin_lat: parseFloat(originLat),
        origin_lng: parseFloat(originLng),
        destination_lat: parseFloat(destLat),
        destination_lng: parseFloat(destLng),
        departure_time: new Date(datetime).toISOString(),
        ...(plateNumber ? { plate_number: plateNumber.toUpperCase() } : {}),
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Booking request failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    const ok = result.status === 'CONFIRMED';
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className={`w-full max-w-[560px] rounded-2xl p-8 shadow-sm border-2 animate-in fade-in slide-in-from-bottom-2 duration-300 ${ok ? 'bg-[var(--green)] border-[var(--green)]' : 'bg-[var(--red)] border-[var(--red)]'}`}>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
              {ok
                ? <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                : <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
              }
            </div>
            <div className="flex-1">
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-2xl text-white mb-2">
                {ok ? 'Booking Confirmed' : 'Booking Rejected'}
              </h2>
              {ok ? (
                <>
                  <p className="text-white/90 mb-4">Your journey has been registered across all regional nodes.</p>
                  <div style={{ fontFamily: 'var(--font-mono)' }} className="text-sm text-white/80 bg-white/10 px-4 py-3 rounded-lg mb-2">
                    {result.booking_id}
                  </div>
                  {result.estimated_duration_minutes && (
                    <p className="text-white/70 text-sm mb-4">Est. duration: {result.estimated_duration_minutes} min</p>
                  )}
                </>
              ) : (
                <p className="text-white/90 mb-6">Capacity full or SAGA transaction rolled back. Please try a different time slot.</p>
              )}
              <button
                onClick={() => navigate('/journeys')}
                style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
                className="bg-white text-[var(--ink)] px-6 py-2.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform text-sm"
              >
                View all journeys →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-[560px] mx-auto">
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-[var(--border)] animate-in fade-in slide-in-from-bottom-2 duration-300">
          <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl mb-8">
            Book a Journey
          </h1>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Route Presets */}
            <div>
              <label className="block text-sm mb-3 text-[var(--foreground)]">Select Route</label>
              <div className="grid grid-cols-2 gap-3">
                {ROUTE_PRESETS.map(route => (
                  <button key={route.id} type="button" onClick={() => handleRouteSelect(route)}
                    className={`p-4 rounded-[10px] border-2 text-left transition-all hover:-translate-y-[1px] ${selectedRoute?.id === route.id ? 'border-[var(--accent)] bg-[var(--accent)]/5' : 'border-[var(--border)] hover:border-[var(--accent)]/40'}`}>
                    <div className="text-2xl mb-1">{route.flag}</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-sm mb-1">{route.label}</div>
                    <div className="text-xs text-[var(--muted-foreground)]">{route.note}</div>
                  </button>
                ))}
              </div>
            </div>

            {selectedRoute?.isCrossRegion && (
              <div className="bg-[var(--violet)]/10 border border-[var(--violet)]/30 rounded-lg p-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="flex items-start gap-3">
                  <span className="text-xl">⚡</span>
                  <div className="text-sm">
                    <span className="font-semibold text-[var(--violet)]">Cross-region journey</span>
                    <span className="text-[var(--foreground)]/70"> — SAGA will coordinate distributed locks across regional schemas.</span>
                  </div>
                </div>
              </div>
            )}

            {/* Origin */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[var(--green)]"></div>
                <span className="text-xs font-semibold tracking-wide" style={{ fontFamily: 'var(--font-display)' }}>ORIGIN</span>
                {selectedRoute && <span className="px-2 py-0.5 bg-[var(--muted)] rounded-full text-xs" style={{ fontFamily: 'var(--font-mono)' }}>{selectedRoute.originRegion}</span>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1.5 text-[var(--muted-foreground)]">Latitude</label>
                  <input type="text" value={originLat} onChange={e => setOriginLat(e.target.value)} style={{ fontFamily: 'var(--font-mono)' }}
                    className="w-full px-3 py-2 text-sm bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
                </div>
                <div>
                  <label className="block text-xs mb-1.5 text-[var(--muted-foreground)]">Longitude</label>
                  <input type="text" value={originLng} onChange={e => setOriginLng(e.target.value)} style={{ fontFamily: 'var(--font-mono)' }}
                    className="w-full px-3 py-2 text-sm bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
                </div>
              </div>
            </div>

            {/* Destination */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[var(--red)]"></div>
                <span className="text-xs font-semibold tracking-wide" style={{ fontFamily: 'var(--font-display)' }}>DESTINATION</span>
                {selectedRoute && <span className="px-2 py-0.5 bg-[var(--muted)] rounded-full text-xs" style={{ fontFamily: 'var(--font-mono)' }}>{selectedRoute.destRegion}</span>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1.5 text-[var(--muted-foreground)]">Latitude</label>
                  <input type="text" value={destLat} onChange={e => setDestLat(e.target.value)} style={{ fontFamily: 'var(--font-mono)' }}
                    className="w-full px-3 py-2 text-sm bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
                </div>
                <div>
                  <label className="block text-xs mb-1.5 text-[var(--muted-foreground)]">Longitude</label>
                  <input type="text" value={destLng} onChange={e => setDestLng(e.target.value)} style={{ fontFamily: 'var(--font-mono)' }}
                    className="w-full px-3 py-2 text-sm bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2 text-[var(--foreground)]">Departure Time</label>
              <input type="datetime-local" value={datetime} onChange={e => setDatetime(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
            </div>

            <div>
              <label className="block text-sm mb-2 text-[var(--foreground)]">
                Plate Number <span className="text-[var(--muted-foreground)]">(optional — required for enforcement checks)</span>
              </label>
              <input type="text" value={plateNumber} onChange={e => setPlateNumber(e.target.value.toUpperCase())}
                style={{ fontFamily: 'var(--font-mono)' }}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all uppercase"
                placeholder="ABC-123" />
            </div>

            {error && <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg">{error}</div>}

            <button type="submit" disabled={loading || !selectedRoute}
              style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
              className="w-full bg-[var(--ink)] text-white py-3.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  {selectedRoute?.isCrossRegion ? 'Submitting via SAGA…' : 'Submitting…'}
                </span>
              ) : 'Request booking →'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
