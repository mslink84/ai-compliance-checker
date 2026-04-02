"""
config.py – Central configuration for the AI Compliance Checker.

All tunable constants live here so they can be changed in one place
without touching business logic.
"""

# ── Document limits ───────────────────────────────────────────────────────────────

MAX_DOC_CHARS     = 14_000   # ~3 500 tokens — leaves room for prompts + full output
OVERLAP_CHARS     = 400      # overlap between chunks to avoid cutting mid-sentence
MAX_FILE_SIZE_MB  = 10       # file upload ceiling (bytes enforced in app.py)

# ── Rate limiting (per session / per day) ─────────────────────────────────────────

MAX_RUNS_PER_SESSION = 3     # maximum analyses a single browser session may run
MAX_RUNS_PER_DAY     = 3     # maximum analyses per calendar day (UTC)
COOLDOWN_SECONDS     = 30    # minimum seconds between consecutive analyses
MAX_HASH_HISTORY     = 5     # number of recent document hashes tracked (duplicate guard)
MAX_AUTH_ATTEMPTS    = 3     # wrong access-code attempts before session lockout

# ── AI model ──────────────────────────────────────────────────────────────────────

CLAUDE_MODEL      = "claude-sonnet-4-6"
MAX_OUTPUT_TOKENS = 8_000    # per API call; large enough for any single framework
API_TIMEOUT_S     = 60.0     # httpx connect + read timeout (streaming resets the read timer)
