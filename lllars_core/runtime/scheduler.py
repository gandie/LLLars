from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Event, Thread
import re
from typing import Any, Callable

_SCHEDULE_PATTERN = re.compile(r"^every:(\d+)([smhd])$")
_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_interval_schedule(schedule: str) -> timedelta:
    raw = schedule.strip()
    match = _SCHEDULE_PATTERN.fullmatch(raw)
    if match is None:
        raise ValueError("schedule must match 'every:<int><unit>'")

    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        raise ValueError("schedule interval must be greater than zero")

    seconds = amount * _UNIT_SECONDS[unit]
    return timedelta(seconds=seconds)


def next_scheduled_time(schedule: str, *, now: datetime) -> datetime:
    return now + parse_interval_schedule(schedule)


@dataclass
class RuntimeScheduler:
    list_jobs: Callable[[], list[Any]]
    is_job_active: Callable[[str], bool]
    start_job: Callable[[str], None]
    poll_interval_sec: float = 0.5
    _stop: Event = field(default_factory=Event)
    _thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(
            target=self._run_loop,
            name="runtime-scheduler-loop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run_loop(self) -> None:
        while not self._stop.wait(self.poll_interval_sec):
            self.promote_due_jobs(now=datetime.now())

    def promote_due_jobs(self, *, now: datetime) -> None:
        for record in self.list_jobs():
            if not self._is_due(record, now=now):
                continue
            if self.is_job_active(record.job_id):
                continue
            self.start_job(record.job_id)

    @staticmethod
    def _is_due(record: Any, *, now: datetime) -> bool:
        return (
            record.status == "queued"
            and record.next_run_at is not None
            and record.next_run_at <= now
        )


__all__ = [
    "RuntimeScheduler",
    "next_scheduled_time",
    "parse_interval_schedule",
]
