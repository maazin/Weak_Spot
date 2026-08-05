import { NavLink, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

const LINKS = [
  { to: '/submit', label: 'Submit' },
  { to: '/reviews', label: 'Review queue' },
  { to: '/patterns', label: 'Weak patterns' },
];

/** Nav uses the mark at 30px, not the wordmark lockup — too wide at this height. */
export function Nav({ user, onSignOut }) {
  const navigate = useNavigate();

  async function signOut() {
    await api.logout();
    onSignOut?.();
    navigate('/');
  }

  return (
    <header className="border-b border-edge">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <NavLink to="/submit" className="flex items-center gap-2">
          <img src="/assets/mark.svg" alt="Weakspot" width="30" height="30" />
          <span className="text-sm font-semibold tracking-tight text-zinc-100">
            Weakspot
          </span>
        </NavLink>

        <nav className="flex items-center gap-1 text-sm">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded px-2.5 py-1.5 transition-colors ${
                  isActive ? 'bg-surface text-accent' : 'text-zinc-400 hover:text-zinc-100'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {user && (
          <div className="ml-auto flex items-center gap-3 text-xs text-muted">
            <span>{user.handle}</span>
            <button onClick={signOut} className="hover:text-zinc-200">
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export function EmptyState({ image, alt, title, children }) {
  return (
    <div className="flex flex-col items-center py-12 text-center">
      <img src={image} alt={alt} className="mb-6 w-56 max-w-full opacity-90" />
      <h2 className="text-base font-medium text-zinc-200">{title}</h2>
      {children && <div className="mt-2 max-w-md text-sm text-muted">{children}</div>}
    </div>
  );
}

export function Spinner({ label }) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-sm text-muted">
      <img
        src="/assets/mark.svg"
        alt=""
        width="32"
        height="32"
        className="animate-pulse"
      />
      {label}
    </div>
  );
}

export function ErrorNote({ children }) {
  if (!children) return null;
  return (
    <p className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300">
      {children}
    </p>
  );
}
