import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet';
import { useAuth } from '../contexts/AuthContext';
import {
  createBooking,
  previewRoute,
  type BookingOut,
  type RoutePreviewOut,
} from '../api/bookings';

import 'leaflet/dist/leaflet.css';

type Waypoint = {
  id: string;
  label: string;
  region: 'EU_WEST_IRELAND' | 'EU_WEST_UK' | 'EU_WEST_FRANCE';
  lat: number;
  lng: number;
};

const WAYPOINTS: Waypoint[] = [
  { id: 'dublin', label: 'Dublin', region: 'EU_WEST_IRELAND', lat: 53.3498, lng: -6.2603 },
  { id: 'cork', label: 'Cork', region: 'EU_WEST_IRELAND', lat: 51.8985, lng: -8.4756 },
  { id: 'galway', label: 'Galway', region: 'EU_WEST_IRELAND', lat: 53.2707, lng: -9.0568 },
  { id: 'limerick', label: 'Limerick', region: 'EU_WEST_IRELAND', lat: 52.6638, lng: -8.6267 },
  { id: 'belfast', label: 'Belfast', region: 'EU_WEST_UK', lat: 54.5973, lng: -5.9301 },
  { id: 'holyhead', label: 'Holyhead', region: 'EU_WEST_UK', lat: 53.3083, lng: -4.6325 },
  { id: 'london', label: 'London', region: 'EU_WEST_UK', lat: 51.5074, lng: -0.1278 },
  { id: 'birmingham', label: 'Birmingham', region: 'EU_WEST_UK', lat: 52.4862, lng: -1.8904 },
  { id: 'manchester', label: 'Manchester', region: 'EU_WEST_UK', lat: 53.4808, lng: -2.2426 },
  { id: 'paris', label: 'Paris', region: 'EU_WEST_FRANCE', lat: 48.8566, lng: 2.3522 },
  { id: 'lyon', label: 'Lyon', region: 'EU_WEST_FRANCE', lat: 45.7640, lng: 4.8357 },
  { id: 'marseille', label: 'Marseille', region: 'EU_WEST_FRANCE', lat: 43.2965, lng: 5.3698 },
  { id: 'bordeaux', label: 'Bordeaux', region: 'EU_WEST_FRANCE', lat: 44.8378, lng: -0.5792 },
  { id: 'calais', label: 'Calais', region: 'EU_WEST_FRANCE', lat: 50.9513, lng: 1.8587 },
];

const WAYPOINT_BY_ID = Object.fromEntries(WAYPOINTS.map((w) => [w.id, w])) as Record<string, Waypoint>;

type RoutePreset = {
  id: string;
  label: string;
  flag: string;
  note: string;
  originId: string;
  destinationId: string;
};

const ROUTE_PRESETS: RoutePreset[] = [
  { id: 'ie-dublin-cork', label: 'Dublin → Cork', flag: '🇮🇪', note: 'Single region', originId: 'dublin', destinationId: 'cork' },
  { id: 'ie-dublin-birmingham', label: 'Dublin → Birmingham', flag: '🇮🇪🇬🇧', note: 'Cross-region: IE→GB', originId: 'dublin', destinationId: 'birmingham' },
  { id: 'gb-london-manchester', label: 'London → Manchester', flag: '🇬🇧', note: 'Single region', originId: 'london', destinationId: 'manchester' },
  { id: 'fr-paris-lyon', label: 'Paris → Lyon', flag: '🇫🇷', note: 'Single region', originId: 'paris', destinationId: 'lyon' },
  { id: 'fr-paris-marseille', label: 'Paris → Marseille', flag: '🇫🇷', note: 'Single region', originId: 'paris', destinationId: 'marseille' },
];

function defaultDeparture() {
  const d = new Date(Date.now() + 3600 * 1000);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
}

