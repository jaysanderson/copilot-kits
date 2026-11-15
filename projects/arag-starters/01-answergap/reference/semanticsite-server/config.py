"""Runtime configuration. Secrets come from the app's own .env only (hard rule 5)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = Path(__file__).resolve().parent


def _load_env():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.split(" #")[0].strip())


_load_env()

ARAG_HOST = os.environ.get("ARAG_HOST", "")          # data-plane base; Progress documents https://<zone>.dp.progress.cloud/api/v1
KB_ID = os.environ.get("KB_ID", "")
KB_TOKEN = os.environ.get("KB_TOKEN", "")
KB_URL = f"{ARAG_HOST}/kb/{KB_ID}" if ARAG_HOST and KB_ID else ""

# Cheapest capable generative tier (hard rule 15). Pinned on every generative call.
MODEL = os.environ.get("SS_MODEL", "gemini-3.1-flash-lite")

DATA_DIR = Path(os.environ.get("SS_DATA_DIR", str(SERVER / "var")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "semanticsite.db"

# Crawler identity and politeness. These are shipping gates, not preferences.
PUBLIC_URL = os.environ.get("SS_PUBLIC_URL", "https://your-app.fly.dev")
BOT_TOKEN = "SemanticSiteBot"
USER_AGENT = f"{BOT_TOKEN}/0.1 (+{PUBLIC_URL}/bot; polite website structuring crawler)"
MIN_DELAY_S = 1.0          # floor between requests to one host; robots Crawl-delay can only raise it
FETCH_TIMEOUT_S = 15.0
MAX_BYTES = 2_000_000
MAX_TEXT_CHARS = 60_000
HARD_MAX_PAGES = 500       # PRD MVP capacity
DEFAULT_MAX_PAGES = 100
ASK_WORKERS = 4

# Optional operator-supplied price assumption (USD per million MODEL tokens, not Progress Agentic RAG consumption tokens) used ONLY to show an
# estimated dollar figure beside the measured model token count. Unset by default: no price is invented.
PRICE_IN_PER_M = float(os.environ.get("SS_PRICE_IN_PER_M", "0") or 0)
PRICE_OUT_PER_M = float(os.environ.get("SS_PRICE_OUT_PER_M", "0") or 0)

# Extraction depth: 1 = a single structured call per page; 2 adds a recall pass that re-reads the page for
# relationships the first pass missed. Both are measured; see the cost and evaluation output.
EXTRACT_PASSES = int(os.environ.get("SS_EXTRACT_PASSES", "2"))

# Public-deployment guards. A crawler that fetches any address a stranger types is an SSRF vector and a cost
# vector, so private ranges are refused by default and runs are capped. Local development sets SS_ALLOW_PRIVATE_HOSTS=1.
ALLOW_PRIVATE_HOSTS = os.environ.get("SS_ALLOW_PRIVATE_HOSTS", "") == "1"
MAX_PAGES_CAP = int(os.environ.get("SS_MAX_PAGES_CAP", str(HARD_MAX_PAGES)))
MAX_CONCURRENT_RUNS = int(os.environ.get("SS_MAX_CONCURRENT_RUNS", "3"))
HOURLY_PAGE_BUDGET = int(os.environ.get("SS_HOURLY_PAGE_BUDGET", "300"))
# Routes that start a crawl, spend a model call or change review state need this key in X-SemanticSite-Key.
# Unset means those routes refuse everyone, unless SS_ALLOW_OPEN=1 (local development only).
QUESTIONS_PER_VISITOR_HOUR = int(os.environ.get("SS_QUESTIONS_PER_VISITOR_HOUR", "8"))
QUESTION_HOURLY_CEILING = int(os.environ.get("SS_QUESTION_HOURLY_CEILING", "150"))
ACCESS_KEY = os.environ.get("SS_ACCESS_KEY", "")
BUILD_COMMIT = os.environ.get("SS_BUILD_COMMIT", "unknown")      # baked into the image at build time, never read from a file
ALLOW_OPEN = os.environ.get("SS_ALLOW_OPEN", "") == "1"
