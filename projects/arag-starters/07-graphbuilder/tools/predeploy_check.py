"""Pre-deploy check: import the app from a directory holding ONLY what the Dockerfile copies.

Why: `flyctl deploy` builds from the Dockerfile's explicit COPY list. A module that exists in the
working directory but not in that list imports fine locally and crashes the container at start, taking
every route down (it did, once). Run this from a clean checkout of the commit you are about to deploy.

  python predeploy_check.py            # must print "subset import ok", exit 0
  python predeploy_check.py --control  # plants a missing module, must FAIL (proves the check can fail)
"""
import re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent


def copy_list():
    files = []
    for line in (HERE / "Dockerfile").read_text().splitlines():
        m = re.match(r"COPY\s+(.+?)\s+(\S+)$", line.strip())
        if m and m.group(1) != "requirements.txt":
            files += [(src, m.group(2)) for src in m.group(1).split()]
    return files


def build(tmp: Path, drop: str = ""):
    for src, dst in copy_list():
        if src == drop:
            continue
        s = HERE / src
        d = tmp / (src if dst.endswith("/") is False and dst in (".", "./") else dst)
        if dst in (".", "./"):
            d = tmp / src
        elif dst.endswith("/"):
            d = tmp / dst / Path(src).name
        else:
            d = tmp / dst
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(s, d) if s.is_dir() else shutil.copy(s, d)


def run(drop: str = "") -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        build(tmp, drop)
        env = {"KB_URL": "http://x", "KB_TOKEN": "t", "INSIGHTS_DB": str(tmp / "i.db"), "PATH": "/usr/bin:/bin"}
        r = subprocess.run([sys.executable, "-c", "import app;print('subset import ok')"], cwd=tmp, env=env,
                           capture_output=True, text=True)
        print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "no output")
        return r.returncode


if __name__ == "__main__":
    if "--control" in sys.argv:
        rc = run(drop="answers.py")
        print("control (answers.py removed) exit", rc, "- expected non-zero")
        sys.exit(0 if rc != 0 else 1)
    sys.exit(run())
