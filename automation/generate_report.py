#!/usr/bin/env python3
"""
Weekly research-report: gather & prepare step.

This runs first in .github/workflows/weekly-report.yml. It gathers the week's
raw material from two sources — writing (Overleaf, via its git bridge) and code
+ results (GitHub) — renders any figures you tagged in your LaTeX to PNG, and
lays down:

  * automation/_work/raw-material.md   the gathered facts
  * automation/_work/report-brief.md   the full instruction for the drafting step
  * site/assets/weekly-reports/<week>/ rendered figure PNGs (if any)
  * site/_posts/<date>-weekly-report-<week>.md   the post file, front matter +
    a placeholder body line for the drafting step to replace

The DRAFTING itself is NOT done here. A later step runs the Claude Code GitHub
Action (authenticated with Chris's Claude subscription via CLAUDE_CODE_OAUTH_TOKEN)
which reads report-brief.md, VISUALLY INSPECTS each rendered figure, and writes
the Steven-Pinker-style body into the post file. A final step opens a PR — nothing
is published until Chris reviews it.

Experiments used to come from a Titan-side collector; that was dropped in favour
of reading results straight from GitHub, since every machine (Titan, Cassini, …)
publishes there anyway.

Everything degrades gracefully: a missing secret, an unreachable source, or a
figure that won't compile logs a warning and is skipped; the run never hard-fails.
Configuration is by environment variable and two committed lists — see
automation/README.md.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
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

# Mark a figure for the report by putting this comment on its own line directly
# above \begin{figure}. Only tagged figures are rendered.
FIGURE_TAG = os.environ.get("REPORT_FIGURE_TAG", "%@report")

WEEK_DAYS = int(os.environ.get("REPORT_WINDOW_DAYS", "7"))

# The window: the WEEK_DAYS ending today (the Friday the job runs).
TODAY = dt.date.today()
SINCE = TODAY - dt.timedelta(days=WEEK_DAYS)
SINCE_ISO = SINCE.isoformat()
ISO_YEAR, ISO_WEEK, _ = TODAY.isocalendar()
WEEK_TAG = f"{ISO_YEAR}-W{ISO_WEEK:02d}"

# --------------------------------------------------------------------------- #
# Persisted state (restored/saved by the workflow cache). Lets us report what
# changed SINCE THE LAST REPORT rather than over a fixed, unreliable git window:
#   * last_run  -> GitHub window start (nothing gets re-reported next week)
#   * overleaf  -> {project_id: {relpath: sha256}} to diff Overleaf .tex files,
#                  which is essential because the Overleaf git bridge exposes no
#                  usable history to diff against.
# --------------------------------------------------------------------------- #
STATE_DIR = REPO_ROOT / "automation" / "_state"
NOW_ISO = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_state() -> dict:
    try:
        return json.loads((STATE_DIR / "state.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - no/empty/corrupt state => cold start
        return {}


STATE = _load_state()
LAST_RUN = STATE.get("last_run")
# GitHub "since": the last report, or fall back to the fixed window on cold start.
GH_SINCE = LAST_RUN or f"{SINCE_ISO}T00:00:00Z"
NEW_OVERLEAF_HASHES: dict[str, dict[str, str]] = {}

ASSETS_DIR = SITE_DIR / ASSETS_SUBDIR / WEEK_TAG            # where PNGs are written
ASSETS_URL = f"/{ASSETS_SUBDIR}/{WEEK_TAG}"                 # how the site references them

BODY_PLACEHOLDER = "<!-- REPORT-BODY: the drafting step replaces this line -->"


def log(msg: str) -> None:
    print(f"[weekly-report] {msg}", file=sys.stderr)


def run(cmd: list[str], cwd: str | None = None, timeout: int = 180) -> subprocess.CompletedProcess:
    """Run a command, returning the CompletedProcess, never raising (log instead)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            log(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()[:500]}")
        return proc
    except Exception as exc:  # noqa: BLE001 - degrade gracefully
        log(f"command errored: {' '.join(cmd)} -> {exc}")
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(exc))


