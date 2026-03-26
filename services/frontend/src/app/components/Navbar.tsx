import { Link, useLocation } from 'react-router';
import { useAuth } from '../contexts/AuthContext';

export function Navbar() {
  const { user, signOut } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const navLinks = [
    { path: '/book',     label: 'BOOK',     roles: ['driver', 'admin'] },
    { path: '/journeys', label: 'JOURNEYS', roles: ['driver', 'admin'] },
    { path: '/verify',   label: 'VERIFY',   roles: ['enforcement', 'admin'] },
  ];

  const visibleLinks = navLinks.filter(link => link.roles.includes(user.role));

  return (
    <nav className="h-[60px] px-6 flex items-center justify-between" style={{ backgroundColor: 'var(--ink)' }}>
      <div className="flex items-center gap-2">
        <span className="text-[#ff3b3b]">●</span>
        <Link
          to={user.role === 'enforcement' ? '/verify' : '/journeys'}
          style={{ fontFamily: 'var(--font-display)', fontWeight: 800, letterSpacing: '-0.02em' }}
          className="text-white text-xl"
        >
          RoutePass
        </Link>
      </div>

      <div className="flex items-center gap-6">
        {visibleLinks.map(link => (
          <Link
            key={link.path}
            to={link.path}
            style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
            className={`text-xs uppercase tracking-wide transition-colors ${
              location.pathname === link.path ? 'text-white' : 'text-white/60 hover:text-white'
            }`}
          >
            {link.label}
          </Link>
        ))}

        <div className="w-[1px] h-5 bg-white/20" />

        <span style={{ fontFamily: 'var(--font-mono)' }} className="text-white/50 text-xs truncate max-w-[180px]">
          {user.email}
        </span>

        <button
          onClick={signOut}
          style={{ fontFamily: 'var(--font-display)', fontWeight: 600 }}
          className="text-xs uppercase tracking-wide text-white/60 hover:text-white px-3 py-1.5 rounded-full border border-white/20 hover:border-white/40 transition-all"
        >
          LOGOUT
        </button>
      </div>
    </nav>
  );
}
