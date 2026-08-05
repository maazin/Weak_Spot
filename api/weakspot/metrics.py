"""Prometheus metrics — where the numbers in the README come from.

Alert conditions from spec section 9 are expressed as recording-friendly series:
verifier rejection rate over a rolling hour, p95 latency, and cost per diagnosis against
the trailing week's median.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from sqlalchemy import text

from .db import engine

REGISTRY = CollectorRegistry()

diagnoses_total = Counter(
    "weakspot_diagnoses_total",
    "Diagnoses produced, by model tier and verifier outcome.",
    ["model_tier", "verifier_passed"],
    registry=REGISTRY,
)

verifier_rejections_total = Counter(
    "weakspot_verifier_rejections_total",
    "Verifier rejections by failed check.",
    ["check"],
    registry=REGISTRY,
)

cache_hits_total = Counter(
    "weakspot_cache_hits_total",
    "Diagnosis outcomes served from the code_hash cache.",
    registry=REGISTRY,
)

prompt_cache_reads_total = Counter(
    "weakspot_prompt_cache_reads_total",
    "Prompt-cache read tokens, the primary cost lever.",
    ["model"],
    registry=REGISTRY,
)

diagnosis_latency_ms = Histogram(
    "weakspot_diagnosis_latency_ms",
    "End-to-end diagnosis latency in milliseconds.",
    buckets=(250, 500, 1000, 2000, 3000, 4000, 6000, 8000, 10000, 20000),
    registry=REGISTRY,
)

diagnosis_cost_usd = Histogram(
    "weakspot_diagnosis_cost_usd",
    "Cost per diagnosis in USD.",
    buckets=(0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.25),
    registry=REGISTRY,
)

rate_limited_total = Counter(
    "weakspot_rate_limited_total",
    "Submissions refused because the daily quota was exhausted.",
    registry=REGISTRY,
)

# Rolling aggregates, refreshed from Postgres when /metrics is scraped.
verifier_rejection_rate_1h = Gauge(
    "weakspot_verifier_rejection_rate_1h",
    "Share of diagnoses rejected by the verifier over the last hour.",
    registry=REGISTRY,
)
latency_quantile_ms = Gauge(
    "weakspot_latency_quantile_ms",
    "Diagnosis latency quantiles over the last 24 hours.",
    ["quantile"],
    registry=REGISTRY,
)
cost_per_diagnosis_usd = Gauge(
    "weakspot_cost_per_diagnosis_usd",
    "Cost per diagnosis, recent mean and trailing-week median.",
    ["window"],
    registry=REGISTRY,
)


def record_diagnosis(
    *,
    model_tier: str,
    verifier_passed: bool,
    latency_ms: int,
    cost_usd: float,
    failed_checks: list[str],
) -> None:
    diagnoses_total.labels(
        model_tier=model_tier, verifier_passed=str(verifier_passed).lower()
    ).inc()
    diagnosis_latency_ms.observe(latency_ms)
    diagnosis_cost_usd.observe(cost_usd)
    for check in failed_checks:
        verifier_rejections_total.labels(check=check).inc()


def refresh_rolling_aggregates() -> None:
    """Recompute the gauges the alert conditions are written against."""
    try:
        with engine.connect() as conn:
            rate = conn.execute(
                text(
                    """
                    SELECT COALESCE(
                        AVG(CASE WHEN verifier_passed THEN 0.0 ELSE 1.0 END), 0.0)
                      FROM diagnoses
                     WHERE created_at > NOW() - INTERVAL '1 hour'
                    """
                )
            ).scalar_one()
            verifier_rejection_rate_1h.set(float(rate or 0.0))

            row = conn.execute(
                text(
                    """
                    SELECT
                      PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms),
                      PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms),
                      PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms)
                      FROM diagnoses
                     WHERE created_at > NOW() - INTERVAL '24 hours'
                    """
                )
            ).fetchone()
            if row:
                for quantile, value in zip(("p50", "p95", "p99"), row, strict=True):
                    latency_quantile_ms.labels(quantile=quantile).set(float(value or 0))

            recent_mean = conn.execute(
                text(
                    """
                    SELECT COALESCE(AVG(cost_usd), 0.0) FROM diagnoses
                     WHERE created_at > NOW() - INTERVAL '1 hour'
                    """
                )
            ).scalar_one()
            week_median = conn.execute(
                text(
                    """
                    SELECT COALESCE(
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cost_usd), 0.0)
                      FROM diagnoses
                     WHERE created_at > NOW() - INTERVAL '7 days'
                    """
                )
            ).scalar_one()
            cost_per_diagnosis_usd.labels(window="1h_mean").set(float(recent_mean or 0))
            cost_per_diagnosis_usd.labels(window="7d_median").set(float(week_median or 0))
    except Exception:
        # /metrics must not 500 because the database is briefly unavailable.
        pass


def render() -> bytes:
    refresh_rolling_aggregates()
    return generate_latest(REGISTRY)
