# Automated weekly research report

Every Friday a GitHub Action drafts a progress report in the classic
(Steven-Pinker) prose style, pulling from three sources, and **opens a pull
request**. Nothing is published until you review and merge it.

```
  TITAN (Thu cron)                    GITHUB ACTIONS (Fri 08:00 UTC)
  weekly_collect.py  ── git push ──▶  generate_report.py
   • scan results dir                  1. clone Titan report repo
   • metrics + plots                   2. clone Overleaf (git bridge) → diff .tex
   • report-YYYY-Www.md                3. GitHub API → week's commits & PRs
                                       4. Claude (opus-4-8) → Pinker-style draft
                                       5. write site/_posts/…-weekly-report-*.md
                                       6. open PR  ──▶  you review & merge ──▶ Pages deploy
```

The draft post is created with `crosspost: false`, so a weekly report never
propagates to the Gaelg AI blog unless you flip that to `true` while reviewing.

---

## One-time setup

### 1. GitHub repository secrets

In this repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add:

| Secret | What it is | Required? |
|--------|-----------|-----------|
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com | **Yes** |
| `GH_REPORT_TOKEN` | Fine-grained PAT with **read** access to your repos' contents (so it can list the week's commits/PRs). Create at github.com → Settings → Developer settings → Fine-grained tokens. | Recommended |
| `OVERLEAF_GIT_URL` | Your Overleaf project's git URL **with token embedded** — see below | Optional |
| `TITAN_REPORT_REPO` | git URL of the repo the Titan collector pushes to | Optional |
| `TITAN_REPORT_TOKEN` | PAT with read access to that repo, **if it is private** | Only if private |

Any optional source you leave unset is simply skipped — the report is built from
whatever is available.

### 2. Overleaf git URL

Overleaf → your project → **Menu → Git**. You'll get a URL like
`https://git.overleaf.com/<project-id>` and a git token. Combine them into the
secret value:

```
https://git:<your-overleaf-git-token>@git.overleaf.com/<project-id>
```

### 3. Titan side

1. Create a **private** git repo for the reports, e.g. `weekly-reports`, and set
   `TITAN_REPORT_REPO` (and `TITAN_REPORT_TOKEN`) to it.
2. On Titan, clone that repo somewhere writable and make sure `git push` works
   there (SSH key or a stored token).
3. Copy [`titan/weekly_collect.py`](titan/weekly_collect.py) to Titan and edit
   the two `ADAPT:` blocks so it reads **your** metrics and plots.
4. Add a weekly cron (`crontab -e`), Thursday 20:00, so the report is ready
   before Friday's run:
   ```cron
   0 20 * * 4 cd /home/chris/automation && /usr/bin/python3 weekly_collect.py \
       --results-dir /data/chris/experiments \
       --report-repo /path/to/weekly-reports >> collect.log 2>&1
   ```

### 4. Test it before trusting the schedule

Go to **Actions → Weekly research report → Run workflow** (the
`workflow_dispatch` trigger). It runs immediately and opens a PR you can inspect.

---

## Tuning

- **Time/day:** edit the `cron` in
  [`.github/workflows/weekly-report.yml`](../.github/workflows/weekly-report.yml).
  It's UTC.
- **Window:** set repo variable/secret `REPORT_WINDOW_DAYS` (default 7).
- **Model or style:** `REPORT_MODEL` env, or edit `PINKER_SYSTEM_PROMPT` in
  [`generate_report.py`](generate_report.py).
- **Local dry run:** with the same env vars set, `python automation/generate_report.py`
  writes the post into `site/_posts/` without opening a PR.

## Why a PR and not auto-publish

An LLM turning commit logs and metrics into prose will occasionally overstate a
result or infer a narrative that didn't happen. The system prompt forbids
inventing numbers, but on a public academic blog under your name the right
safeguard is a human read. The PR *is* that gate — merging is the publish action.
```
