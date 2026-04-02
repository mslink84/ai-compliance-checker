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

from config import (
    MAX_RUNS_PER_SESSION, MAX_RUNS_PER_DAY, COOLDOWN_SECONDS,
    MAX_HASH_HISTORY, MAX_AUTH_ATTEMPTS,
)
from translations import t

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────────
# Values imported from config.py

MAX_DOC_CHARS = 100_000   # hard ceiling before analysis (~25k tokens) — guard-specific
MIN_DOC_CHARS = 10        # reject empty / trivial documents


def _access_code() -> str:
    """
    Load the valid access code.
    Priority: st.secrets["ACCESS_CODE"] → env var ACCESS_CODE → empty string.
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

    # Hard lockout after too many wrong attempts
    if st.session_state["_g_auth_fails"] >= MAX_AUTH_ATTEMPTS:
        logger.warning("guard: session locked – too many failed attempts")
        st.error(t("gate_locked"))
        return False

    st.markdown(t("gate_prompt"))
    code = st.text_input(
        t("gate_input_label"),
        type="password",
        key="_gate_input",
        placeholder="••••••••",
    )

    if st.button(t("gate_btn"), key="_gate_btn"):
        valid_code = _access_code()
        if not valid_code:
            st.error(t("gate_not_configured"))
            return False
        if code == valid_code:
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
                st.error(t("gate_wrong_n", n=remaining))
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
    # MD5 used for non-cryptographic duplicate detection only
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()
