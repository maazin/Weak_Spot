import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { ErrorNote, Spinner } from '../components/Chrome';

const FAMILY_LABEL = {
  pattern_selection: 'Pattern selection',
  implementation: 'Implementation',
  complexity: 'Complexity',
  comprehension: 'Comprehension',
};

/** The user's own code with the evidence lines highlighted. */
function CodeWithEvidence({ code, spans }) {
  const lines = code.split('\n');
  const highlighted = new Set();
  spans.forEach((span) => {
    for (let n = span.start_line; n <= span.end_line; n += 1) highlighted.add(n);
  });

  return (
    <pre className="overflow-x-auto rounded-md border border-edge bg-bg p-0 text-[13px] leading-relaxed">
      <code className="block font-mono">
        {lines.map((line, index) => {
          const number = index + 1;
          const isEvidence = highlighted.has(number);
          return (
            <span
              key={number}
              className={`flex ${isEvidence ? 'bg-accent/10 border-l-2 border-accent' : 'border-l-2 border-transparent'}`}
            >
              <span className="w-12 shrink-0 select-none px-2 text-right text-muted">
                {number}
              </span>
              <span className="whitespace-pre px-2 text-zinc-200">{line || ' '}</span>
            </span>
          );
        })}
      </code>
    </pre>
  );
}

export default function Diagnosis() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getSubmission(id)
      .then((result) => !cancelled && setData(result))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) return <div className="mx-auto max-w-3xl px-4 py-8"><ErrorNote>{error}</ErrorNote></div>;
  if (!data) return <Spinner label="Loading diagnosis…" />;

  const { submission, diagnosis, recommendations } = data;

  if (!diagnosis) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <ErrorNote>This submission has no diagnosis yet.</ErrorNote>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded bg-accent/15 px-2 py-0.5 font-medium text-accent">
            {FAMILY_LABEL[diagnosis.pattern.family] ?? diagnosis.pattern.family}
          </span>
          <span className="text-muted">
            confidence {(diagnosis.confidence * 100).toFixed(0)}%
          </span>
          {!diagnosis.verifier_passed && (
            <span className="rounded border border-amber-800 px-2 py-0.5 text-amber-500">
              unverified
            </span>
          )}
        </div>
        <h1 className="text-xl font-semibold leading-snug tracking-tight text-zinc-50">
          {diagnosis.pattern.name}
        </h1>
        <p className="mt-1 text-xs text-muted">
          on{' '}
          <a
            href={submission.problem.url}
            target="_blank"
            rel="noreferrer"
            className="text-zinc-400 underline decoration-edge hover:text-accent"
          >
            {submission.problem.title}
          </a>{' '}
          · reported {submission.failure_type.replace(/_/g, ' ')}
        </p>
      </div>

      <div className="card">
        <h2 className="label">The gap</h2>
        <p className="text-sm leading-relaxed text-zinc-300">{diagnosis.explanation}</p>
      </div>

      <div className="card">
        <h2 className="label">What the correct shape looks like</h2>
        <p className="text-sm leading-relaxed text-zinc-400">
          {diagnosis.pattern.correct_approach}
        </p>
      </div>

      <div>
        <h2 className="label">Your code, with the evidence highlighted</h2>
        <CodeWithEvidence
          code={submission.code_text}
          spans={diagnosis.evidence_spans}
        />
        <ul className="mt-3 space-y-1.5">
          {diagnosis.evidence_spans.map((span, index) => (
            <li key={index} className="text-xs text-zinc-400">
              <span className="mr-2 font-mono text-accent">
                L{span.start_line}
                {span.end_line !== span.start_line ? `–${span.end_line}` : ''}
              </span>
              {span.why}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="label">Practice these three</h2>
        {recommendations.length === 0 ? (
          <p className="text-sm text-muted">
            No new problems to recommend — you have already queued or attempted the close
            matches for this pattern.
          </p>
        ) : (
          <ul className="space-y-2">
            {recommendations.map((problem) => (
              <li key={problem.id}>
                <a
                  href={problem.url}
                  target="_blank"
                  rel="noreferrer"
                  className="card flex items-center gap-3 hover:border-accent/60"
                >
                  <span className="flex-1 text-sm text-zinc-200">{problem.title}</span>
                  <span className="tag capitalize">{problem.difficulty}</span>
                  <span className="text-xs text-muted">↗</span>
                </a>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-xs text-muted">
          These are now in your{' '}
          <Link to="/reviews" className="text-zinc-400 underline hover:text-accent">
            review queue
          </Link>
          , first due in three days.
        </p>
      </div>
    </div>
  );
}
