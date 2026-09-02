import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { ErrorNote, ThemeToggle } from '../components/Chrome';

/**
 * Landing and sign-in.
 *
 * The headline sits on a solid panel rather than directly over hero.png. Text laid on
 * an image inherits whatever contrast that image happens to have, and a solid ground
 * keeps the copy at a fixed ratio in both appearances.
 */
const STEPS = [
  {
    n: '01',
    title: 'Name the failure',
    body: 'One conceptual failure mode drawn from a closed taxonomy of 51, across pattern selection, implementation, complexity, and comprehension.',
  },
  {
    n: '02',
    title: 'Show the evidence',
    body: 'The lines in your own submission that demonstrate the gap, quoted back with a reason for each. A working solution is never returned.',
  },
  {
    n: '03',
    title: 'Drill it until it holds',
    body: 'Three problems that exercise the same pattern, scheduled on spaced intervals so the mistake has to be unlearned rather than noted.',
  },
];

export default function Landing({ onSignedIn }) {
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function devLogin() {
    setBusy(true);
    setError(null);
    try {
      const user = await api.devLogin();
      onSignedIn?.(user);
      navigate('/submit');
    } catch (e) {
      setError(
        e.status === 404
          ? 'Local sign-in is switched off. Use GitHub, or set DEV_AUTH_BYPASS=true.'
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2.5">
          <img src="/assets/mark.svg" alt="" width="24" height="24" />
          <span className="font-serif text-[15px] font-semibold tracking-tight text-ink">
            Weakspot
          </span>
        </div>
        <ThemeToggle />
      </header>

      <main className="mx-auto max-w-5xl px-4 sm:px-6">
        <section className="grid items-center gap-10 border-b border-hairline py-14 sm:py-20 lg:grid-cols-[7fr,5fr] lg:gap-16">
          <div>
            <p className="eyebrow">Diagnosis for failed attempts</p>
            <h1 className="mt-4 font-serif text-[2rem] font-semibold text-ink sm:text-hero">
              Find out why you actually failed.
            </h1>
            <p className="mt-5 max-w-prose text-lead text-ink-2">
              Weakspot names the conceptual gap behind an attempt that did not pass,
              quotes the lines in your code that show it, and queues problems that
              exercise the same pattern.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href={api.githubLoginUrl()} className="btn-primary">
                Continue with GitHub
              </a>
              <button type="button" onClick={devLogin} disabled={busy} className="btn-secondary">
                {busy ? 'Signing in' : 'Continue without an account'}
              </button>
            </div>

            <div className="mt-5 max-w-prose">
              <ErrorNote>{error}</ErrorNote>
            </div>
          </div>

          {/* hero.png was composed with its left two-thirds empty for an overlay, so the
              frame is pinned right to keep the subject inside the panel. */}
          <div className="hidden overflow-hidden rounded border border-hairline bg-raised lg:block">
            <img
              src="/assets/hero.png"
              alt=""
              className="aspect-[4/3] w-full object-cover object-right"
              width="1600"
              height="900"
            />
          </div>
        </section>

        <section aria-labelledby="how" className="py-14 sm:py-20">
          <h2 id="how" className="eyebrow">
            How it works
          </h2>
          <ol className="mt-8">
            {STEPS.map((step) => (
              <li
                key={step.n}
                className="grid gap-3 border-t border-hairline py-7 sm:grid-cols-[4rem,14rem,1fr] sm:gap-8"
              >
                <span className="font-serif text-title font-semibold text-brass tabular-nums">
                  {step.n}
                </span>
                <h3 className="text-body font-semibold text-ink">{step.title}</h3>
                <p className="max-w-prose text-body text-ink-2">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-hairline">
        <p className="mx-auto max-w-5xl px-4 py-8 text-micro text-ink-2 sm:px-6">
          Problem statements stay on the sites that own them. Weakspot stores titles,
          difficulty, tags, and a link.
        </p>
      </footer>
    </div>
  );
}

/** Sign-in on its own, using the stacked lockup. */
export function SignIn({ onSignedIn }) {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  async function devLogin() {
    try {
      const user = await api.devLogin();
      onSignedIn?.(user);
      navigate('/submit');
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-7 px-4">
      <img src="/assets/logo-stacked-dark.png" alt="Weakspot" className="w-36 max-w-full" />
      <a href={api.githubLoginUrl()} className="btn-primary">
        Continue with GitHub
      </a>
      <button type="button" onClick={devLogin} className="btn-quiet text-micro">
        Local sign-in
      </button>
      <div className="max-w-prose">
        <ErrorNote>{error}</ErrorNote>
      </div>
    </div>
  );
}
