#!/usr/bin/env python3
"""
retro_git_committer.py

Distributes the currently **staged-but-uncommitted** files evenly across the
previous 364 days, building one commit per file and back-dating each commit.

Default behaviour is **dry-run**:   it *prints* the commands it would have run.
Add  --execute   to actually invoke git.
"""
from __future__ import annotations
import argparse, datetime as dt, math, subprocess, sys
from pathlib import Path
from typing import List

DAY_COUNT = 364   # how far back to spread commits (1 year minus today)

def staged_files() -> List[str]:
    """
    Return a list of files that are added (staged) but not yet committed.

    Uses:  git diff --name-only --cached
    """
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"],
        text=True,
    )
    files = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return files

def git_root() -> Path:
    """Determine repo root (raises if not in a repo)."""
    root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
    return Path(root)

def make_commit_cmd(path: str, commit_date: dt.datetime) -> List[str]:
    """Build the git commit command for one file and one date."""
    date_arg = commit_date.strftime("%Y-%m-%d %H:%M:%S")
    return [
        "git", "commit",
        "--date", f'"{date_arg}"',          # author & committer date
        "-m", f'"Add {path}"',
        "--", path,
    ]

def schedule_dates(n_files: int) -> List[dt.datetime]:
    """
    Generate a list of commit-dates (len == n_files) spread as evenly
    as possible over the past DAY_COUNT days.
    """
    today = dt.datetime.now()
    dates: List[dt.datetime] = []
    # integer bucketing based on cumulative ratio
    for day in range(DAY_COUNT):
        commit_count_until_today = round((day + 1) * n_files / DAY_COUNT)
        commit_count_before      = round( day       * n_files / DAY_COUNT)
        commits_today = commit_count_until_today - commit_count_before
        for _ in range(commits_today):
            dates.append(today - dt.timedelta(days=day))
    return dates

def main():
    parser = argparse.ArgumentParser(
        description="Back-date commits for staged files."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run git commands instead of just printing them."
    )
    args = parser.parse_args()

    # Ensure we're inside a repo
    try:
        repo_root = git_root()
    except subprocess.CalledProcessError:
        sys.exit("Error: not inside a git repository.")

    files = staged_files()
    if not files:
        sys.exit("No staged files to commit.")

    dates = schedule_dates(len(files))
    assert len(dates) == len(files)

    # Walk files, pairing with the pre-computed dates
    for path, commit_date in zip(files, dates):
        cmd = make_commit_cmd(path, commit_date)
        cmd_str = " ".join(cmd)
        if args.execute:
            subprocess.run(cmd, check=True)
        else:
            print(cmd_str)

if __name__ == "__main__":
    main()
