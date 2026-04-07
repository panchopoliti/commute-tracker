"""Trigger the GitHub Actions workflow via API. Runs as a Railway cron job."""

import os
import sys

import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "panchopoliti/commute-tracker"
WORKFLOW = "track_commute.yml"

if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN not set")
    sys.exit(1)

resp = requests.post(
    f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
    json={"ref": "main"},
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    timeout=30,
)

if resp.status_code == 204:
    print("Workflow triggered successfully")
else:
    print(f"ERROR: {resp.status_code} - {resp.text}")
    sys.exit(1)
