#!/usr/bin/env python3
"""
Weekly research-report generator.

Runs on Fridays (via .github/workflows/weekly-report.yml). It gathers the
week's raw material from three sources — experiments (Titan, via a git repo the
Titan collector pushes to), writing (Overleaf, via its git bridge), and code
(GitHub) — then asks Claude to draft a progress report in the classic /
Steven-Pinker prose style. The draft is written into site/_posts/ as a Jekyll
post; the workflow opens a PR so nothing is published until Chris reviews it.

Design notes
------------
* Every source degrades gracefully. A missing secret or an unreachable repo
  logs a warning and the corresponding section is simply left thin — the run
  never hard-fails just because Overleaf was down or Titan hadn't pushed yet.
* The model is given ONLY the gathered material and is told, firmly, not to
  invent results. See PINKER_SYSTEM_PROMPT.
* Generated posts default to `crosspost: false` (the opt-in cross-posting
  system) so a weekly personal report never propagates to the Gaelg AI blog
  unless Chris flips it during review.

Configuration is entirely by environment variable — see automation/README.md.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import anthropic

# --------------------------------------------------------------------------- #
# Configuration (all via env; see automation/README.md)
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
POSTS_DIR = SITE_DIR / "_posts"
ASSETS_SUBDIR = "assets/weekly-reports"          # under site/, and under the URL root

GITHUB_USER = os.environ.get("GH_REPORT_USER", "chris-sj-bartley")
GITHUB_TOKEN = os.environ.get("GH_REPORT_TOKEN", "")   # PAT with repo:read across your repos

OVERLEAF_GIT_URL = os.environ.get("OVERLEAF_GIT_URL", "")   # https://git:<token>@git.overleaf.com/<id>

TITAN_REPORT_REPO = os.environ.get("TITAN_REPORT_REPO", "")  # git URL the Titan collector pushes to
TITAN_REPORT_TOKEN = os.environ.get("TITAN_REPORT_TOKEN", "")  # PAT if the report repo is private

MODEL = os.environ.get("REPORT_MODEL", "claude-opus-4-8")
WEEK_DAYS = int(os.environ.get("REPORT_WINDOW_DAYS", "7"))

# The window: the WEEK_DAYS ending today (the Friday the job runs).
TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=WEEK_DAYS)
SINCE_ISO = SINCE.isoformat()
ISO_YEAR, ISO_WEEK, _ = TODAY.isocalendar()
WEEK_TAG = f"{ISO_YEAR}-W{ISO_WEEK:02d}"


def log(msg: str) -> None:
    print(f"[weekly-report] {msg}", file=sys.stderr)


def run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command, return stdout, never raise on non-zero (log instead)."""
    try:
        out = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=180
        )
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

    # Pull requests merged/opened in the window.
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
# --------------------------------------------------------------------------- #
def gather_overleaf() -> str:
    if not OVERLEAF_GIT_URL:
        log("no OVERLEAF_GIT_URL; skipping Overleaf")
        return ""
    tmp = tempfile.mkdtemp(prefix="overleaf-")
    try:
        run(["git", "clone", "--quiet", OVERLEAF_GIT_URL, tmp])
        # Commits in the window.
        commits = run(
            ["git", "log", f"--since={SINCE_ISO}", "--pretty=format:- %ad %s", "--date=short"],
            cwd=tmp,
        ).strip()
        # Per-file change stats for .tex over the window.
        first = run(
            ["git", "rev-list", "-1", f"--before={SINCE_ISO}", "HEAD"], cwd=tmp
        ).strip()
        stat = ""
        added_prose = ""
        if first:
            stat = run(["git", "diff", "--stat", first, "HEAD", "--", "*.tex"], cwd=tmp).strip()
            # The actual added lines (prose) so the model can describe what was written.
            diff = run(["git", "diff", first, "HEAD", "--", "*.tex"], cwd=tmp)
            added = [
                ln[1:].strip()
                for ln in diff.splitlines()
                if ln.startswith("+") and not ln.startswith("+++")
            ]
            added_prose = "\n".join(added)[:6000]  # bound the payload
        parts = ["## Overleaf writing (LaTeX changes this week)"]
        if commits:
            parts.append("Commits:\n" + commits)
        if stat:
            parts.append("Changed files:\n" + stat)
        if added_prose:
            parts.append("Lines added (prose the model may summarise):\n" + added_prose)
        return "\n\n".join(parts) if len(parts) > 1 else ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Source 3: Titan — experiment report the collector pushed to a git repo
