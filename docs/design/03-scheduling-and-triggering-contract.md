# Scheduling and Triggering Contract

This chapter documents currently shipped scheduling and triggering behavior.
Submit requests without scheduling fields still execute immediately.

## Lifecycle Terms
- submitted: Request accepted by API or CLI and materialized as `JobSpec`.
- queued: Job registered and waiting for execution.
- running: Job is currently executing.
- terminal: One of `succeeded`, `failed`, or `canceled`.

Scheduling/triggering terms:
- immediate: submit-now flow where no `run_at` or `schedule` is provided.
- timed: one-shot delayed execution at `run_at`.
- scheduled: policy-driven execution described by `schedule`.
- trigger source: origin hint captured as `trigger_source`.

## JobSpec Contract Fields
- `deadline_at` (optional): latest acceptable execution time.
- `run_at` (optional): one-shot planned execution time.
- `schedule` (optional): opaque strategy selector/expression string.
- `trigger_source` (required with default): origin marker; values: `submit`,
  `scheduled`, `manual`, `api`, `retry`, `external`.

Datetime format policy:
- `deadline_at` and `run_at` are naive ISO datetime strings
  (`YYYY-MM-DDTHH:MM:SS`).
- Timezone/offset notation is out of scope for this runtime contract and is
  rejected.

## Strategy-First Direction
- `schedule` is intentionally strategy-oriented, not cron-oriented.
- Current accepted grammar is interval-based: `every:<int><unit>` where unit is
  one of `s`, `m`, `h`, `d`.
- A cron-style strategy may exist later, but it is not the primary path.
- External signals are first-class scheduling inputs via `trigger_source`.

Example target pattern:
- `schedule = "carbon-aware"`
- `deadline_at = "2026-07-25T23:59:59"`
- `trigger_source = "external"` where an external carbon-awareness signal
  chooses the actual run window before deadline.

## Contract Invariants
- `run_at` and `schedule` are mutually exclusive.
- If both `run_at` and `deadline_at` are provided, `run_at <= deadline_at`.
- If `schedule` is provided, `trigger_source` must be `scheduled`.
- If `trigger_source` is `scheduled`, at least one of `run_at` or `schedule`
  must be present.

## Immediate-Submit Compatibility
- Existing submit payloads that only include `prompt`, `run`, `timeout_sec`,
  and `config_path` remain valid.
- Runtime execution path remains submit-now unless `run_at` or `schedule` is
  provided.
- Runtime includes explicit trigger routes for queued jobs: `GET /jobs` (queue
  visibility) and `POST /jobs/{job_id}/trigger` (manual or caller-selected
  trigger source).
- Trigger route defaults are intentionally minimal: `trigger_source =
  "manual"`, `trigger_payload_ref = null`.

## Operator Flows (End-to-End)
- Immediate submit:
  - Submit without `run_at` and `schedule`.
  - Job transitions `queued -> running -> terminal`.
- Timed submit:
  - Submit with `run_at`.
  - Job stays `queued` until scheduler promotion at or after `run_at`.
- Recurring submit:
  - Submit with `schedule` and `trigger_source = "scheduled"`.
  - Each cycle runs, then requeues with updated `next_run_at` and incremented
    `run_count`.
- Manual trigger:
  - Submit a queued job (for example a future `run_at`).
  - Call `POST /jobs/{job_id}/trigger`.
  - Trigger metadata is recorded as manual by default unless explicitly
    overridden.

## Failure Modes and Recovery
- Validation failure (`422`):
  - Causes: timezone-aware datetimes, invalid schedule grammar, mutually
    exclusive `run_at` + `schedule`, or invalid scheduled-trigger pairing.
  - Recovery: correct payload and resubmit.
- Invalid trigger state (`409`):
  - Cause: trigger called for non-queued job.
  - Recovery: use `GET /jobs` or `GET /jobs/{job_id}` to confirm queued state,
    then trigger.
- Unknown job (`404`):
  - Cause: unknown `job_id`.
  - Recovery: resubmit and use returned `job_id`.
- Operator timeout during smoke run:
  - Recovery: inspect `GET /jobs/{job_id}` and `GET /jobs/{job_id}/logs`, then
    choose trigger (queued jobs) or resubmit.

## Smoke Scenarios
- Immediate: expect terminal `succeeded` with test payload return code `0`.
- Timed: expect queued visibility before terminal completion after due-time
  promotion.
- Recurring: expect a requeued state with `run_count >= 1` and non-null
  `next_run_at`.
- Manual trigger: expect queued job to start after `POST /jobs/{job_id}/trigger`
  and preserve trigger metadata.
