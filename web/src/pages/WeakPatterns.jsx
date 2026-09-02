import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { EmptyState, ErrorNote, Page, PageHeader, Spinner } from '../components/Chrome';

const FAMILY_LABEL = {
  pattern_selection: 'Pattern selection',
  implementation: 'Implementation',
  complexity: 'Complexity',
  comprehension: 'Comprehension',
};

/**
 * Direction is carried by a word as well as a colour, so the reading survives without
 * colour vision. This remains the only chart in the product, by design.
 */
function Trend({ direction }) {
  const config =
    {
      up: { label: 'Rising', className: 'text-oxblood' },
      down: { label: 'Easing', className: 'text-forest' },
      flat: { label: 'Steady', className: 'text-ink-2' },
    }[direction] ?? { label: 'Steady', className: 'text-ink-2' };

  return (
    <span className={`text-micro font-semibold uppercase tracking-[0.06em] ${config.className}`}>
      {config.label}
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

  if (error)
    return (
      <Page>
        <ErrorNote>{error}</ErrorNote>
      </Page>
    );
  if (!items) return <Spinner label="Loading your profile" />;

  if (items.length === 0) {
    return (
      <Page>
        <EmptyState title="No patterns yet">
          Once a few failed attempts have been diagnosed, the failure modes that keep
          recurring appear here, ranked by frequency.
        </EmptyState>
      </Page>
    );
  }

  return (
    <Page>
      <PageHeader title="Weak patterns">
        Ranked by how often each has been diagnosed. The trend compares the last 30 days
        against the 30 before them.
      </PageHeader>

      <ol className="divide-y divide-hairline border-y border-hairline">
        {items.map((item) => (
          <li key={item.pattern.id} className="grid gap-4 py-7 sm:grid-cols-[4.5rem,1fr] sm:gap-7">
            <div className="flex items-baseline gap-2 sm:block">
              <span className="font-serif text-title font-semibold text-ink tabular-nums">
                {item.occurrences}
              </span>
              <span className="text-micro text-ink-2 sm:mt-1 sm:block">
                time{item.occurrences === 1 ? '' : 's'}
              </span>
            </div>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <h2 className="text-lead font-medium text-ink">{item.pattern.name}</h2>
                <Trend direction={item.trend} />
              </div>
              <p className="mt-1.5 text-micro text-ink-2">
                {FAMILY_LABEL[item.pattern.family] ?? item.pattern.family}
                <span className="px-2 text-ink-3">/</span>
                last seen {new Date(item.last_seen_at).toLocaleDateString()}
              </p>
              <p className="mt-3 max-w-prose text-body text-ink-2">
                {item.pattern.correct_approach}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {item.pattern.practice_tags.map((tag) => (
                  <span key={tag} className="chip">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </Page>
  );
}
