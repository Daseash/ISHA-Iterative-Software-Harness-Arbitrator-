# ISHA Benchmark Runbook — SWE-bench Lite, full 300, pass@1

The runbook is the complete, copy-paste process from a clean machine to a
publishable full-300 number. Every command has been checked against the
v0.3.0 code. If a step fails, see the decision table at the bottom.

**Headline metric**: `resolved / 300` from the *official* SWE-bench harness
(`harness_report.json`), pass@1. This is the same metric Agentless,
OpenHands and SWE-agent report on this split — the only number that makes a
"top free agent" claim defensible.

---

## 0. Ground rules (non-negotiable)

1. The solver never sees `gold_patch` / `test_patch` — enforced by
   `src/bench/dataset.py:agent_view`.
2. One run = one prompt/budget profile. The numbers below are produced with
   the **v0.3.0 defaults** (`docs/PIPELINE.md` §5). Do not mix profiles inside
   a run; if you must resume after a config change, use a new `--run-id`.
3. Every metric in the README carries its source file under `results/`.
   Nothing is hand-entered (`src/bench/report.py` derives everything from
   per-instance `meta.json`).

---

## 1. Prerequisites

```powershell
cd C:\Users\Eashwar\ISHA\isha-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .            # installs `isha` CLI
python -m pip install swebench docker   # official harness + Docker client
docker pull isha-sandbox:latest 2>$null; docker compose up -d qdrant
copy .env.example .env      # add GROQ_API_KEY / GOOGLE_API_KEY (free tiers)
```

## 2. Doctor (must be ALL CLEAR before spending quota)

```powershell
isha doctor
```

Checks: python, git, keys, disk (≥15 GB free), SWE-bench Lite cache
(300 instances), checkout mirrors, LAYA combiner status.

## 3. Smoke — 1 instance, end-to-end (≈15 min, ~free)

```powershell
isha bench --limit 1 --run-id smoke --report
```

Must produce: `results/smoke/<instance>/meta.json` with `status: done`,
a non-empty `model_log` (no `offline` entries), and either a patch or a
classified failure. **If the only model in the log is `offline-brain`, stop —
API keys are not being read.**

## 4. Smoke — 50-instance stratified slice (≈10-16 h, parallel-safe)

```powershell
isha bench --limit 50 --slice stratified --run-id smoke50 --workers 1 --report
```

Pass criteria before spending the full 300:

| Check | Bar | Where |
|---|---|---|
| Timeout rate | < 15% of instances | stage table in the report |
| `api_failure` / `offline` calls | < 5% | `meta.json → model_log` |
| Patch yield | ≥ 40% | stage table |
| No CRLF/harness aborts | 0 | stage table |

If 429s dominate: lower the prompt profile (PIPELINE §5 low-bandwidth), do NOT
raise `--workers` (one account = one shared TPM window).

## 5. The full 300

```powershell
isha bench --limit 300 --slice head --run-id lite300 --workers 1
```

- Resumable: re-running the same command skips finished instances
  (checkpoints in `results/lite300/<instance>/meta.json`).
- Run it in a terminal that survives reboots; a stopped run resumes for free
  (and every answered LLM call is disk-cached, so resuming re-burns almost no
  quota).
- Expected wall-clock on one account: **~65-100 h of pure solving**, which on
  free-tier quota translates to daily sprints — a healthy day does 60-100
  instances, a congested one 10-30. Plan the calendar in days, not hours
  (`plan.md` Rate-Limit War Plan has the observed 2026-10-01 numbers).

## 6. Grade with the official harness (Docker)

```powershell
isha bench --limit 300 --run-id lite300 --eval --eval-workers 2
# or, if the run finished separately:
python -m src.bench.harness_eval --run-id lite300 --max-workers 2
```

- One eval image per instance (~4 GB); `--keep-images` only for debugging.
- Output: `results/lite300/harness_report.json` → `resolved_ids`,
  `resolved_instances`, `total_instances`.
- **The headline number is `resolved_instances / 300`** (denominator = the
  whole slice, empty patches included — `harness_eval.py:main` enforces this).

## 7. Report, plot, relabel

```powershell
isha report --run-id lite300 --compare baseline   # table + Wilson CIs
python -m src.bench.make_plots                    # assets/isha_vs_baselines.png
python -m src.bench.relabel_laya --run-id lite300 # real LAYA labels + refit
```

`relabel_laya` writes `data/laya_labels_real.jsonl` (labels = real harness
verdicts on ISHA's own patches), backs up the synthetic combiner to
`data/laya_combiner_synthetic.json`, refits `data/laya_combiner.json`, and
writes `results/calibration_real.json`. **From this point on, the README cites
the real-label calibration.**

## 8. Real-world deployment test (outside the benchmark)

See `scripts/realworld.py`. Protocol: pick 5-10 *live* Python GitHub issues
from repos that are NOT in SWE-bench, clone, run `isha fix --apply`, and record
(human-verified) resolution. This is the "trustworthy in practice" evidence —
benchmark ≠ real world, and the README says so.

```powershell
python scripts/realworld.py --cases scripts/realworld_cases.json
```

## 9. Update the README (last, only with measured numbers)

- Full-300 pass@1 + Wilson CI from `results/lite300/harness_report.json`.
- Stage table from `isha report`.
- Real-label LAYA calibration from `results/calibration_real.json`.
- Keep the *Limitations* section — it is what makes the numbers credible.

---

## Decision table — when a run misbehaves

| Symptom | Diagnosis | Action |
|---|---|---|
| Most instances `timeout` with long `model_log` chains | rate limits eat the 30-min budget | use low-bandwidth prompt profile; keep `--workers 1` |
| `offline-brain` entries in `model_log` | keys not loaded / provider dead for the session | restart the run (provider state resets per instance); verify `isha doctor` |
| Many `patch_apply_failed` | context drift in model diffs | already mitigated (verbatim-feedback retry); check `results/apply_failures/` |
| `harness_no_output` | CRLF into the container | `install_lf_writes` is automatic; if it recurs, check the Windows Docker FS layer |
| Harness step stalls on image pull | disk / Docker | `docker system prune`, ensure ≥15 GB free |
| One instance loop-retries forever | graph retry budget | it cannot: `MAX_RETRIES=3` + per-instance timeout; kill & resume (checkpoint) |
| Want faster wall-clock, have 2+ provider accounts | throughput-bound | `--workers 2` (each account's TPM window is separate) |

---

## What "top" means here (be honest in the README)

- Compare pass@1 on SWE-bench Lite (full 300) against published open agents:
  Agentless ≈ 32.6%, SWE-agent ≈ 37%, OpenHands ≈ 38% (published figures;
  verify current values before printing — the leaderboard moves).
- ISHA's differentiators are **$0 inference cost**, **zero apply failures**,
  and a **calibrated ship/review gate** — state those next to the pass@1, not
  instead of it.
- A 30-instance DEV slice (3.3% resolve) is what the repo currently proves.
  The full-300 run is what turns the claim from "promising" into "top".
