#!/usr/bin/env python3
"""
Weekly research-report: gather & prepare step.

This runs first in .github/workflows/weekly-report.yml. It gathers the week's
raw material from three sources — experiments (Titan, via a git repo the Titan
collector pushes to), writing (Overleaf, via its git bridge), and code (GitHub) —
copies any plots into the site's assets, and lays down:

  * automation/_work/raw-material.md   the gathered facts
  * automation/_work/report-brief.md   the full instruction for the drafting step
  * site/_posts/<date>-weekly-report-<week>.md   the post file, front matter +
    a placeholder body line for the drafting step to replace

The DRAFTING itself is NOT done here. A later step runs the Claude Code GitHub
Action (authenticated with Chris's Claude subscription via CLAUDE_CODE_OAUTH_TOKEN)
which reads report-brief.md and writes the Steven-Pinker-style body into the post
file. A final step opens a PR — nothing is published until Chris reviews it.

Everything degrades gracefully: a missing secret or unreachable source logs a
warning and that section is simply left thin; the run never hard-fails because
one source was down. Configuration is entirely by environment variable — see
automation/README.md.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration (all via env; see automation/README.md)
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
POSTS_DIR = SITE_DIR / "_posts"
WORK_DIR = REPO_ROOT / "automation" / "_work"
ASSETS_SUBDIR = "assets/weekly-reports"          # under site/, and under the URL root

GITHUB_USER = os.environ.get("GH_REPORT_USER", "chris-sj-bartley")
GITHUB_TOKEN = os.environ.get("GH_REPORT_TOKEN", "")   # PAT with repo contents:read

OVERLEAF_TOKEN = os.environ.get("OVERLEAF_TOKEN", "")   # account-wide git token (secret)
OVERLEAF_PROJECTS_FILE = REPO_ROOT / "automation" / "overleaf_projects.txt"  # committed list of IDs

TITAN_REPORT_REPO = os.environ.get("TITAN_REPORT_REPO", "")  # git URL the Titan collector pushes to
TITAN_REPORT_TOKEN = os.environ.get("TITAN_REPORT_TOKEN", "")  # PAT if that repo is private

WEEK_DAYS = int(os.environ.get("REPORT_WINDOW_DAYS", "7"))

# The window: the WEEK_DAYS ending today (the Friday the job runs).
TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=WEEK_DAYS)
SINCE_ISO = SINCE.isoformat()
ISO_YEAR, ISO_WEEK, _ = TODAY.isocalendar()
WEEK_TAG = f"{ISO_YEAR}-W{ISO_WEEK:02d}"

BODY_PLACEHOLDER = "<!-- REPORT-BODY: the drafting step replaces this line -->"


def log(msg: str) -> None:
    print(f"[weekly-report] {msg}", file=sys.stderr)


def run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command, return stdout, never raise on non-zero (log instead)."""
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=180)
        if out.returncode != 0:
            log(f"command failed ({out.returncode}): {' '.join(cmd)}\n{out.stderr.strip()}")
        return out.stdout
    except Exception as exc:  # noqa: BLE001 - degrade gracefully
        log(f"command errored: {' '.join(cmd)} -> {exc}")
        return ""


# --------------------------------------------------------------------------- #
# Source 1: GitHub — the week's commits and merged PRs
# --------------------------------------------------------------------------- #
def gather_github() -> str:
    if not GITHUB_TOKEN:
        log("no GH_REPORT_TOKEN; skipping GitHub")
        return ""
    try:
        import requests
    except ImportError:
        log("requests not installed; skipping GitHub")
        return ""

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    lines: list[str] = []

    # Commits authored in the window, across all repos.
    q = f"author:{GITHUB_USER} author-date:>={SINCE_ISO}"
    try:
        r = requests.get(
            "https://api.github.com/search/commits",
            params={"q": q, "sort": "author-date", "per_page": 100},
            headers=headers,
            timeout=30,
        )
        if r.ok:
            for item in r.json().get("items", []):
                repo = item.get("repository", {}).get("full_name", "?")
                msg = (item.get("commit", {}).get("message", "") or "").splitlines()[0]
                lines.append(f"- [{repo}] {msg}")
        else:
            log(f"GitHub commit search failed: {r.status_code} {r.text[:200]}")
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub commit search errored: {exc}")

    # Pull requests opened/updated in the window.
    q_pr = f"author:{GITHUB_USER} type:pr updated:>={SINCE_ISO}"
    try:
        r = requests.get(
            "https://api.github.com/search/issues",
            params={"q": q_pr, "per_page": 50},
            headers=headers,
            timeout=30,
        )
        if r.ok:
            for item in r.json().get("items", []):
                state = "merged" if item.get("pull_request", {}).get("merged_at") else item.get("state", "")
                lines.append(f"- PR ({state}): {item.get('title', '')} — {item.get('html_url', '')}")
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub PR search errored: {exc}")

    if not lines:
        return ""
    return "## GitHub activity (commits & PRs this week)\n" + "\n".join(lines)


