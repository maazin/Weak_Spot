import { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

const LINKS = [
  { to: '/submit', label: 'Submit' },
  { to: '/reviews', label: 'Review queue' },
  { to: '/patterns', label: 'Weak patterns' },
];

/* ------------------------------------------------------------------ appearance */

/**
 * Three states rather than a boolean, so "follow the system" stays reachable after
 * someone has made a manual choice. The control is labelled in words, since a sun or
 * moon glyph carries no meaning to a screen reader.
 */
export function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem('weakspot-theme') || 'system');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', theme);
    localStorage.setItem('weakspot-theme', theme);
  }, [theme]);

  const next = { system: 'light', light: 'dark', dark: 'system' }[theme];
  const label = { system: 'Auto', light: 'Light', dark: 'Dark' }[theme];

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      className="btn-quiet text-micro font-medium tabular-nums"
      aria-label={`Appearance is ${label.toLowerCase()}. Switch to ${next}.`}
    >
      {label}
    </button>
  );
}

/* ------------------------------------------------------------------ navigation */

export function Nav({ user, onSignOut }) {
  const navigate = useNavigate();

  async function signOut() {
    await api.logout();
    onSignOut?.();
    navigate('/');
  }

  return (
    <header className="sticky top-0 z-20 border-b border-hairline bg-canvas/90 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-5xl items-center gap-2 px-4 sm:px-6">
        <NavLink
          to="/submit"
          className="flex shrink-0 items-center gap-2.5 pr-3"
          aria-label="Weakspot home"
        >
          <img src="/assets/mark.svg" alt="" width="24" height="24" />
          <span className="hidden font-serif text-[15px] font-semibold tracking-tight text-ink sm:block">
            Weakspot
          </span>
        </NavLink>

        <nav aria-label="Primary" className="flex items-center gap-1">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                [
                  'flex min-h-11 items-center rounded px-3 text-caption transition-colors',
                  // Fill and weight carry the active state, so it survives without colour.
                  isActive
                    ? 'bg-raised font-semibold text-ink'
                    : 'font-medium text-ink-2 hover:bg-raised/60 hover:text-ink',
                ].join(' ')
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          {user && (
            <>
              <span className="hidden px-2 text-micro text-ink-2 sm:block">{user.handle}</span>
              <button type="button" onClick={signOut} className="btn-quiet text-micro">
                Sign out
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

/* ------------------------------------------------------------------ page shell */

export function Page({ children, width = 'default' }) {
  const max = width === 'wide' ? 'max-w-5xl' : 'max-w-3xl';
  return <main className={`mx-auto ${max} px-4 py-10 sm:px-6 sm:py-14`}>{children}</main>;
}

export function PageHeader({ title, children, aside }) {
  return (
    <header className="mb-9 flex flex-wrap items-end justify-between gap-4 border-b border-hairline pb-5">
      <div>
        <h1 className="font-serif text-display font-semibold text-ink">{title}</h1>
        {children && <p className="mt-2 max-w-prose text-body text-ink-2">{children}</p>}
      </div>
      {aside}
    </header>
  );
}

/* ------------------------------------------------------------------ states */

/**
 * Typographic rather than illustrated. The supplied empty-state PNGs carry a dark
 * ground baked into the file, so on the light canvas they render as a black rectangle.
 * A rule and a heading state the same thing and hold up in both appearances.
 */
export function EmptyState({ title, children, action }) {
  return (
    <div className="border-y border-hairline px-6 py-20 text-center">
      <h2 className="font-serif text-title font-semibold text-ink">{title}</h2>
      {children && (
        <p className="mx-auto mt-3 max-w-prose text-body text-ink-2">{children}</p>
      )}
      {action && <div className="mt-7">{action}</div>}
    </div>
  );
}

export function Spinner({ label }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center gap-5 py-28 text-caption text-ink-2"
    >
      <span aria-hidden="true" className="sweep" />
      {label}
    </div>
  );
}

export function ErrorNote({ children, tone = 'error' }) {
  if (!children) return null;
  const isError = tone === 'error';
  return (
    <p
      role={isError ? 'alert' : undefined}
      className={[
        'flex items-start gap-2.5 rounded border px-3.5 py-3 text-caption',
        isError ? 'border-oxblood/40 bg-oxblood/10' : 'border-hairline bg-raised',
      ].join(' ')}
    >
      {/* A word as well as a colour, so the state reads without colour vision. */}
      <span className={`shrink-0 font-semibold ${isError ? 'text-oxblood' : 'text-ink-2'}`}>
        {isError ? 'Error' : 'Note'}
      </span>
      <span className="text-ink">{children}</span>
    </p>
  );
}
