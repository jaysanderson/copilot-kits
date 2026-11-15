"""Deploy this app to Fly with its own commit baked in, then prove the live service reports that commit.

    python server/scripts/deploy.py [--app semanticsite] [--url https://your-app.fly.dev]

Refuses to deploy a dirty tree or a commit that is not on origin/main (nothing lives local-only). The commit is passed to the image build
as GIT_SHA and read back from /api/health after the deploy; the script exits non-zero if the live service does not report it.
"""
import argparse, json, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--app", default="semanticsite")
ap.add_argument("--url", default="https://your-app.fly.dev")
a = ap.parse_args()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


sha = git("rev-parse", "HEAD")
dirty = git("status", "--porcelain", "--untracked-files=no")
if dirty:
    sys.exit("refusing to deploy: tracked files have uncommitted changes:\n" + dirty)
remote = git("ls-remote", "origin", "main").split()[0]
if remote != sha:
    sys.exit(f"refusing to deploy: HEAD {sha} is not origin/main {remote}. Push first.")
print("deploying", sha, flush=True)
r = subprocess.run(["flyctl", "deploy", "-a", a.app, "--ha=false", "--build-arg", f"GIT_SHA={sha}"], cwd=ROOT)
if r.returncode:
    sys.exit(r.returncode)
live = None
for _ in range(30):
    try:
        live = json.load(urllib.request.urlopen(a.url + "/api/health", timeout=10)).get("commit")
        if live == sha:
            break
    except Exception:
        pass
    time.sleep(3)
print("live /api/health commit:", live)
if live != sha:
    sys.exit(f"FAIL: the live service reports {live}, not {sha}")
print("PASS: the live service reports the commit that was deployed")
