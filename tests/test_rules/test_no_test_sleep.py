from __future__ import annotations

from anti_slop.engine import analyze_source
from anti_slop.rules.no_test_sleep import NoTestSleepRule


def test_time_sleep_flagged():
    code = """
import time

def test_async_work():
    trigger()
    time.sleep(1)
    assert check() is True
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTestSleepRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP028"
    assert diags[0].rule_id == "no-test-sleep"
    assert "time.sleep" in diags[0].message


def test_asyncio_sleep_flagged():
    code = """
import asyncio

async def test_async_coro():
    await asyncio.sleep(0.5)
    assert True
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTestSleepRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP028"
    assert "asyncio.sleep" in diags[0].message


def test_custom_sleep_on_fake_clock_flagged():
    code = """
def test_clock(fake_clock):
    fake_clock.sleep(10)
"""
    diags = analyze_source(code, filename="test_service.py", rules=[NoTestSleepRule])
    assert len(diags) == 1
    assert diags[0].code == "SLOP028"


def test_production_file_ignored():
    code = """
import time

def rate_limiter():
    time.sleep(1)
"""
    diags = analyze_source(code, filename="service.py", rules=[NoTestSleepRule])
    assert len(diags) == 0
