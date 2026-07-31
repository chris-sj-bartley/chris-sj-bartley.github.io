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
        params={"author": GITHUB_USER, "since": f"{SINCE_ISO}T00:00:00Z", "per_page": 100},
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

    q = f"author:{GITHUB_USER} author-date:>={SINCE_ISO}"
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

    q_pr = f"author:{GITHUB_USER} type:pr updated:>={SINCE_ISO}"
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


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's well-known empty tree


def _window_base(repo_dir: str) -> str | None:
    """Diff base for this week's changes: the parent of the oldest in-window
    commit (or the empty tree if that's the repo's root). None => no activity.

    This does NOT require a commit before the window, so it works even when a
    project's whole git history is recent (common with Overleaf's git bridge)."""
    shas = out(["git", "log", f"--since={SINCE_ISO}", "--format=%H"], cwd=repo_dir).split()
    if not shas:
        return None
    oldest = shas[-1]
    parent = out(["git", "rev-parse", "--verify", "--quiet", f"{oldest}^"], cwd=repo_dir).strip()
    return parent or EMPTY_TREE


def _changed_tex_files(repo_dir: str, base: str) -> list[str]:
    """.tex files changed during the window (paths relative to the repo)."""
    names = out(
        ["git", "diff", "--name-only", base, "HEAD", "--", "*.tex"], cwd=repo_dir
    ).splitlines()
    return [n.strip() for n in names if n.strip()]


def _find_main_tex(repo_dir: str) -> Path | None:
    """The .tex containing \\documentclass and \\begin{document}."""
    for path in Path(repo_dir).rglob("*.tex"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "\\documentclass" in text and "\\begin{document}" in text:
            return path
    return None


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


def _png_ok(path: Path) -> bool:
    """Valid PNG with sensible dimensions, and (if Pillow is present) not blank."""
    try:
        head = path.read_bytes()[:24]
    except OSError:
        return False
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    if width < 40 or height < 40:
        return False
    try:
        from PIL import Image  # optional; the model does the real visual check too
    except ImportError:
        return True
    try:
        img = Image.open(path).convert("L")
        hist = img.histogram()
        total = sum(hist) or 1
        near_white = sum(hist[250:])           # near-white pixels
        return (total - near_white) / total > 0.001
    except Exception:  # noqa: BLE001
        return True


def _render_figures(repo_dir: str, label: str, changed_tex: list[str]) -> list[dict]:
    """Compile figures tagged in changed .tex to validated PNGs. Returns metadata."""
    if not shutil.which("pdflatex") or not shutil.which("pdftoppm"):
        log("pdflatex/pdftoppm not available; skipping figure rendering")
        return []
    main_tex = _find_main_tex(repo_dir)
    if main_tex is None:
        log(f"figure render: no main .tex (with \\documentclass) found for '{label}'")
        return []
    preamble = main_tex.read_text(encoding="utf-8", errors="replace").split("\\begin{document}", 1)[0]

    rendered: list[dict] = []
    fig_index = 0
    tagged = 0
    for rel in changed_tex:
        tex_path = Path(repo_dir) / rel
        if not tex_path.exists():
            continue
        figs_here = _extract_tagged_figures(tex_path.read_text(encoding="utf-8", errors="replace"))
        if figs_here:
            log(f"figure render: {len(figs_here)} tagged '{FIGURE_TAG}' figure(s) in {rel}")
        for block, caption in figs_here:
            tagged += 1
            fig_index += 1
            slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "fig"
            stem = f"{slug}-{fig_index}"
            # Wrap in the project's own preamble + the preview package to crop.
            wrapper = (
                preamble
                + "\n\\usepackage[active,tightpage,floats]{preview}\n"
                + "\\setlength\\PreviewBorder{6pt}\n"
                + "\\PreviewEnvironment{figure}\n"
                + "\\begin{document}\n"
                + block
                + "\n\\end{document}\n"
            )
            wrap_path = Path(repo_dir) / f"__report_{stem}.tex"
            wrap_path.write_text(wrapper, encoding="utf-8")
            # Compile in the project dir so \includegraphics + the .cls resolve.
            ok = False
            for _ in range(2):  # a second pass settles node references
                proc = run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                     "-no-shell-escape", wrap_path.name],
                    cwd=repo_dir,
                    timeout=120,
                )
                ok = proc.returncode == 0
                if not ok:
                    break
            pdf_path = wrap_path.with_suffix(".pdf")
            if not (ok and pdf_path.exists()):
                log(f"figure did not compile: {label} #{fig_index}")
                continue
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            png_path = ASSETS_DIR / f"{stem}.png"
            run(["pdftoppm", "-png", "-r", "200", "-singlefile",
                 str(pdf_path), str(png_path.with_suffix(""))])
            if not _png_ok(png_path):
                log(f"figure PNG failed validation, discarding: {label} #{fig_index}")
                png_path.unlink(missing_ok=True)
                continue
            rendered.append({
                "url": f"{ASSETS_URL}/{stem}.png",
                "project": label,
                "source": rel,
                "caption": caption,
            })
    if tagged:
        log(f"figure render '{label}': {len(rendered)}/{tagged} rendered OK")
    return rendered


