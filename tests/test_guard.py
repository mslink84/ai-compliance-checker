"""Tests for guard.py protection logic (without Streamlit context)."""

import hashlib
import time

import pytest


# ── Minimal session_state stub so guard.py can be imported outside Streamlit ─────

class _FakeSessionState(dict):
    pass


# Patch st.session_state before importing guard
import sys
from unittest.mock import MagicMock, patch

# Build a minimal streamlit mock
_st_mock = MagicMock()
_fake_ss = _FakeSessionState()
_st_mock.session_state = _fake_ss
sys.modules.setdefault("streamlit", _st_mock)

import guard  # noqa: E402 – must come after mock setup


def _reset():
    """Reset session state between tests."""
    _fake_ss.clear()
    guard._init()


# ── _init ─────────────────────────────────────────────────────────────────────────

def test_init_sets_defaults():
    _reset()
    assert _fake_ss["_g_authed"] is False
    assert _fake_ss["_g_run_count"] == 0
    assert _fake_ss["_g_day_count"] == 0
    assert _fake_ss["_g_hashes"] == []


def test_init_does_not_overwrite_existing_values():
    _reset()
    _fake_ss["_g_run_count"] = 2
    guard._init()
    assert _fake_ss["_g_run_count"] == 2


# ── check_request – empty / short input ───────────────────────────────────────────

def test_blocks_empty_input():
    _reset()
    ok, msg = guard.check_request("")
    assert not ok
    assert "empty" in msg.lower() or "short" in msg.lower()


def test_blocks_whitespace_input():
    _reset()
    ok, msg = guard.check_request("   \n\t  ")
    assert not ok


def test_blocks_input_below_min():
    _reset()
    ok, msg = guard.check_request("abc")
    assert not ok


# ── check_request – too long ──────────────────────────────────────────────────────

def test_blocks_input_over_max():
    _reset()
    big = "x" * (guard.MAX_DOC_CHARS + 1)
    ok, msg = guard.check_request(big)
    assert not ok
    assert "limit" in msg.lower() or "exceed" in msg.lower()


def test_allows_input_at_max():
    _reset()
    _fake_ss["_g_last_ts"] = 0.0  # no cooldown
    doc = "a" * guard.MAX_DOC_CHARS
    ok, _ = guard.check_request(doc)
    assert ok


# ── check_request – cooldown ──────────────────────────────────────────────────────

def test_blocks_within_cooldown():
    _reset()
    _fake_ss["_g_last_ts"] = time.time()   # just ran
    ok, msg = guard.check_request("a" * 100)
    assert not ok
    assert "wait" in msg.lower() or "seconds" in msg.lower()


def test_allows_after_cooldown():
    _reset()
    _fake_ss["_g_last_ts"] = time.time() - guard.COOLDOWN_SECONDS - 1
    ok, _ = guard.check_request("a" * 100)
    assert ok


# ── check_request – session / daily limits ────────────────────────────────────────

def test_blocks_when_session_limit_reached():
    _reset()
    _fake_ss["_g_run_count"] = guard.MAX_RUNS_PER_SESSION
    ok, msg = guard.check_request("a" * 100)
    assert not ok
    assert "session" in msg.lower()


def test_blocks_when_daily_limit_reached():
    _reset()
    from datetime import date
    _fake_ss["_g_day"]       = date.today().isoformat()
    _fake_ss["_g_day_count"] = guard.MAX_RUNS_PER_DAY
    ok, msg = guard.check_request("a" * 100)
    assert not ok
    assert "daily" in msg.lower() or "tomorrow" in msg.lower()


# ── check_request – duplicate detection ──────────────────────────────────────────

def test_blocks_duplicate_document():
    _reset()
    doc = "a" * 100
    doc_hash = hashlib.md5(doc.encode()).hexdigest()
    _fake_ss["_g_hashes"] = [doc_hash]
    ok, msg = guard.check_request(doc)
    assert not ok
    assert "already" in msg.lower() or "duplicate" in msg.lower()


def test_allows_different_document():
    _reset()
    _fake_ss["_g_hashes"] = [hashlib.md5(b"other doc").hexdigest()]
    ok, _ = guard.check_request("a" * 100)
    assert ok


# ── record_run ────────────────────────────────────────────────────────────────────

def test_record_run_increments_counters():
    _reset()
    from datetime import date
    _fake_ss["_g_day"] = date.today().isoformat()
    doc = "sample document " * 10
    guard.record_run(doc)
    assert _fake_ss["_g_run_count"] == 1
    assert _fake_ss["_g_day_count"] == 1
    assert len(_fake_ss["_g_hashes"]) == 1


def test_record_run_caps_hash_history():
    _reset()
    from datetime import date
    _fake_ss["_g_day"] = date.today().isoformat()
    for i in range(guard.MAX_HASH_HISTORY + 3):
        _fake_ss["_g_last_ts"] = 0.0  # bypass cooldown check in _init
        guard.record_run(f"document number {i} " * 10)
    assert len(_fake_ss["_g_hashes"]) == guard.MAX_HASH_HISTORY
