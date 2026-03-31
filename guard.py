"""
guard.py – Anti-abuse and access protection for the AI Compliance Checker.

All state is stored in st.session_state (per-session, server-side).
No database required.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import date

import streamlit as st

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────────

MAX_RUNS_PER_SESSION  = 3
MAX_RUNS_PER_DAY      = 3
COOLDOWN_SECONDS      = 30
MAX_DOC_CHARS         = 100_000   # hard ceiling before analysis (~25k tokens)
MIN_DOC_CHARS         = 10        # reject empty / trivial documents
MAX_HASH_HISTORY      = 5         # number of recent doc hashes to track for duplicates
MAX_AUTH_ATTEMPTS     = 3         # wrong access codes before session is locked out


def _access_code() -> str:
    """
    Load the valid access code.
    Priority: st.secrets["ACCESS_CODE"] → env var ACCESS_CODE → built-in default.
    To change without touching code, set ACCESS_CODE in Streamlit Cloud secrets.
    """
    try:
        return st.secrets["ACCESS_CODE"]
    except Exception:
        return os.environ.get("ACCESS_CODE", "")


# ── Session state bootstrap ───────────────────────────────────────────────────────

def _init() -> None:
    defaults: dict = {
        "_g_authed":       False,   # access code passed
        "_g_auth_fails":   0,       # consecutive wrong access code attempts
        "_g_run_count":    0,       # total runs this session
        "_g_day":          None,    # ISO date string of current day
        "_g_day_count":    0,       # runs today
        "_g_last_ts":      0.0,     # timestamp of last successful run
        "_g_hashes":       [],      # md5 hashes of recently analysed documents
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Public API ────────────────────────────────────────────────────────────────────

def require_access_code() -> bool:
    """
    Render the access code gate.
    Returns True when the user is authenticated; False when not.
    Caller should call st.stop() on False.
    """
    _init()

    if st.session_state["_g_authed"]:
        return True

    st.title("AI Compliance Checker")

    # Hard lockout after too many wrong attempts
    if st.session_state["_g_auth_fails"] >= MAX_AUTH_ATTEMPTS:
        logger.warning("guard: session locked – too many failed attempts")
        st.error(
            "Too many incorrect attempts — this session is locked. "
            "Open a new browser tab to try again, or contact "
            "[Mikael Sundberg](https://www.msun.se) to request access."
        )
        return False

    st.markdown("Please enter the access code to continue.")
    code = st.text_input("Access code", type="password", key="_gate_input",
                         placeholder="Enter access code…")

    if st.button("Continue", key="_gate_btn"):
        if code == _access_code():
            st.session_state["_g_authed"] = True
            st.session_state["_g_auth_fails"] = 0
            logger.info("guard: access granted")
            st.rerun()
        else:
            st.session_state["_g_auth_fails"] += 1
            fails = st.session_state["_g_auth_fails"]
            remaining = MAX_AUTH_ATTEMPTS - fails
            logger.warning("guard: access denied – wrong code (attempt %d/%d)", fails, MAX_AUTH_ATTEMPTS)
            if remaining > 0:
                st.error(f"Incorrect access code. {remaining} attempt(s) remaining.")
            else:
                st.rerun()  # triggers the lockout message above

    return False


def check_request(document_text: str) -> tuple[bool, str]:
    """
    Validate a request before running analysis.

    Returns:
        (True, "")             – request is allowed
        (False, reason_str)    – request is blocked; reason is user-facing
    """
    _init()
    _refresh_daily_counter()

    stripped = document_text.strip()

    # ── Empty / trivial input ─────────────────────────────────────────────────────
    if len(stripped) < MIN_DOC_CHARS:
        logger.warning("guard: blocked – input too short (%d chars)", len(stripped))
        return False, "The document appears to be empty or too short to analyse."

    # ── Input too long ────────────────────────────────────────────────────────────
    if len(stripped) > MAX_DOC_CHARS:
        logger.warning("guard: blocked – input too long (%d chars)", len(stripped))
        return (
            False,
            f"Document exceeds the {MAX_DOC_CHARS:,}-character limit. "
            "Please split it into smaller files.",
        )

    # ── Cooldown ──────────────────────────────────────────────────────────────────
    elapsed = time.time() - st.session_state["_g_last_ts"]
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed) + 1
        logger.warning("guard: blocked – cooldown (%ds remaining)", remaining)
        return False, f"Please wait {remaining} seconds before running another analysis."

    # ── Session run limit ─────────────────────────────────────────────────────────
    if st.session_state["_g_run_count"] >= MAX_RUNS_PER_SESSION:
        logger.warning("guard: blocked – session run limit reached")
        return (
            False,
            f"Maximum of {MAX_RUNS_PER_SESSION} analyses per session reached. "
            "Start a new session to continue.",
        )

    # ── Daily run limit ───────────────────────────────────────────────────────────
    if st.session_state["_g_day_count"] >= MAX_RUNS_PER_DAY:
        logger.warning("guard: blocked – daily run limit reached")
        return (
            False,
            f"Daily limit of {MAX_RUNS_PER_DAY} analyses reached. "
            "Please come back tomorrow.",
        )

    # ── Duplicate / spam detection ────────────────────────────────────────────────
    doc_hash = _md5(stripped)
    if doc_hash in st.session_state["_g_hashes"]:
        logger.warning("guard: blocked – duplicate document submission")
        return (
            False,
            "This document has already been analysed in this session. "
            "Please upload a different document.",
        )

    return True, ""


def record_run(document_text: str) -> None:
    """Update counters after a successful analysis run."""
    _init()
    _refresh_daily_counter()

    doc_hash = _md5(document_text.strip())
    hashes: list = st.session_state["_g_hashes"]
    hashes.append(doc_hash)
    st.session_state["_g_hashes"]    = hashes[-MAX_HASH_HISTORY:]
    st.session_state["_g_run_count"] += 1
    st.session_state["_g_day_count"] += 1
    st.session_state["_g_last_ts"]   = time.time()

    logger.info(
        "guard: run recorded – session %d/%d, daily %d/%d",
        st.session_state["_g_run_count"], MAX_RUNS_PER_SESSION,
        st.session_state["_g_day_count"], MAX_RUNS_PER_DAY,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────────

def _refresh_daily_counter() -> None:
    today = date.today().isoformat()
    if st.session_state["_g_day"] != today:
        st.session_state["_g_day"]       = today
        st.session_state["_g_day_count"] = 0


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()
