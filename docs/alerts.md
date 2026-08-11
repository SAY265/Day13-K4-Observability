# Alert runbook

Alerts are based on user-visible symptoms and the SLOs in `config/slo.yaml`.
For every alert, follow the evidence path: metrics -> Langfuse trace -> JSON log.

## Alert 1

- Name: `high_latency_p95`
- Severity: warning
- Related SLI/SLO: `latency_p95_ms <= 3000`, target 99.5% over 28 days
- Trigger: P95 latency is above 3000 ms continuously for 5 minutes
- User impact: users wait longer for an answer or experience a timeout
- First checks:
  1. Check `/metrics` and confirm the P95 value and start time.
  2. Open a slow Langfuse trace and inspect the `run` span duration.
  3. Match the trace correlation ID to `response_sent` in `data/logs.jsonl`.
- Temporary mitigation: reduce concurrency or disable the affected optional feature; keep the service available while investigating.
- Owner: on-call-engineer

## Alert 2

- Name: `elevated_error_rate`
- Severity: critical
- Related SLI/SLO: `error_rate_pct <= 2`, target 99.0% over 28 days
- Trigger: error rate is above 5% continuously for 3 minutes
- User impact: requests fail or users receive no usable answer
- First checks:
  1. Check `/metrics` for the error rate and `error_breakdown`.
  2. Open a failed Langfuse trace and identify the failed span or status.
  3. Search `data/logs.jsonl` for the same correlation ID and `request_failed` event.
- Temporary mitigation: disable the failing feature or route traffic to the known-good prompt/model; preserve logs and traces.
- Owner: on-call-engineer

## Alert 3

- Name: `cost_budget_exceeded`
- Severity: warning
- Related SLI/SLO: `daily_cost_usd <= 2.5`, target 100% over 28 days
- Trigger: accumulated daily cost is above 2.5 USD
- User impact: the service may need throttling, reduced model usage, or temporary unavailability.
- First checks:
  1. Check `/metrics` for total and average cost and the time of the increase.
  2. Inspect recent Langfuse traces for unusual token counts or model usage.
  3. Match those traces to `tokens_in`, `tokens_out`, and `cost_usd` in `data/logs.jsonl`.
- Temporary mitigation: rate-limit non-critical traffic and switch to the configured lower-cost path until the cause is fixed.
- Owner: team-lead

## Escalation and closure

Record the alert start/end time, metric value, trace ID, correlation ID, root cause,
mitigation, and follow-up action in the incident report. Close an alert only after
the metric is back within its SLO for the required observation window.
