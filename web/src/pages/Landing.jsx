import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { ErrorNote } from '../components/Chrome';

/**
 * Landing + auth. hero.png leaves its left two-thirds empty by design, so the headline
 * and CTA are laid over that region rather than baked into the image.
 */
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
          ? 'Local sign-in is disabled. Use GitHub, or set DEV_AUTH_BYPASS=true.'
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="mx-auto max-w-5xl px-4 py-6">
        <img
          src="/assets/logo-horizontal-dark.png"
          alt="Weakspot"
          className="h-8 w-auto"
        />
      </header>

      <main className="relative mx-auto max-w-5xl px-4">
        <div className="relative overflow-hidden rounded-xl border border-edge">
          <img
            src="/assets/hero.png"
            alt=""
            className="h-auto w-full"
            width="1600"
            height="900"
          />
          <div className="absolute inset-y-0 left-0 flex w-full flex-col justify-center gap-5 p-6 sm:w-2/3 sm:p-10">
            <h1 className="max-w-md text-2xl font-semibold leading-tight tracking-tight text-zinc-50 sm:text-4xl">
              Find out why you actually failed.
            </h1>
            <p className="max-w-sm text-sm text-zinc-300 sm:text-base">
              Weakspot names the conceptual gap behind a failed attempt, quotes the lines
              in your own code that show it, and queues three problems that drill the same
              pattern until it sticks.
            </p>
            <div className="flex flex-col items-start gap-3">
              <a href={api.githubLoginUrl()} className="btn-primary">
                Continue with GitHub
              </a>
              <button onClick={devLogin} disabled={busy} className="btn-ghost">
                {busy ? 'Signing in…' : 'Continue without an account (local dev)'}
              </button>
            </div>
            <div className="max-w-sm">
              <ErrorNote>{error}</ErrorNote>
            </div>
          </div>
        </div>

        <section className="my-12 grid gap-4 sm:grid-cols-3">
          {[
            {
              title: 'One named failure mode',
              body: 'From a closed taxonomy of 50, across pattern selection, implementation, complexity, and comprehension.',
            },
            {
              title: 'Evidence from your code',
              body: 'The specific lines that demonstrate the gap, quoted back with a reason. Never a solution.',
            },
            {
              title: 'Spaced practice',
              body: 'Three same-pattern problems on an SM-2 schedule, so the mistake stops recurring.',
            },
          ].map((item) => (
            <div key={item.title} className="card">
              <h2 className="mb-1.5 text-sm font-medium text-accent">{item.title}</h2>
              <p className="text-sm leading-relaxed text-zinc-400">{item.body}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}

/** Sign-in screen: stacked lockup centred above the GitHub button, per spec. */
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
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <img
        src="/assets/logo-stacked-dark.png"
        alt="Weakspot"
        className="w-40 max-w-full"
      />
      <a href={api.githubLoginUrl()} className="btn-primary">
        Continue with GitHub
      </a>
      <button onClick={devLogin} className="text-xs text-muted hover:text-zinc-300">
        Local dev sign-in
      </button>
      <ErrorNote>{error}</ErrorNote>
    </div>
  );
}
