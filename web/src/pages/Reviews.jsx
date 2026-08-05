import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import { EmptyState, ErrorNote, Spinner } from '../components/Chrome';

const RESULTS = [
  ['solved', 'Solved'],
  ['failed', 'Failed'],
  ['skipped', 'Skip'],
];

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

  if (error && !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <ErrorNote>{error}</ErrorNote>
      </div>
    );
  }
  if (!data) return <Spinner label="Loading your queue…" />;

  // Two distinct empty states: nothing queued at all, versus a queue that is clear
  // for today.
  if (data.items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        {data.total_items === 0 ? (
          <EmptyState
            image="/assets/empty-done.png"
            alt=""
            title="Nothing queued yet"
          >
            Diagnose a failed attempt and its three recommended problems land here on a
            spaced schedule.
          </EmptyState>
        ) : (
          <EmptyState
            image="/assets/empty-queue.png"
            alt=""
            title="Nothing due today"
          >
            You have {data.total_items} problem{data.total_items === 1 ? '' : 's'} in the
            queue. The next one comes back around when its interval elapses.
          </EmptyState>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
          Due today
        </h1>
        <p className="text-xs text-muted">
          {data.items.length} of {data.total_items} queued
        </p>
      </div>

      <ErrorNote>{error}</ErrorNote>

      <ul className="space-y-3">
        {data.items.map((item) => (
          <li key={item.id} className="card">
            <div className="flex flex-wrap items-start gap-3">
              <div className="min-w-0 flex-1">
                <a
                  href={item.problem.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-zinc-100 hover:text-accent"
                >
                  {item.problem.title} ↗
                </a>
                <p className="mt-1 text-xs text-muted">
                  drilling <span className="text-zinc-400">{item.pattern_name}</span>
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <span className="tag capitalize">{item.problem.difficulty}</span>
                  <span className="tag">
                    interval {item.interval_days.toFixed(1)}d
                  </span>
                  <span className="tag">reps {item.repetitions}</span>
                </div>
              </div>

              <div className="flex gap-2">
                {RESULTS.map(([value, label]) => (
                  <button
                    key={value}
                    onClick={() => complete(item.id, value)}
                    disabled={pending === item.id}
                    className={value === 'solved' ? 'btn-primary' : 'btn-ghost'}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