def out(cmd: list[str], cwd: str | None = None) -> str:
    return run(cmd, cwd=cwd).stdout


# --------------------------------------------------------------------------- #
# Source 1: GitHub — commits, PRs, and the actual diffs of pertinent files
# (results like .json/.csv, and plan/notes .md files) across active repos.
# --------------------------------------------------------------------------- #
GH_FILE_EXT = {".md", ".json", ".csv", ".tsv", ".yaml", ".yml"}
GH_FILE_NAME_RE = re.compile(r"(plan|note|result|todo|changelog|readme|metric|eval|score)", re.I)
GH_FILE_EXCLUDE_RE = re.compile(
    r"(package-lock\.json|yarn\.lock|poetry\.lock|\.min\.|(^|/)(node_modules|dist|build|vendor|\.venv)/|\.ipynb$)",
    re.I,
)
GH_MAX_FILE_PATCH = 1500     # chars of diff kept per file
GH_MAX_TOTAL = 12000         # chars of file-diff material total


def _gh_pertinent(filename: str) -> bool:
    if GH_FILE_EXCLUDE_RE.search(filename):
        return False
    name = Path(filename).name
    return Path(filename).suffix.lower() in GH_FILE_EXT or bool(GH_FILE_NAME_RE.search(name))


def _gh_repo_file_changes(requests, headers, full_name: str) -> str:
    """Aggregate this week's diffs of pertinent files in one repo, as text."""
    try:
        owner, repo = full_name.split("/", 1)
    except ValueError:
        return ""
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        params={"author": GITHUB_USER, "since": GH_SINCE, "per_page": 100},
        headers=headers, timeout=30,
    )
    if not r.ok or not r.json():
        return ""
    commits = r.json()
    head = commits[0]["sha"]
    parents = commits[-1].get("parents") or []
    files = []
    try:
        if parents:  # net diff over the week: base = parent of oldest commit
            rc = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/compare/{parents[0]['sha']}...{head}",
                headers=headers, timeout=30,
            )
            files = rc.json().get("files", []) if rc.ok else []
        else:  # initial commit in the repo
            rc = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits/{head}",
                headers=headers, timeout=30,
            )
            files = rc.json().get("files", []) if rc.ok else []
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub compare errored for {full_name}: {exc}")
        return ""

    blocks = []
    for f in files:
        fn = f.get("filename", "")
        if not _gh_pertinent(fn):
            continue
        patch = (f.get("patch") or "").strip()
        if not patch:  # binary or too large; note the change without the diff
            blocks.append(f"#### {full_name}/{fn} ({f.get('status', '')}, no text diff)")
            continue
        blocks.append(
            f"#### {full_name}/{fn} ({f.get('status', '')})\n```diff\n"
            + patch[:GH_MAX_FILE_PATCH] + "\n```"
        )
    return "\n\n".join(blocks)


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
    active_repos: list[str] = []

    q = f"author:{GITHUB_USER} author-date:>={GH_SINCE}"
    try:
        r = requests.get(
            "https://api.github.com/search/commits",
            params={"q": q, "sort": "author-date", "per_page": 100},
            headers=headers, timeout=30,
        )
        if r.ok:
            for item in r.json().get("items", []):
                repo = item.get("repository", {}).get("full_name", "?")
                if repo not in active_repos:
                    active_repos.append(repo)
                msg = (item.get("commit", {}).get("message", "") or "").splitlines()[0]
                lines.append(f"- [{repo}] {msg}")
        else:
            log(f"GitHub commit search failed: {r.status_code} {r.text[:200]}")
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub commit search errored: {exc}")

    q_pr = f"author:{GITHUB_USER} type:pr updated:>={GH_SINCE}"
    try:
        r = requests.get(
            "https://api.github.com/search/issues",
            params={"q": q_pr, "per_page": 50},
            headers=headers, timeout=30,
        )
        if r.ok:
            for item in r.json().get("items", []):
                state = "merged" if item.get("pull_request", {}).get("merged_at") else item.get("state", "")
                lines.append(f"- PR ({state}): {item.get('title', '')} — {item.get('html_url', '')}")
    except Exception as exc:  # noqa: BLE001
        log(f"GitHub PR search errored: {exc}")

    # Pull the actual diffs of pertinent files (results + plan/notes) per repo,
    # up to a total budget so the drafter gets substance, not noise.
    file_sections: list[str] = []
    budget = GH_MAX_TOTAL
    for repo in active_repos:
        if budget <= 0:
            break
        chunk = _gh_repo_file_changes(requests, headers, repo)
        if chunk:
            chunk = chunk[:budget]
            budget -= len(chunk)
            file_sections.append(chunk)

    if not lines and not file_sections:
        return ""
    parts = []
    if lines:
        parts.append("## GitHub activity (commits & PRs this week)\n" + "\n".join(lines))
    if file_sections:
        parts.append(
            "## GitHub file changes this week (results, plans, notes)\n"
            "Diffs of pertinent files. Treat results files (.json/.csv) as data, "
            "and plan/notes .md files as intent/next-steps.\n\n"
            + "\n\n".join(file_sections)
        )
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# Source 2: Overleaf — writing + tagged figures (git bridge)
#
# The account-wide token clones every project; there is no list endpoint, so we
# loop over a committed list of project IDs (automation/overleaf_projects.txt).
# --------------------------------------------------------------------------- #
def _overleaf_projects() -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if not OVERLEAF_PROJECTS_FILE.exists():
        return items
    for raw in OVERLEAF_PROJECTS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        pid = parts[0].rstrip("/").split("/")[-1]
        label = parts[1].strip() if len(parts) > 1 else pid
        items.append((pid, label))
    return items


