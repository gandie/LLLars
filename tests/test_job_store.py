from __future__ import annotations

import threading
import unittest
from datetime import datetime

from lllars_core.job_store import InMemoryJobStore, InvalidTransitionError
from lllars_core.runtime.models import JobSpec, RunResult


def _job_spec(prompt: str = "hello") -> JobSpec:
    return JobSpec(
        prompt=prompt,
        run={
            "model": "test-model",
            "provider_url": "http://localhost:11434",
            "project_root": ".",
            "command_profile": "none",
        },
    )


def _scheduled_job_spec(schedule: str = "every:1m") -> JobSpec:
    return JobSpec(
        prompt="scheduled",
        run={
            "model": "test-model",
            "provider_url": "http://localhost:11434",
            "project_root": ".",
            "command_profile": "none",
        },
        schedule=schedule,
        trigger_source="scheduled",
    )


def _ok_result() -> RunResult:
    return RunResult(
        success=True,
        agent_returncode=0,
        elapsed_sec=0.01,
        agent_stdout="ok",
        agent_stderr="",
    )


def _run_cancel_success_race(
    store: InMemoryJobStore,
    job_id: str,
) -> list[Exception]:
    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def do_cancel() -> None:
        barrier.wait()
        try:
            store.cancel(job_id)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def do_success() -> None:
        barrier.wait()
        try:
            store.update(job_id, status="succeeded", result=_ok_result())
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    cancel_thread = threading.Thread(target=do_cancel)
    success_thread = threading.Thread(target=do_success)
    cancel_thread.start()
    success_thread.start()
    cancel_thread.join()
    success_thread.join()
    return errors


class InMemoryJobStoreTests(unittest.TestCase):
    def test_create_get_list_primitives(self) -> None:
        store = InMemoryJobStore()
        created = store.create(_job_spec(), job_id="job-1")

        self.assertEqual(created.job_id, "job-1")
        self.assertEqual(created.status, "queued")
        self.assertEqual(created.trigger_source, "submit")
        self.assertIsNone(created.trigger_payload_ref)

        fetched = store.get("job-1")
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.job_id, "job-1")

        listed = store.list()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].job_id, "job-1")

    def test_invalid_transition_cannot_skip_state(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")

        with self.assertRaises(InvalidTransitionError):
            store.update("job-1", status="succeeded", result=_ok_result())

    def test_valid_running_to_succeeded_transition(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")
        store.update("job-1", status="running")

        finished = store.update(
            "job-1",
            status="succeeded",
            result=_ok_result(),
            artifacts={"summary": "artifacts/job-1/summary.json"},
        )
        self.assertEqual(finished.status, "succeeded")
        self.assertEqual(
            finished.artifacts["summary"],
            "artifacts/job-1/summary.json",
        )

    def test_cancel_is_idempotent_for_terminal_states(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")

        first = store.cancel("job-1")
        second = store.cancel("job-1")

        self.assertEqual(first.status, "canceled")
        self.assertEqual(second.status, "canceled")

    def test_cancel_race_with_success_transition(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")
        store.update("job-1", status="running")

        errors = _run_cancel_success_race(store, "job-1")
        self.assertEqual(errors, [])

        final_record = store.get("job-1")
        self.assertIsNotNone(final_record)
        assert final_record is not None
        self.assertIn(final_record.status, {"succeeded", "canceled"})

        if final_record.status == "succeeded":
            self.assertIsNotNone(final_record.result)
            self.assertIsNone(final_record.error)
        if final_record.status == "canceled":
            self.assertIsNone(final_record.result)
            self.assertIsNotNone(final_record.error)

    def test_create_persists_schedule_next_run_metadata(self) -> None:
        store = InMemoryJobStore()
        next_run_at = datetime(2030, 1, 1, 10, 0, 0)
        created = store.create(
            _scheduled_job_spec(),
            job_id="job-sched",
            next_run_at=next_run_at,
        )

        self.assertEqual(created.next_run_at, next_run_at)
        status = created.as_status()
        self.assertEqual(status.schedule, "every:1m")
        self.assertEqual(status.next_run_at, next_run_at)
        self.assertEqual(status.run_count, 0)

    def test_mark_running_sets_last_run_and_increments_count(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")

        started_at = datetime(2030, 1, 1, 10, 5, 0)
        record = store.mark_running("job-1", started_at=started_at)

        self.assertEqual(record.status, "running")
        self.assertEqual(record.last_run_at, started_at)
        self.assertEqual(record.run_count, 1)

    def test_reschedule_recurring_returns_job_to_queued(self) -> None:
        store = InMemoryJobStore()
        store.create(_scheduled_job_spec(), job_id="job-1")
        store.mark_running("job-1", started_at=datetime(2030, 1, 1, 8, 0, 0))
        store.update("job-1", status="failed", error=None)

        next_run_at = datetime(2030, 1, 1, 9, 0, 0)
        record = store.reschedule_recurring("job-1", next_run_at=next_run_at)

        self.assertEqual(record.status, "queued")
        self.assertEqual(record.next_run_at, next_run_at)
        self.assertIsNone(record.result)
        self.assertIsNone(record.error)

    def test_update_can_override_trigger_metadata(self) -> None:
        store = InMemoryJobStore()
        store.create(_job_spec(), job_id="job-1")

        updated = store.update(
            "job-1",
            trigger_source="external",
            trigger_payload_ref="evt-1",
        )
        self.assertEqual(updated.trigger_source, "external")
        self.assertEqual(updated.trigger_payload_ref, "evt-1")

        cleared = store.update("job-1", trigger_payload_ref=None)
        self.assertEqual(cleared.trigger_source, "external")
        self.assertIsNone(cleared.trigger_payload_ref)


if __name__ == "__main__":
    unittest.main()
