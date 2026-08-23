import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import { EmptyState, ErrorNote, Page, PageHeader, Spinner } from '../components/Chrome';

export default function Reviews() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(null);

  const load = useCallback(() => {
    api
      .dueReviews()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  useEffect(load, [load]);

  async function complete(id, result) {
    setPending(id);
    setError(null);
    try {
      await api.completeReview(id, result);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setPending(null);
    }
  }

  if (error && !data)
    return (
      <Page>
        <ErrorNote>{error}</ErrorNote>
      </Page>
    );
  if (!data) return <Spinner label="Loading your queue" />;

  // Two distinct empty states: nothing queued at all, against a queue clear for today.
  if (data.items.length === 0) {
    return (
      <Page>
        {data.total_items === 0 ? (
          <EmptyState title="Nothing queued yet">
            Diagnose a failed attempt and the problems it recommends arrive here on a
            spaced schedule.
          </EmptyState>
        ) : (
          <EmptyState title="Nothing due today">
            {data.total_items} problem{data.total_items === 1 ? '' : 's'} remain in the
            queue. Each returns when its interval elapses.
          </EmptyState>
        )}
      </Page>
    );
  }

  return (
    <Page>
      <PageHeader
        title="Due today"
        aside={
          <span className="text-caption tabular-nums text-ink-2">
            {data.items.length} of {data.total_items} queued
          </span>
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}

      <ul className="divide-y divide-hairline border-y border-hairline">
        {data.items.map((item) => {
          const busy = pending === item.id;
          return (
            <li key={item.id} className="py-6">
              <div className="flex flex-wrap items-start justify-between gap-5">
                <div className="min-w-0 flex-1">
                  <a
                    href={item.problem.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-lead font-medium text-ink underline decoration-hairline decoration-1 underline-offset-[3px] hover:decoration-brass"
                  >
                    {item.problem.title}
                  </a>
                  <p className="mt-1.5 text-caption text-ink-2">
                    Drilling {item.pattern_name}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <span className="chip capitalize">{item.problem.difficulty}</span>
                    <span className="chip tabular-nums">
                      Interval {item.interval_days.toFixed(1)}d
                    </span>
                    <span className="chip tabular-nums">
                      {item.repetitions} rep{item.repetitions === 1 ? '' : 's'}
                    </span>
                  </div>
                </div>

                <fieldset className="flex shrink-0 items-center gap-2" disabled={busy}>
                  <legend className="sr-only">
                    Result for {item.problem.title}
                  </legend>
                  <button
                    type="button"
                    onClick={() => complete(item.id, 'solved')}
                    className="btn-primary"
                  >
                    Solved
                  </button>
                  <button
                    type="button"
                    onClick={() => complete(item.id, 'failed')}
                    className="btn-secondary"
                  >
                    Failed
                  </button>
                  <button
                    type="button"
                    onClick={() => complete(item.id, 'skipped')}
                    className="btn-quiet"
                  >
                    Skip
                  </button>
                </fieldset>
              </div>
            </li>
          );
        })}
      </ul>
    </Page>
  );
}