export function BookJourney() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedRoute, setSelectedRoute] = useState<string>('');
  const [originId, setOriginId] = useState<string>('dublin');
  const [destinationId, setDestinationId] = useState<string>('cork');
  const [datetime, setDatetime] = useState(defaultDeparture());
  const [plateNumber, setPlateNumber] = useState(user?.plateNumber || '');
  const [routePreview, setRoutePreview] = useState<RoutePreviewOut | null>(null);
  const [checkingRoute, setCheckingRoute] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState<BookingOut | null>(null);
  const [error, setError]       = useState('');

  const origin = originId ? WAYPOINT_BY_ID[originId] : null;
  const destination = destinationId ? WAYPOINT_BY_ID[destinationId] : null;
  const isCrossRegion = !!origin && !!destination && origin.region !== destination.region;

  const canSubmit = useMemo(
    () => !!origin && !!destination && !!datetime && !!routePreview?.route_available && !checkingRoute,
    [origin, destination, datetime, routePreview, checkingRoute]
  );

  const handleRouteSelect = (route: RoutePreset) => {
    setSelectedRoute(route.id);
    setOriginId(route.originId);
    setDestinationId(route.destinationId);
    setResult(null);
    setError('');
  };

  const handleMapPointClick = (id: string) => {
    setSelectedRoute('');
    setResult(null);
    setError('');
    if (!originId) {
      setOriginId(id);
      return;
    }
    if (originId === id) {
      setOriginId('');
      setDestinationId('');
      return;
    }
    if (!destinationId) {
      setDestinationId(id);
      return;
    }
    if (destinationId === id) {
      setDestinationId('');
      return;
    }
    setDestinationId(id);
  };

  useEffect(() => {
    let cancelled = false;

    async function checkRoute() {
      if (!origin || !destination || !datetime) {
        setRoutePreview(null);
        setPreviewError('');
        return;
      }
      setCheckingRoute(true);
      setPreviewError('');
      try {
        const res = await previewRoute({
          origin_lat: origin.lat,
          origin_lng: origin.lng,
          destination_lat: destination.lat,
          destination_lng: destination.lng,
          departure_time: new Date(datetime).toISOString(),
        });
        if (cancelled) return;
        setRoutePreview(res.data);
        if (!res.data.route_available) {
          setPreviewError(res.data.reason || 'No valid path found between origin and destination.');
        }
      } catch (err: any) {
        if (cancelled) return;
        setRoutePreview(null);
        setPreviewError(err.response?.data?.detail || 'Could not validate route right now.');
      } finally {
        if (!cancelled) setCheckingRoute(false);
      }
    }

    checkRoute();
    return () => {
      cancelled = true;
    };
  }, [origin, destination, datetime]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin || !destination) {
      setError('Select origin and destination from the map first.');
      return;
    }
    if (!routePreview?.route_available) {
      setError(previewError || 'No valid path found between origin and destination.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await createBooking({
        origin_lat: origin.lat,
        origin_lng: origin.lng,
        destination_lat: destination.lat,
        destination_lng: destination.lng,
        departure_time: new Date(datetime).toISOString(),
        ...(plateNumber ? { plate_number: plateNumber.toUpperCase() } : {}),
      });
      setResult(res.data);
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || '';

      let msg = 'Booking request failed. Please try again.';

      const isTimeout = err.code === 'ECONNABORTED' || err.message?.includes('timeout');
      const isNetworkError = !err.response;

      if (isTimeout || isNetworkError) {
        msg = 'A regional node appears to be down. The service is partially available — try booking within a single region (e.g. London → Manchester or Dublin → Cork).';
      } else if (status === 503 || status === 502) {
        msg = 'A regional node is currently unavailable. Try a same-region journey — cross-region bookings are temporarily suspended.';
      } else if (status === 409) {
        if (detail.toLowerCase().includes('peer') || detail.toLowerCase().includes('saga') || detail.toLowerCase().includes('rollback')) {
          msg = 'Cross-region SAGA failed — the peer regional node could not be reached. Your reservations have been rolled back automatically. Try a same-region journey or retry later.';
        } else {
          msg = 'Capacity full for this time slot. Please try a different departure time.';
        }
      } else if (detail) {
        msg = detail;
      }

      setError(msg);
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
                <p className="text-white/90 mb-6">Booking could not be completed — capacity full, regional node unavailable, or SAGA rolled back. Please try a different time or route.</p>
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
                    className={`p-4 rounded-[10px] border-2 text-left transition-all hover:-translate-y-[1px] ${selectedRoute === route.id ? 'border-[var(--accent)] bg-[var(--accent)]/5' : 'border-[var(--border)] hover:border-[var(--accent)]/40'}`}>
                    <div className="text-2xl mb-1">{route.flag}</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }} className="text-sm mb-1">{route.label}</div>
                    <div className="text-xs text-[var(--muted-foreground)]">{route.note}</div>
                  </button>
                ))}
              </div>
            </div>

            {isCrossRegion && (
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

            <div>
              <label className="block text-sm mb-2 text-[var(--foreground)]">Pick on map (click two points)</label>
              <div className="bg-white border border-[var(--border)] rounded-[10px] p-3">
                <MapContainer center={[52.0, -2.0]} zoom={5} className="h-[360px] w-full rounded-lg z-0" scrollWheelZoom>
                  <TileLayer
                    attribution='&copy; OpenStreetMap contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {origin && destination && routePreview?.route_available && routePreview.segments.length > 0 ? (
                    <>
                      {/* Dashed approach line: origin to first segment start */}
                      {routePreview.segments[0].start_lat != null && (
                        <Polyline
                          positions={[
                            [origin.lat, origin.lng],
                            [routePreview.segments[0].start_lat!, routePreview.segments[0].start_lng!],
                          ]}
                          pathOptions={{ color: '#888', dashArray: '6 6', weight: 2, opacity: 0.5 }}
                        />
                      )}
                      {/* Colored route segments */}
                      {routePreview.segments.map((seg, idx) => {
                        if (seg.start_lat == null || seg.end_lat == null) return null;
                        const regionColor =
                          seg.region === 'EU_WEST_IRELAND' ? '#00c26f' :
                          seg.region === 'EU_WEST_UK' ? '#2563eb' :
                          seg.region === 'EU_WEST_FRANCE' ? '#f59e0b' : '#888';
                        return (
                          <Polyline
                            key={`seg-${seg.segment_id}-${idx}`}
                            positions={[
                              [seg.start_lat!, seg.start_lng!],
                              [seg.end_lat!, seg.end_lng!],
                            ]}
                            pathOptions={{ color: regionColor, weight: 4, opacity: 0.85 }}
                          />
                        );
                      })}
                      {/* Dashed approach line: last segment end to destination */}
                      {routePreview.segments[routePreview.segments.length - 1].end_lat != null && (
                        <Polyline
                          positions={[
                            [routePreview.segments[routePreview.segments.length - 1].end_lat!, routePreview.segments[routePreview.segments.length - 1].end_lng!],
                            [destination.lat, destination.lng],
                          ]}
                          pathOptions={{ color: '#888', dashArray: '6 6', weight: 2, opacity: 0.5 }}
                        />
                      )}
                    </>
                  ) : origin && destination ? (
                    <Polyline
                      positions={[
                        [origin.lat, origin.lng],
                        [destination.lat, destination.lng],
                      ]}
                      pathOptions={{ color: '#1a1aff', dashArray: '8 8', weight: 3 }}
                    />
                  ) : null}
                  {WAYPOINTS.map((wp) => {
                    const isOrigin = wp.id === originId;
                    const isDestination = wp.id === destinationId;
                    const fillColor = isOrigin ? '#00c26f' : isDestination ? '#f03e3e' : '#2563eb';
                    return (
                      <CircleMarker
                        key={wp.id}
                        center={[wp.lat, wp.lng]}
                        radius={isOrigin || isDestination ? 9 : 7}
                        pathOptions={{ color: '#ffffff', weight: 2, fillColor, fillOpacity: 0.95 }}
                        eventHandlers={{ click: () => handleMapPointClick(wp.id) }}
                      >
                        <Popup>
                          <div className="text-sm">
                            <strong>{wp.label}</strong>
                            <br />
                            {wp.region}
                            <br />
                            Click to select
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </MapContainer>
              </div>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="px-3 py-2 rounded-lg bg-[var(--green-bg)] border border-[var(--border)]">
                  <strong>Origin:</strong>{' '}
                  {origin ? `${origin.label} (${origin.region})` : 'Not selected'}
                </div>
                <div className="px-3 py-2 rounded-lg bg-[var(--red-bg)] border border-[var(--border)]">
                  <strong>Destination:</strong>{' '}
                  {destination ? `${destination.label} (${destination.region})` : 'Not selected'}
                </div>
              </div>
              {routePreview?.route_available && routePreview.segments.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-[var(--muted-foreground)]">
                  <span className="flex items-center gap-1.5"><span style={{width:14,height:3,borderRadius:2,background:'#00c26f',display:'inline-block'}}></span> Ireland</span>
                  <span className="flex items-center gap-1.5"><span style={{width:14,height:3,borderRadius:2,background:'#2563eb',display:'inline-block'}}></span> UK</span>
                  <span className="flex items-center gap-1.5"><span style={{width:14,height:3,borderRadius:2,background:'#f59e0b',display:'inline-block'}}></span> France</span>
                  <span className="flex items-center gap-1.5"><span style={{width:14,height:0,borderRadius:2,background:'#888',display:'inline-block',borderTop:'2px dashed #888'}}></span> Approach</span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm mb-2 text-[var(--foreground)]">Departure Time</label>
              <input type="datetime-local" value={datetime} onChange={e => setDatetime(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all" required />
            </div>

            <div className="rounded-lg border border-[var(--border)] p-4 bg-[var(--surface)]/70">
              <p className="text-sm font-semibold mb-2">Route Check</p>
              {checkingRoute ? (
                <p className="text-sm text-[var(--muted-foreground)]">Checking route availability…</p>
              ) : routePreview?.route_available ? (
                <div className="space-y-2">
                  <p className="text-sm text-[var(--green)]">
                    Route available • {routePreview.segments.length} segment(s) • {routePreview.estimated_duration_minutes} min
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]" style={{ fontFamily: 'var(--font-mono)' }}>
                    {routePreview.region_chain.join(' → ')}
                  </p>
                  <div className="space-y-1 max-h-28 overflow-auto pr-1">
                    {routePreview.segments.slice(0, 6).map((s, idx) => (
                      <p key={`${s.segment_id}-${idx}`} className="text-xs text-[var(--foreground)]/80">
                        {idx + 1}. {s.segment_name} ({s.region}) • {s.distance_km.toFixed(1)} km
                      </p>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-[var(--red)]">
                  {previewError || 'Select two points to validate route.'}
                </p>
              )}
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

            <button type="submit" disabled={loading || !canSubmit}
              style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
              className="w-full bg-[var(--ink)] text-white py-3.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  {isCrossRegion ? 'Submitting via SAGA…' : 'Submitting…'}
                </span>
              ) : !origin || !destination ? (
                'Select origin + destination'
              ) : routePreview?.route_available === false ? (
                'Route unavailable'
              ) : checkingRoute ? (
                'Checking route…'
              ) : (
                'Request booking →'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}