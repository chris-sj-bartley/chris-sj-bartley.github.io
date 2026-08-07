# Automated weekly research report

Every Friday a GitHub Action drafts a progress report in the classic
(Steven-Pinker) prose style, pulling from three sources, and **opens a pull
request**. Nothing is published until you review and merge it. The drafting runs
via the **Claude Code Action authenticated with your Claude subscription** (an
OAuth token — not API billing, so no card or console credit is spent).

```
  GITHUB ACTIONS (Fri 08:00 UTC)
  1. generate_report.py gathers:
     • GitHub API → week's commits, PRs, results
     • Overleaf git bridge → diff .tex (writing + results tables)
     • extracts figures tagged %@report (their LaTeX source) for the model
     • groups everything by research project (report_projects.txt)
     → writes _work/raw-material.md + brief; lays down the post shell in _posts/
  2. Claude Code Action (subscription auth): reads the brief; writes the
     Pinker-style body as ONE section per project, each heading linked to its
     /projects/ page; for each tagged figure, understands the TikZ at a high
     level and DRAWS a clean PNG (graphviz/matplotlib), views it, and embeds it
     in that project's section only if it reads clearly
  3. create-pull-request opens the PR  ──▶ you review & merge ──▶ Pages deploy
```

Experiments come straight from **GitHub** — every machine (Titan, Cassini, …)
publishes results there, so there's no per-server collector to maintain.

The draft post is created with `crosspost: false`, so a weekly report never
propagates to the Gaelg AI blog unless you flip that to `true` while reviewing.

---

## One-time setup

### 1. Generate your Claude subscription token

On your own machine, in the Claude Code terminal, run:

```
claude setup-token
```

This uses your active Claude Pro/Max subscription to mint a long-lived OAuth
token for headless/CI use. Copy the token it prints — you'll paste it as a secret
in the next step. (Re-run this if it ever expires and the Friday run starts
failing on auth.)

### 2. GitHub repository secrets

In this repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add:

| Secret | What it is | Required? |
|--------|-----------|-----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | The token from `claude setup-token` (step 1). Draws on your Claude subscription. | **Yes** |
| `GH_REPORT_TOKEN` | Fine-grained PAT with **Contents: read** across your repos (to list the week's commits/PRs). github.com → Settings → Developer settings → Fine-grained tokens. | Recommended |
| `OVERLEAF_TOKEN` | Your account-wide Overleaf git authentication token (one token, all projects) — see step 4 | Optional |

Any optional source you leave unset is simply skipped — the report is built from
whatever is available. For a first smoke test you need only
`CLAUDE_CODE_OAUTH_TOKEN`.

### 3. Allow Actions to open PRs (one setting)

**Settings → Actions → General → Workflow permissions →** tick **"Allow GitHub
Actions to create and approve pull requests" → Save.** Without this the final
step can't open the PR.

### 4. Overleaf (multiple projects, account-wide token)

Overleaf's git token is **account-wide** — one token clones every project — but
there is no API to list projects, so you maintain a short list of project IDs.

1. Get the token: Overleaf → **Account Settings → Git integration** (or any
   project's **Menu → Git**) → generate/copy your **git authentication token**.
   Add it as the secret **`OVERLEAF_TOKEN`**. (Just the token — no URL.)
2. List the projects to report on in
   [`overleaf_projects.txt`](overleaf_projects.txt), one per line
   (`<project-id>  <label>`). The project ID is the last part of the project URL:
   `https://www.overleaf.com/project/<project-id>`. Commit the file.

   **Too many to list by hand?** Run the one-time bootstrap, which reads your
   browser session cookie and generates the file for you:
   ```
   python3 automation/bootstrap_overleaf_projects.py
   ```
   It prompts for your `overleaf_session2` cookie (DevTools → Application →
   Cookies → overleaf.com) without echoing it, and never uses that cookie in the
   weekly job — that stays on `OVERLEAF_TOKEN`. Re-run it any time to refresh.
3. **Adding a new project later:** add one line to `overleaf_projects.txt` and
   commit. That's the only per-project step — the account token already covers it.
   Projects with no changes in a given week are silently skipped.

### 5. Figures (drawn from your LaTeX's intent, verified before embedding)

Results **tables** need nothing — the drafter reproduces changed tables as
Markdown from the `.tex`. **Figures** are drawn only when you opt each one in:

1. Put a comment line `%@report` directly above the `\begin{figure}` you want in
   the report (change the marker with the `REPORT_FIGURE_TAG` env var if you like).
2. Each Friday, the drafting model reads each tagged figure's LaTeX/TikZ source,
   understands *at a high level* what it depicts and the information it must
   convey, and **draws a clean PNG** (graphviz for pipelines, matplotlib for
   plots). The goal is a plausible, legible rendering of the same information —
   **not** a pixel-faithful LaTeX compile.
3. It then **opens the PNG and analyses it fresh**: is it clear, and does it
   convey what the report needs? It regenerates if not, and embeds only figures
   that read clearly — noting any it left out. You get the final say in the PR,
   where every embedded figure shows in the diff.

Nothing to configure beyond the `%@report` tags.

### 6. Project sections (recommended)

The report is organised into **one section per research project**, and each
section's heading links to that project's page on `/projects/`. The mapping from
sources to projects lives in
[`report_projects.txt`](report_projects.txt), one project per line:

```
Display name | /projects/#anchor | pattern, pattern, ...
```

Each pattern is matched (case-insensitively, as a substring) against the GitHub
repository name *and* the Overleaf project label, so a repo like
`…/vc-experiments` or an Overleaf project labelled `ICASSP 2027` both land in the
same section. The `#anchor` is the project's heading on `/projects/`, lower-cased
with spaces as hyphens. Anything matching no project is reported under a generic
**Other** section with no link. Adding a new repo or paper to a project is a
one-line edit here (or a new line for a brand-new project — remember to add the
matching heading to [`site/projects.md`](../site/projects.md)).

### 7. Test it before trusting the schedule

Go to **Actions → Weekly research report → Run workflow** (the
`workflow_dispatch` trigger). It runs immediately and opens a PR you can inspect.
With only `CLAUDE_CODE_OAUTH_TOKEN` set, the report will be thin — it'll honestly
say it was a quiet week — but a green run that opens a PR proves the pipeline.

---

## Tuning

- **Time/day:** edit the `cron` in
  [`.github/workflows/weekly-report.yml`](../.github/workflows/weekly-report.yml).
  It's UTC.
- **Window:** set repo variable/secret `REPORT_WINDOW_DAYS` (default 7).
- **Model:** change `--model` in the `claude_args` line of the workflow (e.g.
  `claude-sonnet-5` to spend less of your subscription usage per run).
- **Style/accuracy rules:** edit `PINKER_STYLE` / `ACCURACY_RULES` in
  [`generate_report.py`](generate_report.py).
- **Local dry run:** with the same env vars set, `python automation/generate_report.py`
  gathers the material and writes the post shell + brief under `automation/_work/`,
  without drafting or opening a PR.

## Why a PR and not auto-publish

An LLM turning commit logs and metrics into prose will occasionally overstate a
result or infer a narrative that didn't happen. The brief forbids inventing
numbers, but on a public academic blog under your name the right safeguard is a
human read. The PR *is* that gate — merging is the publish action.