# --------------------------------------------------------------------------- #
def gather_titan() -> tuple[str, list[Path]]:
    """Returns (markdown_text, [plot image paths already copied into site assets])."""
    if not TITAN_REPORT_REPO:
        log("no TITAN_REPORT_REPO; skipping Titan experiments")
        return "", []
    url = TITAN_REPORT_REPO
    if TITAN_REPORT_TOKEN and url.startswith("https://") and "@" not in url:
        url = url.replace("https://", f"https://git:{TITAN_REPORT_TOKEN}@")

    tmp = tempfile.mkdtemp(prefix="titan-")
    copied: list[Path] = []
    try:
        run(["git", "clone", "--quiet", "--depth", "1", url, tmp])
        report_root = Path(tmp)

        # The collector writes reports/report-YYYY-Www.md (this week's preferred,
        # else the most recent).
        candidates = sorted(report_root.glob("reports/report-*.md"))
        this_week = report_root / "reports" / f"report-{WEEK_TAG}.md"
        chosen = this_week if this_week.exists() else (candidates[-1] if candidates else None)
        if chosen is None:
            log("no Titan report found in repo")
            return "", []

        text = chosen.read_text(encoding="utf-8", errors="replace")

        # Copy any plots referenced beside the report into site assets, and
        # rewrite their paths to the published URL location.
        dest_dir = SITE_DIR / ASSETS_SUBDIR / WEEK_TAG
        dest_dir.mkdir(parents=True, exist_ok=True)
        plot_dir = chosen.parent
        for img in list(plot_dir.glob("*.png")) + list(plot_dir.glob("*.svg")) + list(plot_dir.glob("*.jpg")):
            dest = dest_dir / img.name
            shutil.copy2(img, dest)
            copied.append(dest)
            # Rewrite references in the report text to the site URL.
            text = text.replace(img.name, f"/{ASSETS_SUBDIR}/{WEEK_TAG}/{img.name}")

        plot_note = ""
        if copied:
            urls = "\n".join(f"- /{ASSETS_SUBDIR}/{WEEK_TAG}/{p.name}" for p in copied)
            plot_note = "\n\nAvailable plot images (embed with Markdown if relevant):\n" + urls

        return "## Experiments on Titan (this week's report)\n" + text + plot_note, copied
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Compose the draft with Claude
# --------------------------------------------------------------------------- #
PINKER_SYSTEM_PROMPT = """\
You are ghost-writing a weekly research-progress report for Chris Bartley, a PhD \
researcher building speech and language technology for Manx Gaelic (an endangered \
language) at the University of Sheffield. The report is published on his personal \
blog and written in the first person ("I").

Write in the classic prose style associated with Steven Pinker's *The Sense of \
Style*: clear, concrete, and confident. Specifically:
- Treat prose as a window onto the world: show the reader what happened, don't \
  talk about the act of reporting it. No metadiscourse ("In this report I will…", \
  "It is worth noting that…").
- Prefer concrete nouns and strong verbs over abstraction and nominalisation. \
  Name the actual experiment, model, metric, or file.
- Explain each result to an intelligent reader who is NOT a specialist in speech \
  technology — define a term the first time it matters, then move on.
- Be economical. Cut hedging, throat-clearing, and filler. Coherent paragraphs, \
  not bullet soup — though a short list is fine for enumerating concrete results.
- Curious and engaged in tone, never breathless or self-congratulatory.

Structure the report as Markdown with these sections, omitting any section that \
has no material this week (do not pad):
1. A short opening summary (2–4 sentences) — the week in a nutshell.
2. **Experiments** — what was run and why.
3. **Results** — what the numbers showed. Embed any provided plot images with \
   Markdown image syntax using the exact URLs given.
4. **Writing** — progress on papers/thesis, drawn from the Overleaf changes.

CRITICAL ACCURACY RULES:
- Use ONLY the material provided in the user message. Do not invent experiments, \
  numbers, results, or conclusions. If the material is thin or a source is empty, \
  say plainly that it was a quiet week on that front rather than inflating it.
- Never overstate significance. Report what the evidence shows, no more.
- If something is ambiguous in the source material, describe it cautiously rather \
  than guessing.

Output ONLY the Markdown body of the post — no YAML front matter, no title line, \
no surrounding commentary."""


def compose(raw_material: str) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    user_msg = (
        f"Here is everything gathered for the week of {SINCE_ISO} to "
        f"{TODAY.isoformat()} ({WEEK_TAG}). Draft the report.\n\n{raw_material}"
    )
    # Stream the response (output can run long) and take the final message.
    # Extended thinking is enabled with a modest budget to help the model follow
    # the structure and accuracy rules; max_tokens must exceed the think budget.
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "enabled", "budget_tokens": 3000},
        system=PINKER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        message = stream.get_final_message()

    if message.stop_reason == "refusal":
        raise SystemExit("Model refused to draft the report; check the input material.")
    return "".join(b.text for b in message.content if b.type == "text").strip()


# --------------------------------------------------------------------------- #
# Write the Jekyll post
# --------------------------------------------------------------------------- #
def write_post(body: str) -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"weekly-report-{WEEK_TAG.lower()}"
    filename = f"{TODAY.isoformat()}-{slug}.md"
    path = POSTS_DIR / filename
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
    )
    path.write_text(front + body + "\n", encoding="utf-8")
    return path


def main() -> None:
    sections: list[str] = []

    gh = gather_github()
    if gh:
        sections.append(gh)

    over = gather_overleaf()
    if over:
        sections.append(over)

    titan, _plots = gather_titan()
    if titan:
        sections.append(titan)

    if not sections:
        log("no material gathered from any source; writing a minimal placeholder note")
        raw = "No experiment, writing, or code activity was captured for this week."
    else:
        raw = "\n\n---\n\n".join(sections)

    body = compose(raw)
    path = write_post(body)
    log(f"wrote {path.relative_to(REPO_ROOT)}")

    # Expose the new file path to the workflow (for the PR branch/title).
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"post_path={path.relative_to(REPO_ROOT)}\n")
            fh.write(f"week_tag={WEEK_TAG}\n")


if __name__ == "__main__":
    main()