def _extract_tagged_figures(tex_text: str) -> list[tuple[str, str]]:
    """Return [(figure_source, caption)] for figures preceded by FIGURE_TAG."""
    figs: list[tuple[str, str]] = []
    pattern = re.compile(
        re.escape(FIGURE_TAG) + r"[^\n]*\n\s*(\\begin\{figure\*?\}.*?\\end\{figure\*?\})",
        re.DOTALL,
    )
    for m in pattern.finditer(tex_text):
        block = m.group(1)
        cap = re.search(r"\\caption\{(.*?)\}", block, re.DOTALL)
        caption = re.sub(r"\s+", " ", cap.group(1)).strip() if cap else ""
        figs.append((block, caption))
    return figs


def _collect_tagged_figures(repo_dir: str, label: str) -> list[dict]:
    """Find %@report-tagged figures and save each one's LaTeX source for the
    drafting model. This script does NOT render anything: the model reads the
    source, understands the figure's intent at a high level, draws a clean PNG
    (graphviz/matplotlib), checks it visually, and embeds it if clear.

    Driven by the tag, not by weekly change detection — Overleaf's git bridge
    doesn't expose reliable history, so the explicit tag is the opt-in signal."""
    figs: list[dict] = []
    idx = 0
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "fig"
    fig_dir = WORK_DIR / "figures"
    for tex_path in Path(repo_dir).rglob("*.tex"):
        try:
            text = tex_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for block, caption in _extract_tagged_figures(text):
            idx += 1
            stem = f"{slug}-{idx}"
            fig_dir.mkdir(parents=True, exist_ok=True)
            header = f"% caption: {caption}\n\n" if caption else ""
            (fig_dir / f"{stem}.tex").write_text(header + block, encoding="utf-8")
            figs.append({
                "project": label,
                "caption": caption,
                "source": f"automation/_work/figures/{stem}.tex",
                "disk": f"site{ASSETS_URL}/{stem}.png",
                "url": f"{ASSETS_URL}/{stem}.png",
            })
            log(f"figure to create: {stem} (from {tex_path.name}, '{label}')")
    return figs


