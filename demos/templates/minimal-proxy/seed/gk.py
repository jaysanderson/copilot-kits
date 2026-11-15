import os, httpx
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
KB_URL = os.environ["KB_URL"].rstrip("/")
H = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {os.environ['KB_TOKEN']}", "Content-Type": "application/json", "X-Synchronous": "true"}
def c(): return httpx.Client(headers=H, timeout=60)
