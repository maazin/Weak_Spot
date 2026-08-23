import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { ErrorNote, Page, Spinner } from '../components/Chrome';

const FAMILY_LABEL = {
  pattern_selection: 'Pattern selection',
  implementation: 'Implementation',
  complexity: 'Complexity',
  comprehension: 'Comprehension',
};

function Section({ title, children, id }) {
  return (
    <section aria-labelledby={id} className="border-t border-hairline pt-7">
      <h2 id={id} className="eyebrow">
        {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

/** The submitted code with the cited lines marked by a rule and a tinted ground. */
function CodeWithEvidence({ code, spans }) {
  const lines = code.split('\n');
  const cited = new Set();
  spans.forEach((span) => {
    for (let n = span.start_line; n <= span.end_line; n += 1) cited.add(n);
  });

  return (
    <div className="overflow-hidden rounded border border-hairline bg-surface">
      <pre className="overflow-x-auto text-[13px] leading-[1.7]">
        <code className="block font-mono">
          {lines.map((line, index) => {
            const number = index + 1;
            const isCited = cited.has(number);
            return (
              <span
                key={number}
                className={[
                  'flex border-l-2',
                  isCited ? 'border-brass bg-brass/[0.07]' : 'border-transparent',
                ].join(' ')}
              >
                <span
                  aria-hidden="true"
                  className={[
                    'w-12 shrink-0 select-none px-2 text-right tabular-nums',
                    isCited ? 'font-semibold text-brass' : 'text-ink-3',
                  ].join(' ')}
                >
                  {number}
                </span>
                <span className="whitespace-pre px-3 text-ink">{line || ' '}</span>
              </span>
            );
          })}
        </code>
      </pre>
    </div>
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

  if (error)
    return (
      <Page>
        <ErrorNote>{error}</ErrorNote>
      </Page>
    );
  if (!data) return <Spinner label="Loading diagnosis" />;

  const { submission, diagnosis, recommendations } = data;

  if (!diagnosis) {
    return (
      <Page>
        <ErrorNote>This submission has no diagnosis recorded.</ErrorNote>
      </Page>
    );
  }

  const confidence = Math.round(diagnosis.confidence * 100);

  return (
    <Page>
      <header className="mb-9">
        <p className="eyebrow">
          {FAMILY_LABEL[diagnosis.pattern.family] ?? diagnosis.pattern.family}
        </p>
        <h1 className="mt-3 max-w-prose font-serif text-display font-semibold text-ink">
          {diagnosis.pattern.name}
        </h1>

        <p className="mt-4 text-caption text-ink-2">
          <a
            href={submission.problem.url}
            target="_blank"
            rel="noreferrer"
            className="link"
          >
            {submission.problem.title}
          </a>
          <span className="px-2 text-ink-3">/</span>
          reported {submission.failure_type.replace(/_/g, ' ')}
        </p>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <span className="chip tabular-nums">Confidence {confidence}%</span>
          <span className="chip">
            {diagnosis.verifier_passed ? 'Verified' : 'Unverified'}
          </span>
          {diagnosis.retry_count > 0 && <span className="chip">Escalated</span>}
        </div>

        {!diagnosis.verifier_passed && (
          <div className="mt-5">
            <ErrorNote tone="info">
              The verifier could not confirm this one. Read it as a suggestion and check
              the cited lines yourself.
            </ErrorNote>
          </div>
        )}
      </header>

      <div className="space-y-9">
        <Section id="gap" title="The gap">
          <p className="max-w-prose text-body text-ink">{diagnosis.explanation}</p>
        </Section>

        <Section id="shape" title="What the correct shape looks like">
          <p className="max-w-prose text-body text-ink-2">
            {diagnosis.pattern.correct_approach}
          </p>
        </Section>

        <Section id="evidence" title="Your code, with the cited lines marked">
          <CodeWithEvidence code={submission.code_text} spans={diagnosis.evidence_spans} />
          <ul className="mt-5 space-y-3">
            {diagnosis.evidence_spans.map((span, index) => (
              <li key={index} className="flex gap-3 text-caption">
                <span className="shrink-0 font-mono font-semibold text-brass tabular-nums">
                  {span.start_line}
                  {span.end_line !== span.start_line ? `-${span.end_line}` : ''}
                </span>
                <span className="max-w-prose text-ink-2">{span.why}</span>
              </li>
            ))}
          </ul>
        </Section>

        <Section id="practice" title="Practice these next">
          {recommendations.length === 0 ? (
            <p className="max-w-prose text-body text-ink-2">
              Nothing new to recommend. The close matches for this pattern are already
              queued or attempted.
            </p>
          ) : (
            <ul className="divide-y divide-hairline border-y border-hairline">
              {recommendations.map((problem) => (
                <li key={problem.id}>
                  <a
                    href={problem.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex min-h-11 items-center gap-4 py-4 transition-colors hover:bg-raised/60"
                  >
                    <span className="flex-1 text-body text-ink">{problem.title}</span>
                    <span className="chip capitalize">{problem.difficulty}</span>
                    <span className="text-micro text-ink-3">Opens on the source site</span>
                  </a>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-5 text-caption text-ink-2">
            These are in your{' '}
            <Link to="/reviews" className="link">
              review queue
            </Link>
            , first due in three days.
          </p>
        </Section>
      </div>
    </Page>
  );
}
