"""Real driver cancellation and CPU deadlines must never return partial answers."""

import time
from threading import Event, Timer
from unittest.mock import patch

import pytest
from sqlalchemy import text

from reality.services.analytics.execution import AnalyticsError, execute


@pytest.mark.parametrize("cancel", [False, True])
def test_inflight_database_work_is_cancelled(cancel):
    stopped = Event()
    timer = Timer(0.1, stopped.set) if cancel else None

    def slow(session, tenant_id, arguments):
        session.execute(text("SELECT pg_sleep(5)"))
        return {"metadata": {}}

    started = time.monotonic()
    if timer:
        timer.start()
    try:
        with (
            patch("reality.services.analytics.execution.query", slow),
            pytest.raises(AnalyticsError) as error,
        ):
            execute(
                "unused",
                {},
                cancellation=stopped,
                timeout_seconds=2 if cancel else 0.1,
            )
        assert error.value.code == ("query_cancelled" if cancel else "query_timeout")
        assert time.monotonic() - started < 3
    finally:
        if timer:
            timer.cancel()
            timer.join()


def test_cpu_result_after_deadline_is_rejected():
    def slow(session, tenant_id, arguments):
        time.sleep(0.15)
        return {"metadata": {}}

    with (
        patch("reality.services.analytics.execution.query", slow),
        pytest.raises(AnalyticsError) as error,
    ):
        execute("unused", {}, timeout_seconds=0.05)
    assert error.value.code == "query_timeout"