# --------------------------------------------------------------------------- #
# Source 2: Overleaf — what was written this week (git bridge)
#
# Overleaf's git token is account-wide (one token clones every project), but
# there is no endpoint to list projects — so we keep a committed list of project
# IDs in automation/overleaf_projects.txt and loop over it. Add one line there
# when you create a new project. IDs are not secret; only OVERLEAF_TOKEN is.
# --------------------------------------------------------------------------- #
def _overleaf_projects() -> list[tuple[str, str]]:
    """Parse the project list -> [(project_id, label)]. Lines: `<id>  <label>`."""
    items: list[tuple[str, str]] = []
    if not OVERLEAF_PROJECTS_FILE.exists():
        return items
    for raw in OVERLEAF_PROJECTS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        pid = parts[0].rstrip("/").split("/")[-1]      # accept a bare id or a full URL
        label = parts[1].strip() if len(parts) > 1 else pid
        items.append((pid, label))
    return items


def _overleaf_one(project_id: str, label: str) -> str:
    """Clone one project and summarise this week's .tex changes, or '' if none."""
    url = f"https://git:{OVERLEAF_TOKEN}@git.overleaf.com/{project_id}"
    tmp = tempfile.mkdtemp(prefix="overleaf-")
    try:
        run(["git", "clone", "--quiet", url, tmp])
        if not (Path(tmp) / ".git").exists():
            log(f"Overleaf clone failed for {label} ({project_id})")
            return ""
        commits = run(
            ["git", "log", f"--since={SINCE_ISO}", "--pretty=format:- %ad %s", "--date=short"],
            cwd=tmp,
        ).strip()
        first = run(["git", "rev-list", "-1", f"--before={SINCE_ISO}", "HEAD"], cwd=tmp).strip()
        stat = ""
        added_prose = ""
        if first:
            stat = run(["git", "diff", "--stat", first, "HEAD", "--", "*.tex"], cwd=tmp).strip()
            diff = run(["git", "diff", first, "HEAD", "--", "*.tex"], cwd=tmp)
            added = [
                ln[1:].strip()
                for ln in diff.splitlines()
                if ln.startswith("+") and not ln.startswith("+++")
            ]
            added_prose = "\n".join(added)[:4000]  # bound per-project payload
        if not (commits or stat):
            return ""  # no change this week -> omit this project
        parts = [f"### {label}"]
        if commits:
            parts.append("Commits:\n" + commits)
        if stat:
            parts.append("Changed files:\n" + stat)
        if added_prose:
            parts.append("Lines added (prose the model may summarise):\n" + added_prose)
        return "\n\n".join(parts)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gather_overleaf() -> str:
    if not OVERLEAF_TOKEN:
        log("no OVERLEAF_TOKEN; skipping Overleaf")
        return ""
    projects = _overleaf_projects()
    if not projects:
        log("no projects in automation/overleaf_projects.txt; skipping Overleaf")
        return ""
    blocks = [b for b in (_overleaf_one(pid, label) for pid, label in projects) if b]
    if not blocks:
        return ""
    return "## Overleaf writing (LaTeX changes this week)\n\n" + "\n\n".join(blocks)