def _overleaf_one(project_id: str, label: str) -> tuple[str, list[dict]]:
    """Detect a project's .tex changes since the last report (by content hash,
    since the git bridge has no usable history) and render its tagged figures."""
    url = f"https://git:{OVERLEAF_TOKEN}@git.overleaf.com/{project_id}"
    tmp = tempfile.mkdtemp(prefix="overleaf-")
    try:
        run(["git", "clone", "--quiet", url, tmp])
        if not (Path(tmp) / ".git").exists():
            log(f"Overleaf clone failed for {label} ({project_id})")
            return "", []

        prev = STATE.get("overleaf", {}).get(project_id)  # {relpath: sha} or None
        cur_hashes: dict[str, str] = {}
        changes: list[tuple[str, str, str]] = []  # (relpath, kind, content)
        for tex in sorted(Path(tmp).rglob("*.tex")):
            rel = tex.relative_to(tmp).as_posix()
            content = tex.read_text(encoding="utf-8", errors="replace")
            digest = hashlib.sha256(content.encode("utf-8", "replace")).hexdigest()
            cur_hashes[rel] = digest
            if prev is not None and prev.get(rel) != digest:
                kind = "changed" if rel in prev else "new"
                changes.append((rel, kind, content[:3500]))
        NEW_OVERLEAF_HASHES[project_id] = cur_hashes
        if prev is None:
            log(f"Overleaf '{label}': baselined (first run; no diff reported)")

        figures = _collect_tagged_figures(tmp, label)

        if not (changes or figures):
            return "", figures
        parts = [f"### {label}"]
        for rel, kind, content in changes[:8]:
            parts.append(
                f"**{rel}** ({kind} since last report; reproduce any results "
                f"tables as Markdown, summarise prose):\n```latex\n{content}\n```"
            )
        if figures and not changes:
            parts.append("(A figure tagged for the report was drawn from this paper.)")
        return "\n\n".join(parts), figures
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gather_overleaf() -> tuple[str, list[dict]]:
    if not OVERLEAF_TOKEN:
        log("no OVERLEAF_TOKEN; skipping Overleaf")
        return "", []
    projects = _overleaf_projects()
    if not projects:
        log("no projects in automation/overleaf_projects.txt; skipping Overleaf")
        return "", []
    blocks: list[str] = []
    figures: list[dict] = []
    for pid, label in projects:
        text, figs = _overleaf_one(pid, label)
        if text:
            blocks.append(text)
        figures.extend(figs)
    if not blocks:
        return "", figures
    return "## Overleaf writing (LaTeX changes this week)\n\n" + "\n\n".join(blocks), figures


# --------------------------------------------------------------------------- #
# The drafting brief (style + accuracy + figure verification) for Claude
# --------------------------------------------------------------------------- #
PINKER_STYLE = """\
Write in the first person ("I"). Use the classic prose style of Steven Pinker's \
*The Sense of Style*: clear, concrete, and confident.
- Treat prose as a window onto the world: show what happened; don't narrate the \
  act of reporting. No metadiscourse.
- Prefer concrete nouns and strong verbs. Name the actual experiment, model, \
  metric, or file.
- Explain each result to an intelligent reader who is NOT a speech-technology \
  specialist — define a term the first time it matters, then move on.
- Be economical; coherent paragraphs, not bullet soup (a short list for concrete \
  results is fine).

Structure as Markdown with these sections, OMITTING any with no material:
1. A short opening summary (2-4 sentences).
2. **Experiments** — what was run and why.
3. **Results** — what the numbers showed. If the Overleaf changes include results \
   tables, reproduce the changed table(s) as clean Markdown tables using the \
   actual values from the material. Embed verified figures (see below).
4. **Writing** — progress on papers/thesis, from the Overleaf changes.
5. **Next** (optional) — planned next steps, ONLY if the material (e.g. plan or
   notes .md files from GitHub) actually states them. Don't speculate."""

ACCURACY_RULES = """\
CRITICAL ACCURACY RULES:
- Use ONLY the facts in raw-material.md. Do not invent experiments, numbers, \
  results, or conclusions. If a source is empty or the week was thin, say so.
- Never overstate significance. If something is ambiguous, describe it cautiously."""


