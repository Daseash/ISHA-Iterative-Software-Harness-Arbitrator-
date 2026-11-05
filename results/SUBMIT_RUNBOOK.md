# A-1 SUBMISSION RUNBOOK (owner, ~10 minutes, browser needed)

> Payload: `isha-agent/results/all_preds.jsonl` — **213 rows, LINT PASS**
> (verify fresh before submitting: `python isha-agent/scripts/lint_all_preds.py` → expect `LINT PASS`)
> Ground-truth context: bundle dedup prefers graded > resolved > longest (P2-04);
> Docker-audited score today: 76/300 (report.json-proven). The run will re-grade
> all rows on SWE-bench's own servers and publish the official score.

## Steps

1. **Install GitHub CLI** (PowerShell, once):
   ```powershell
   winget install --id GitHub.cli
   ```
   New terminal after install (so PATH refreshes).

2. **Login** (opens browser):
   ```powershell
   gh auth login
   ```
   Choose: GitHub.com → HTTPS → "Login with a web browser". Copy the one-time
   code, approve in browser. Then `gh auth status` should say `Logged in to
   github.com as Daseash`.

3. **Open the PR** (PR_DRAFT body is ready; first line after `# Title` contains it):
   ```powershell
   cd C:\Users\Eashwar\ISHA
   gh pr create --repo Daseash/ISHA-Iterative-Software-Harness-Arbitrator- `
     --base main --head improve/...IS-already-merged-see-note `
     --title "..." --body-file isha-agent/results/PR_DRAFT.md
   ```
   NOTE: a same-branch PR (main→main) is impossible on GitHub; open the PR
   only if you have NEW commits on a branch. The pipeline/elapsed fixes are
   ALREADY MERGED (PR #2, commit c147407) — so this step is optional ceremony:
   skip unless you want a review page for future changes.

4. **Submit to the official leaderboard (SWE-bench Lite):**
   - Go to <https://www.swe-bench.github.io> (SWE-bench official site).
   - Click **"Submit"** / **"Log in with GitHub"** (OAuth popup, approve Daseash).
   - Follow the app flow: choose benchmark **SWE-bench Lite** → upload
     `C:\Users\Eashwar\ISHA\isha-agent\results\all_preds.jsonl` → submit.
   - Their grader runs official Docker tests on all 300; results appear on
     the Lite leaderboard under your GitHub handle (can take hours-days).

5. **Record the result (A-1 closes when):**
   - Paste the leaderboard URL + their official score into
     `MAKING_BETTER.md` Sec 1 (next to the PR evidence line), and tick
     Sec 10's "Lite300 >=75/300 Docker-graded + submitted PR link" row.
   - Keep A-2 discipline: quote ONLY their audited number in public claims.

## Common pitfalls
- Browser popup blocked: allow popups for github.com + swe-bench.github.io.
- Schema rejected: rerun the lint; do not hand-edit rows — rebuild with
  `python isha-agent/scripts/build_submit.py`.
- OAuth app not found: the site's GitHub App may be renamed; use the ""
  login button text as-is on the site (it authorizes by app id, not name).