# --------------------------------------------------------------------------- #
# Source 3: Titan — experiment report the collector pushed to a git repo
# --------------------------------------------------------------------------- #
def gather_titan() -> str:
    if not TITAN_REPORT_REPO:
        log("no TITAN_REPORT_REPO; skipping Titan experiments")
        return ""
    url = TITAN_REPORT_REPO
    if TITAN_REPORT_TOKEN and url.startswith("https://") and "@" not in url:
        url = url.replace("https://", f"https://git:{TITAN_REPORT_TOKEN}@")

    tmp = tempfile.mkdtemp(prefix="titan-")
    try:
        run(["git", "clone", "--quiet", "--depth", "1", url, tmp])
        report_root = Path(tmp)

        candidates = sorted(report_root.glob("reports/report-*.md"))
        this_week = report_root / "reports" / f"report-{WEEK_TAG}.md"
        chosen = this_week if this_week.exists() else (candidates[-1] if candidates else None)
        if chosen is None:
            log("no Titan report found in repo")
            return ""

        text = chosen.read_text(encoding="utf-8", errors="replace")

        # Copy any plots beside the report into site assets, rewriting references
        # to the published URL location.
        dest_dir = SITE_DIR / ASSETS_SUBDIR / WEEK_TAG
        dest_dir.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for img in (
            list(chosen.parent.glob("*.png"))
            + list(chosen.parent.glob("*.svg"))
            + list(chosen.parent.glob("*.jpg"))
        ):
            shutil.copy2(img, dest_dir / img.name)
            copied.append(img.name)
            text = text.replace(img.name, f"/{ASSETS_SUBDIR}/{WEEK_TAG}/{img.name}")

        note = ""
        if copied:
            urls = "\n".join(f"- /{ASSETS_SUBDIR}/{WEEK_TAG}/{n}" for n in copied)
            note = "\n\nPlot images available to embed (use exact URLs):\n" + urls
        return "## Experiments on Titan (this week's report)\n" + text + note
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# The drafting brief (style + accuracy rules) handed to the Claude Code action
# --------------------------------------------------------------------------- #
PINKER_STYLE = """\
Write in the first person ("I"). Use the classic prose style of Steven Pinker's \
*The Sense of Style*: clear, concrete, and confident.
- Treat prose as a window onto the world: show what happened; don't narrate the \
  act of reporting. No metadiscourse ("In this report I will…", "It is worth \
  noting…").
- Prefer concrete nouns and strong verbs over abstraction. Name the actual \
  experiment, model, metric, or file.
- Explain each result to an intelligent reader who is NOT a speech-technology \
  specialist — define a term the first time it matters, then move on.
- Be economical: cut hedging and filler. Coherent paragraphs, not bullet soup, \
  though a short list is fine for enumerating concrete results.
- Curious and engaged in tone; never breathless or self-congratulatory.

Structure as Markdown with these sections, OMITTING any that has no material \
(do not pad):
1. A short opening summary (2–4 sentences) — the week in a nutshell.
2. **Experiments** — what was run and why.
3. **Results** — what the numbers showed. Embed any provided plot images with \
   Markdown image syntax using the exact URLs given in the material.
4. **Writing** — progress on papers/thesis, drawn from the Overleaf changes."""

ACCURACY_RULES = """\
CRITICAL ACCURACY RULES:
- Use ONLY the facts in raw-material.md. Do not invent experiments, numbers, \
  results, or conclusions. If a source is empty or the week was thin, say so \
  plainly rather than inflating it.
- Never overstate significance. Report what the evidence shows, no more.
- If something is ambiguous in the material, describe it cautiously, don't guess."""


def write_brief(post_rel_path: str) -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    brief = f"""\
# Task: draft this week's research progress report

Read the gathered material in `automation/_work/raw-material.md`. It contains this
week's experiments (from Titan), writing (from Overleaf), and code activity (from
GitHub) for the week {SINCE_ISO} to {TODAY.isoformat()} ({WEEK_TAG}).

Then edit the file `{post_rel_path}`: replace the single placeholder line
`{BODY_PLACEHOLDER}` (directly beneath the YAML front matter) with the drafted
report body in Markdown. Do NOT modify the YAML front matter — leave everything
between the `---` markers exactly as it is. Do not create any other files.

## Style
{PINKER_STYLE}

## Accuracy
{ACCURACY_RULES}
"""
    path = WORK_DIR / "report-brief.md"
    path.write_text(brief, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# The Jekyll post shell (front matter + placeholder body)
# --------------------------------------------------------------------------- #
def write_post_shell() -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"weekly-report-{WEEK_TAG.lower()}"
    path = POSTS_DIR / f"{TODAY.isoformat()}-{slug}.md"
    title = f"Weekly report: {TODAY.strftime('%d %b %Y')} ({WEEK_TAG})"
    description = f"Research progress for {WEEK_TAG}: experiments, results, and writing."
    front = (
        "---\n"
        "layout: post\n"
        f'title: "{title}"\n'
        f"date: {TODAY.isoformat()}\n"
        f'description: "{description}"\n'
        "tags: [weekly, research]\n"
        "crosspost: false   # personal report; set true to also propagate to Gaelg AI\n"
        "---\n\n"
        f"{BODY_PLACEHOLDER}\n"
    )
    path.write_text(front, encoding="utf-8")
    return path


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    sections = [s for s in (gather_github(), gather_overleaf(), gather_titan()) if s]
    if sections:
        raw = "\n\n---\n\n".join(sections)
    else:
        log("no material gathered from any source; brief will note a quiet week")
        raw = "No experiment, writing, or code activity was captured for this week."
    (WORK_DIR / "raw-material.md").write_text(raw, encoding="utf-8")

    post_path = write_post_shell()
    post_rel = post_path.relative_to(REPO_ROOT).as_posix()
    write_brief(post_rel)
    log(f"prepared {post_rel} and drafting brief")

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"post_path={post_rel}\n")
            fh.write(f"week_tag={WEEK_TAG}\n")


if __name__ == "__main__":
    main()
