import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '../contexts/AuthContext';

export function SignIn() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const { signIn } = useAuth();
  const navigate   = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signIn(email, password);
      // Root.tsx will redirect based on role — navigate to / and let it decide
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--surface)' }}>
      <div className="w-full max-w-[460px] bg-white rounded-2xl p-8 shadow-sm border border-[var(--border)] animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div style={{ fontFamily: 'var(--font-mono)' }} className="text-xs text-[var(--muted-foreground)] mb-6 tracking-widest uppercase">
          CS7NS6 Distributed Systems
        </div>

        <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800 }} className="text-3xl mb-2">
          Sign in
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mb-8">Access the traffic booking system</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm mb-2">Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoFocus
              required
              autoComplete="email"
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
              required
              autoComplete="current-password"
              className="w-full px-4 py-3 bg-white border border-[var(--border)] rounded-[10px] focus:outline-none focus:border-[var(--accent)] focus:ring-[3px] focus:ring-[var(--ring)] transition-all"
            />
          </div>

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
                Signing in…
              </span>
            ) : 'Sign in →'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--muted-foreground)]">
          No account?{' '}
          <Link to="/register" className="text-[var(--accent)] font-semibold hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
