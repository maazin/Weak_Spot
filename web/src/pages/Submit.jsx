import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { EmptyState, ErrorNote, Spinner } from '../components/Chrome';

const LANGUAGES = [
  ['python', 'Python'],
  ['java', 'Java'],
  ['cpp', 'C++'],
  ['javascript', 'JavaScript'],
  ['go', 'Go'],
];

const FAILURES = [
  ['wrong_answer', 'Wrong answer'],
  ['tle', 'Time limit exceeded'],
  ['mle', 'Memory limit exceeded'],
  ['runtime_error', 'Runtime error'],
  ['gave_up', 'Gave up'],
  ['looked_at_solution', 'Looked at the solution'],
];

export default function Submit() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    problem_slug: '',
    code: '',
    language: 'python',
    failure_type: 'wrong_answer',
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const untouched = !form.problem_slug && !form.code;

  function update(key) {
    return (event) => setForm((f) => ({ ...f, [key]: event.target.value }));
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.createSubmission(form);
      navigate(`/diagnosis/${result.submission_id}`);
    } catch (e) {
      setError(
        e.status === 429
          ? 'You have used all 10 free diagnoses for today. The limit resets at midnight UTC.'
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }

  if (busy) return <Spinner label="Diagnosing your attempt…" />;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {untouched && (
        <EmptyState
          image="/assets/empty-submit.png"
          alt=""
          title="Paste a failed attempt"
        >
          Weakspot works on attempts that did not pass. Tell it which problem, what your
          code was, and what happened.
        </EmptyState>
      )}

      <form onSubmit={submit} className="card space-y-5">
        <div>
          <label className="label" htmlFor="slug">
            Problem slug or URL
          </label>
          <input
            id="slug"
            className="field"
            placeholder="two-sum, or https://leetcode.com/problems/two-sum/"
            value={form.problem_slug}
            onChange={update('problem_slug')}
            required
          />
        </div>

        <div>
          <label className="label" htmlFor="code">
            Your failing code
          </label>
          <textarea
            id="code"
            className="field min-h-[280px] font-mono text-[13px] leading-relaxed"
            placeholder="Paste the attempt exactly as you wrote it."
            value={form.code}
            onChange={update('code')}
            required
          />
          <p className="mt-1.5 text-xs text-muted">
            Up to 32KB and 800 lines. Comments and strings are stripped before the model
            sees your code.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="language">
              Language
            </label>
            <select
              id="language"
              className="field"
              value={form.language}
              onChange={update('language')}
            >
              {LANGUAGES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label" htmlFor="failure">
              What happened
            </label>
            <select
              id="failure"
              className="field"
              value={form.failure_type}
              onChange={update('failure_type')}
            >
              {FAILURES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <ErrorNote>{error}</ErrorNote>

        <button type="submit" className="btn-primary w-full" disabled={busy}>
          Diagnose
        </button>
      </form>
    </div>
  );
}
