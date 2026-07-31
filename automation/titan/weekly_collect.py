#!/usr/bin/env python3
"""
Titan-side weekly experiment collector.

Runs ON TITAN (weekly cron, e.g. Thursday night) where it can see your
experiment outputs. It scans a results directory, extracts the week's metrics
and plots into a single Markdown report, and pushes that report to a git repo
the Friday generator reads (TITAN_REPORT_REPO in automation/README.md).

This file is deliberately a TEMPLATE: the one part only you can write is how to
pull a metric out of YOUR results. Everything around it — the week window, the
Markdown assembly, the git commit/push — is done for you. Look for the two
`ADAPT:` blocks below and fill them in.

Usage:
    python weekly_collect.py \
        --results-dir /data/chris/experiments \
        --report-repo /data/chris/weekly-reports   # a local clone that has a remote

Cron (run `crontab -e` on Titan), every Thursday at 20:00:
    0 20 * * 4 cd /home/chris/automation && /usr/bin/python3 weekly_collect.py \
        --results-dir /data/chris/experiments \
        --report-repo /data/chris/weekly-reports >> collect.log 2>&1
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=7)
ISO_YEAR, ISO_WEEK, _ = TODAY.isocalendar()
WEEK_TAG = f"{ISO_YEAR}-W{ISO_WEEK:02d}"


def sh(cmd: list[str], cwd: str | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def modified_this_week(path: Path) -> bool:
    try:
        mtime = dt.date.fromtimestamp(path.stat().st_mtime)
        return mtime >= SINCE
    except OSError:
        return False


def collect_metrics(results_dir: Path) -> list[str]:
    """
    ADAPT (1/2): turn your experiment outputs into human-readable metric lines.

    The default below finds JSON files modified in the last week and prints a few
    top-level numeric keys from each — a reasonable start if you log metrics as
    JSON (e.g. {"wer": 0.31, "epoch": 40}). Replace the body with whatever
    matches your setup: parse a CSV, read a `metrics.json`, tail a log, call
    `wandb` — anything that yields short factual strings. Return a list of
    Markdown bullet strings. Keep them concrete and truthful; the report
    generator will NOT invent numbers, so only what you emit here becomes a
    result in the post.
    """
    lines: list[str] = []
    for jf in sorted(results_dir.rglob("*.json")):
        if not modified_this_week(jf):
            continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        nums = {k: v for k, v in data.items() if isinstance(v, (int, float))}
        if nums:
            rel = jf.relative_to(results_dir)
            summary = ", ".join(f"{k}={v}" for k, v in list(nums.items())[:8])
            lines.append(f"- `{rel}`: {summary}")
    return lines


def collect_plots(results_dir: Path, dest_dir: Path) -> list[str]:
    """
    ADAPT (2/2): choose which plots to include.

    The default copies any .png/.svg image modified in the last week into the
    report folder. Narrow this if your runs produce many images — e.g. only
    files named `*_final.png`, or only the newest per experiment.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for img in sorted(list(results_dir.rglob("*.png")) + list(results_dir.rglob("*.svg"))):
        if not modified_this_week(img):
            continue
        target = dest_dir / img.name
        shutil.copy2(img, target)
        names.append(img.name)
    return names


def build_report(metrics: list[str], plots: list[str]) -> str:
    parts = [
        f"# Experiment report — {WEEK_TAG}",
        f"_Window: {SINCE.isoformat()} to {TODAY.isoformat()}. Machine: Titan._",
        "",
        "## Metrics",
        "\n".join(metrics) if metrics else "No metrics files were updated this week.",
    ]
    if plots:
        parts += ["", "## Plots", "\n".join(f"![{n}]({n})" for n in plots)]
    return "\n".join(parts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True, type=Path,
                    help="Directory holding your experiment outputs")
    ap.add_argument("--report-repo", required=True, type=Path,
                    help="Local clone of the weekly-reports git repo (with a remote set)")
    ap.add_argument("--no-push", action="store_true", help="Build the report but do not git push")
    args = ap.parse_args()

    report_dir = args.report_repo / "reports"
    week_asset_dir = report_dir  # plots sit beside the report; the generator finds them
    report_dir.mkdir(parents=True, exist_ok=True)

    metrics = collect_metrics(args.results_dir)
    plots = collect_plots(args.results_dir, week_asset_dir)
    report_md = build_report(metrics, plots)

    report_path = report_dir / f"report-{WEEK_TAG}.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Wrote {report_path} ({len(metrics)} metrics, {len(plots)} plots)")

    if args.no_push:
        return

    # Commit and push so the Friday generator can read it.
    repo = str(args.report_repo)
    sh(["git", "add", "-A"], cwd=repo)
    # Only commit if something changed.
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                            capture_output=True, text=True).stdout.strip()
    if status:
        sh(["git", "commit", "-m", f"Weekly report {WEEK_TAG}"], cwd=repo)
        sh(["git", "push"], cwd=repo)
        print("Pushed report.")
    else:
        print("No changes to push.")


if __name__ == "__main__":
    main()