def _overleaf_one(project_id: str, label: str) -> tuple[str, list[dict]]:
    """Summarise one project's weekly .tex changes and render its tagged figures."""
    url = f"https://git:{OVERLEAF_TOKEN}@git.overleaf.com/{project_id}"
    tmp = tempfile.mkdtemp(prefix="overleaf-")
    try:
        run(["git", "clone", "--quiet", url, tmp])
        if not (Path(tmp) / ".git").exists():
            log(f"Overleaf clone failed for {label} ({project_id})")
            return "", []
        commits = out(
            ["git", "log", f"--since={SINCE_ISO}", "--pretty=format:- %ad %s", "--date=short"],
            cwd=tmp,
        ).strip()
        base = _window_base(tmp)
        changed: list[str] = []
        stat = ""
        added_prose = ""
        if base:
            changed = _changed_tex_files(tmp, base)
            stat = out(["git", "diff", "--stat", base, "HEAD", "--", "*.tex"], cwd=tmp).strip()
            diff = out(["git", "diff", base, "HEAD", "--", "*.tex"], cwd=tmp)
            added = [ln[1:].strip() for ln in diff.splitlines()
                     if ln.startswith("+") and not ln.startswith("+++")]
            added_prose = "\n".join(added)[:5000]
        if changed:
            log(f"Overleaf '{label}': {len(changed)} changed .tex file(s)")

        figures = _render_figures(tmp, label, changed) if changed else []

        if not (commits or stat or figures):
            return "", []
        parts = [f"### {label}"]
        if commits:
            parts.append("Commits:\n" + commits)
        if stat:
            parts.append("Changed files:\n" + stat)
        if added_prose:
            parts.append(
                "Lines added (prose + tables the model may summarise; reproduce "
                "changed results tables as Markdown):\n" + added_prose
            )
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
        return "No figures were tagged for rendering this week, so embed none."
    lines = [
        "Candidate figures have been rendered to PNG. For EACH one below you MUST:",
        "  1. Open the PNG with the Read tool and actually look at it.",
        "  2. Embed it (Markdown image, using the exact URL) ONLY if it shows a "
        "clean, complete figure — not blank, not clipped, not a LaTeX error page.",
        "  3. If it looks broken, do NOT embed it; briefly note the figure could "
        "not be rendered cleanly.",
        "Place each embedded figure near the relevant Results/Experiments text and "
        "use its caption as the alt text / a short figure line.",
        "",
        "Candidates:",
    ]
    for f in figures:
        # The PNG lives under site/, so its on-disk path for Read is site + url.
        disk = f"site{f['url']}"
        cap = f" — caption: {f['caption']}" if f["caption"] else ""
        lines.append(f"- {f['project']}: url `{f['url']}`, file to inspect `{disk}`{cap}")
    return "\n".join(lines)


def write_brief(post_rel_path: str, figures: list[dict]) -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    brief = f"""\
# Task: draft this week's research progress report

Read the gathered material in `automation/_work/raw-material.md`. It covers the
week {SINCE_ISO} to {TODAY.isoformat()} ({WEEK_TAG}): writing from Overleaf and
code + results from GitHub.

Then edit the file `{post_rel_path}`: replace the single placeholder line
`{BODY_PLACEHOLDER}` (directly beneath the YAML front matter) with the drafted
report body in Markdown. Do NOT modify the YAML front matter. Do not create any
other files (you may Read the figure PNGs listed below to inspect them).

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

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"post_path={post_rel}\n")
            fh.write(f"week_tag={WEEK_TAG}\n")
            fh.write(f"figure_count={len(figures)}\n")


if __name__ == "__main__":
    main()
