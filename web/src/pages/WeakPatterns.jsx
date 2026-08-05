import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { EmptyState, ErrorNote, Spinner } from '../components/Chrome';

const FAMILY_LABEL = {
  pattern_selection: 'Pattern selection',
  implementation: 'Implementation',
  complexity: 'Complexity',
  comprehension: 'Comprehension',
};

/** Trend arrows are the only chart in the product, by design. */
function Trend({ direction }) {
  const config = {
    up: { glyph: '▲', className: 'text-red-400', title: 'more often lately' },
    down: { glyph: '▼', className: 'text-emerald-400', title: 'less often lately' },
    flat: { glyph: '—', className: 'text-muted', title: 'unchanged' },
  }[direction] ?? { glyph: '—', className: 'text-muted', title: '' };

  return (
    <span className={`text-xs ${config.className}`} title={config.title}>
      {config.glyph}
    </span>
  );
}

export default function WeakPatterns() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .weakPatterns()
      .then((data) => setItems(data.items))
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <ErrorNote>{error}</ErrorNote>
      </div>
    );
  }
  if (!items) return <Spinner label="Loading your profile…" />;

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <EmptyState image="/assets/empty-done.png" alt="" title="No patterns yet">
          Once you have diagnosed a few failed attempts, the failure modes you keep
          repeating show up here, ranked.
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
          Weak patterns
        </h1>
        <p className="text-xs text-muted">
          Ranked by how often each has been diagnosed. The arrow compares the last 30
          days against the 30 before.
        </p>
      </div>

      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.pattern.id} className="card">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 w-8 shrink-0 text-right font-mono text-sm text-accent">
                {item.occurrences}×
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-medium text-zinc-100">
                    {item.pattern.name}
                  </h2>
                  <Trend direction={item.trend} />
                </div>
                <p className="mt-1 text-xs text-muted">
                  {FAMILY_LABEL[item.pattern.family] ?? item.pattern.family} · last seen{' '}
                  {new Date(item.last_seen_at).toLocaleDateString()}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-zinc-400">
                  {item.pattern.correct_approach}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {item.pattern.practice_tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