def _figures_section(figures: list[dict]) -> str:
    if not figures:
        return "No figures were tagged this week, so create and embed none."
    lines = [
        "Each item is a figure the author tagged for the report. You are given its",
        "original LaTeX/TikZ SOURCE FILE and caption. Do NOT reproduce the LaTeX",
        "exactly — that is not the goal. For EACH figure:",
        "",
        "  1. Read the source file to understand, at a HIGH LEVEL, what the figure",
        "     depicts and the essential information it must convey (the nodes and",
        "     flow of a pipeline; the axes and trend of a plot; the groupings/labels).",
        "  2. Create a clean, self-contained PNG that conveys that clearly. Write and",
        "     run a small script via the Bash tool — Graphviz (`dot -Tpng`) is ideal",
        "     for pipeline/flow diagrams; Python matplotlib for data plots or",
        "     box-and-arrow diagrams. It does NOT need to match the LaTeX visually;",
        "     it needs to be a plausible, legible rendering of the same information.",
        "     Save it to the exact disk path given (mkdir -p its directory first).",
        "  3. Open the PNG with the Read tool and analyse it FRESH, as if seeing it",
        "     for the first time: is it clear and legible, and does it convey the",
        "     information the surrounding report needs? If not, revise and regenerate.",
        "  4. Embed it (Markdown image with the exact URL) near the relevant text,",
        "     ONLY once it clearly conveys the needed information. If you cannot make",
        "     it clear, omit it and note briefly that the figure was left out.",
        "",
        "Figures:",
    ]
    for f in figures:
        cap = f" — caption: {f['caption']}" if f["caption"] else ""
        lines.append(
            f"- {f['project']}: source `{f['source']}` → create PNG at `{f['disk']}`, "
            f"embed with url `{f['url']}`{cap}"
        )
    return "\n".join(lines)


def write_brief(post_rel_path: str, figures: list[dict]) -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    brief = f"""\
# Task: draft this week's research progress report

Read the gathered material in `automation/_work/raw-material.md`. It covers what
changed since the last report ({LAST_RUN or "the start of the window"}) up to
{TODAY.isoformat()} ({WEEK_TAG}): writing from Overleaf and code + results from
GitHub. Report only that period's work; if a source shows nothing new, say so
rather than restating older work.

Then edit the file `{post_rel_path}`: replace the single placeholder line
`{BODY_PLACEHOLDER}` (directly beneath the YAML front matter) with the drafted
report body in Markdown. Do NOT modify the YAML front matter. The only files you
should write are the report post, the figure PNGs described below, and any short
scripts you use to generate them.

## Style
{PINKER_STYLE}

## Accuracy
{ACCURACY_RULES}

## Figures (verify before embedding)
{_figures_section(figures)}
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

    gh = gather_github()
    overleaf_text, figures = gather_overleaf()

    sections = [s for s in (gh, overleaf_text) if s]
    if sections:
        raw = "\n\n---\n\n".join(sections)
    else:
        log("no material gathered from any source; brief will note a quiet week")
        raw = "No writing or code activity was captured for this week."
    (WORK_DIR / "raw-material.md").write_text(raw, encoding="utf-8")

    post_path = write_post_shell()
    post_rel = post_path.relative_to(REPO_ROOT).as_posix()
    write_brief(post_rel, figures)
    log(f"prepared {post_rel}; {len(figures)} figure(s) rendered")

    # Persist state for next run's "since last report" diffing. Keep the previous
    # Overleaf hashes if we didn't gather Overleaf this run (so we don't wipe the
    # baseline). The workflow caches automation/_state between runs.
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    new_state = {
        "last_run": NOW_ISO,
        "overleaf": NEW_OVERLEAF_HASHES if NEW_OVERLEAF_HASHES else STATE.get("overleaf", {}),
    }
    (STATE_DIR / "state.json").write_text(json.dumps(new_state, indent=1), encoding="utf-8")
    log(f"state saved (last_run={NOW_ISO}, {len(new_state['overleaf'])} Overleaf projects)")

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"post_path={post_rel}\n")
            fh.write(f"week_tag={WEEK_TAG}\n")
            fh.write(f"figure_count={len(figures)}\n")


if __name__ == "__main__":
    main()
