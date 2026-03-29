import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth, UserRole, Region } from '../contexts/AuthContext';

export function Register() {
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [role, setRole]             = useState<UserRole>('driver');
  const [region, setRegion]         = useState<Region>('IE');
  const [plateNumber, setPlateNumber] = useState('');
  const [error, setError]           = useState('');
  const [loading, setLoading]       = useState(false);
  const { signUp } = useAuth();
  const navigate   = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signUp(email, password, role, region, role === 'driver' ? plateNumber : undefined);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10" style={{ background: 'var(--surface)' }}>
      <div className="w-full max-w-[460px] bg-white rounded-2xl p-8 shadow-sm border border-[var(--border)] animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--muted-foreground)] mb-6 tracking-widest uppercase">
          New Account
        </div>

        <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl mb-2">
          Register
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mb-8">Join the distributed traffic system</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm mb-2">Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required autoFocus autoComplete="email"
              className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all"
            />
          </div>

          <div>
            <label className="block text-sm mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required minLength={6} autoComplete="new-password"
              className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-2">Role</label>
              <select
                value={role}
                onChange={e => setRole(e.target.value as UserRole)}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all"
              >
                <option value="driver">Driver</option>
                <option value="enforcement">Enforcement Agent</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-2">Home Region</label>
              <select
                value={region}
                onChange={e => setRegion(e.target.value as Region)}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all"
              >
                <option value="IE">🇮🇪 Ireland</option>
                <option value="GB">🇬🇧 United Kingdom</option>
                <option value="FR">🇫🇷 France</option>
              </select>
            </div>
          </div>

          {role === 'driver' && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-300">
              <label className="block text-sm mb-2">Plate Number</label>
              <input
                type="text"
                value={plateNumber}
                onChange={e => setPlateNumber(e.target.value.toUpperCase())}
                style={{ fontFamily: 'var(--font-mono)' }}
                className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all uppercase"
                placeholder="241-D-12345"
                required
              />
            </div>
          )}

          {error && (
            <div className="text-sm text-[var(--red)] bg-red-50 px-4 py-3 rounded-lg">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}
            className="w-full bg-[var(--ink)] text-white py-3.5 rounded-[10px] hover:-translate-y-[1px] active:translate-y-0 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating account…
              </span>
            ) : 'Create account →'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--muted-foreground)]">
          Already registered?{' '}
          <Link to="/signin" className="text-[var(--accent)] font-semibold hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
