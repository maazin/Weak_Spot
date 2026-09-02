import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { ErrorNote, Page, PageHeader, Spinner } from '../components/Chrome';

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

const MAX_LINES = 800;

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

  const lineCount = form.code ? form.code.split('\n').length : 0;
  const overLimit = lineCount > MAX_LINES;

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
          ? 'All 10 free diagnoses for today have been used. The limit resets at midnight UTC.'
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }

  if (busy) return <Spinner label="Reading your attempt" />;

  return (
    <Page>
      <PageHeader title="Submit an attempt">
        Weakspot works on attempts that did not pass. Give it the problem, the code you
        wrote, and what the judge said.
      </PageHeader>

      <form onSubmit={submit} className="space-y-7" noValidate>
        <div>
          <label className="label" htmlFor="slug">
            Problem
          </label>
          <input
            id="slug"
            className="field"
            placeholder="two-sum, or a full problem URL"
            value={form.problem_slug}
            onChange={update('problem_slug')}
            autoComplete="off"
            spellCheck="false"
            required
            aria-describedby="slug-hint"
          />
          <p className="hint" id="slug-hint">
            A slug or a link. Weakspot stores the title, difficulty, and tags, never the
            problem statement.
          </p>
        </div>

        <div>
          <div className="flex items-baseline justify-between gap-3">
            <label className="label" htmlFor="code">
              Your failing code
            </label>
            {lineCount > 0 && (
              <span
                className={`text-micro tabular-nums ${overLimit ? 'font-semibold text-oxblood' : 'text-ink-2'}`}
              >
                {lineCount} / {MAX_LINES} lines
              </span>
            )}
          </div>
          <textarea
            id="code"
            className="field min-h-[22rem] resize-y font-mono text-[13px] leading-[1.7]"
            placeholder="Paste the attempt exactly as you wrote it."
            value={form.code}
            onChange={update('code')}
            spellCheck="false"
            required
            aria-describedby="code-hint"
            aria-invalid={overLimit || undefined}
          />
          <p className="hint" id="code-hint">
            Up to 32KB. Comments and string literals are replaced with placeholders
            before the model reads any of it.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
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

        <div className="flex flex-wrap items-center gap-4 border-t border-hairline pt-6">
          <button type="submit" className="btn-primary" disabled={busy || overLimit}>
            Diagnose
          </button>
          <span className="text-micro text-ink-2">10 free diagnoses per day.</span>
        </div>
      </form>
    </Page>
  );
}
