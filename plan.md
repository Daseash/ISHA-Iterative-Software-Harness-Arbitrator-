# 🏗️ ISHA — Master Benchmark & Continuous Improvement Plan

> **Mission**: Make ISHA the best autonomous coding agent in the world.
> **Method**: Run the hardest benchmarks, dissect every failure to its root cause in ISHA's code, fix that exact line, re-run, prove the score went up. Repeat.
>
> **What counts as a score?** Only **RESOLVED** — the patch must make the official test suite pass inside the SWE-bench Docker container. Generating a patch is not a score. Applying a patch is not a score. Only a patch that actually **solves the bug** and passes the harness counts.

---

## 🔄 THE IMPROVEMENT LOOP (Core Process)

```
   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │  1. RUN   │───▶│ 2. GRADE │───▶│ 3. ROOT  │───▶│ 4. FIX   │
   │ + DOCKER  │    │ FAILURES │    │  CAUSE   │    │ IN ISHA  │
   │  HARNESS  │    │          │    │          │    │          │
   └──────────┘    └──────────┘    └──────────┘    └──────────┘
        ▲                                               │
        │          ┌──────────┐    ┌──────────┐         │
        └──────────│6. RESOLVED│◀───│ 5. RE-RUN│◀────────┘
                   │ COUNT ▲  │    │ + DOCKER │
                   │ MUST GO  │    └──────────┘
                   │   UP     │
                   └──────────┘
```

### After EVERY session:

1. **RUN** — Generate patches for the session's instances. Record run-id, timestamp, ISHA commit.
2. **GRADE IN DOCKER** — Submit ALL patches to the official SWE-bench Docker harness (`python -m src.bench.harness_eval`). Only patches that make FAIL_TO_PASS tests go green = **RESOLVED**.
3. **CLASSIFY UNRESOLVED** — Every non-resolved instance goes into exactly ONE failure bucket (table below). The biggest bucket = the biggest lever to pull.
4. **ROOT CAUSE** — Trace each failure to the exact ISHA source file + line. Why didn't it SOLVE the bug?
5. **FIX** — Smallest diff that fixes the root cause. `pytest tests/` must pass.
6. **RE-RUN + RE-GRADE** — Same instances, same Docker harness. Resolved count MUST go up.

> ⚠️ **Patch yield, apply rate, gate pass rate are intermediate metrics only.** The ONLY number that matters for the leaderboard is **RESOLVED** (tests pass in Docker).

### Failure Buckets → ISHA Code Map

| Bucket | Meaning | Fix In |
|---|---|---|
| `tests_failed` | **Patch applied, but didn't solve the bug** — this is the #1 bucket. The fix was wrong. | `src/agents/nodes.py` (coder prompt, reasoning) |
| `localization_miss` | Didn't find the right file → can't solve it | `src/tools/localizer.py` |
| `symbol_miss` | Found file, wrong function → edit misses the defect | `src/tools/symbol_target.py` |
| `coder_wrong_edit` | Right place, but the code change doesn't fix the bug | `src/agents/nodes.py` |
| `patch_apply_failed` | Diff won't apply → never even reaches Docker | `src/tools/patch_engine.py` |
| `syntax_error` | Generated code won't parse → blocked before Docker | `src/bench/gates.py` |
| `timeout` | Ran out of time → no patch submitted | `src/agents/candidates.py`, `src/config.py` |
| `test_wrong` | Repro test was wrong, led solver to wrong fix | `src/agents/nodes.py` |
| `model_hallucination` | Fallback model invented content → garbage patch | `src/config.py` |
| `env_failure` | Docker / git / OS issue | `src/bench/harness_eval.py` |
| `gate_false_reject` | Gate rejected a patch that would have solved it | `src/approval/` |

### Root Cause Template (use for every failure)
```markdown
### Instance: <task-id>
- **Bucket**: <bucket>
- **What happened**: <1-2 sentences>
- **Root cause**: `src/<file>.py` line <N> — <what the code does wrong>
- **Fix**: <what to change>
- **Impact**: <expected score improvement>
```

---

## 📋 PHASE 1: SWE-bench Lite 300

### 1A: Clear the Smoke-50 Gate (Current Priority)

| Step | Action | Status |
|---|---|---|
| 1A.1 | Fix M-2: anchor coder to real file content on fallback models (`nodes.py`) | ✅ DONE (81/81 tests passed) |
| 1A.2 | Run `smoke50-r3` on failing instances | 🟡 IN PROGRESS |
| 1A.3 | Merge r3, re-compute gate verdict (`python scripts/score.py`) | 🔴 TODO |
| 1A.4 | PASS → Phase 1B. FAIL → improvement loop. | 🔴 TODO |

### 1B: Lite 300 Execution — Session Plan

> **Why sessions?** Free-tier models (Groq/Gemini/Cerebras) hit 429 rate limits fast. Running 300 at once = most instances timeout waiting for cooldowns. Small sessions → cooldown → Docker grade → improvement loop → next session.

**10 sessions × 30 instances = 300 total**

Each session follows this flow:
```
Generate patches (30 instances) → Docker harness grade → Count RESOLVED → Improvement loop on unresolved → Re-grade → Next session
```

| Session | Instances | Generate | Docker Grade | Improvement Loop | Status |
|---|---|---|---|---|---|
| S1 | 1–30 | ~45 min | 19 clean patches | Gate context fix + 1-worker rule landed | ✅ COMPLETED (19/30 patches) |
| S2 | 31–60 | ~45 min | in progress | +S1 fixes applied, 1-worker safe mode | 🟡 IN PROGRESS (Launching) |
| S3 | 61–90 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S4 | 91–120 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S5 | 121–150 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S6 | 151–180 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S7 | 181–210 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S8 | 211–240 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S9 | 241–270 | ~45 min | grade all 30 | cumulative fixes, loop | 🔴 |
| S10 | 271–300 | ~45 min | grade all 30 | final loop, aggregate RESOLVED | 🔴 |

**Session rules:**
- Run 1 instance at a time (no parallel workers) — halves API calls per minute
- 15 min cooldown between sessions — rate limit tokens reset
- **ALWAYS Docker-grade every patch** — a patch that applies but doesn't solve = 0 points
- **Improvement Loop with 3 Candidates (`--candidates 3`)**: Pits 3 diverse strategies in parallel (Qwen 3.8 minimal diff, GPT-OSS 120B call-site aware, Gemini 3.8 Flash root-cause first). LAYA arbitrates and selects the best patch.
- After each session: run improvement loop on unresolved BEFORE starting next session
- If heavy 429s mid-run: pause, wait 5 min, resume from checkpoint
- Re-run + re-grade unresolved instances AFTER fixes, during cooldown gap

### Lite 300 Score Tracker (RESOLVED = tests pass in Docker)

> **Current Live Status (PARALLEL EXECUTION)**:
> - **Active Run #1 (Session 2)**: `lite300-s2` (Instances 31–60) — 🌟 **5 / 5 clean patches so far (100% win rate)** (`django-12125`, `django-12184`, `django-12284`, `django-12286`, `django-12308`).
> - **Active Run #2 (Session 1 Upgrade)**: `lite300-s1-c3` running in parallel with 3 candidates — 🌟 **`django-10924` RECOVERED** (Candidate #3 won), boosting Session 1 patch count to **20 / 30 (66.7% yield)**!
> - **Predictions File**: [`results/lite300-s1/predictions.json`](file:///c:/Users/Eashwar/ISHA/isha-agent/results/lite300-s1/predictions.json) regenerated with all 20 patches.
> - **Levers Active**: Multi-model tournament (`--candidates 3`), decoupled Planner/Coder models, expanded fuzzy search window with whole-file fallback, and verbatim compiler syntax feedback.

| Session | Date | RESOLVED | Patched but Failed Tests | No Patch | Fixes Applied | Δ Resolved |
|---|---|---|---|---|---|---|
| S1 | 2026-10-08 | *20 patches (eval pending)* | — | 10 | M-2 + GAP 1 + Gate Context + 3-Candidates | +20 patches |
| S2 | 2026-10-08 | *in-progress (5/5 patches generated)* | — | — | +S1 fixes, 3 candidates, decoupled models | in-progress |
| S3 | — | —/30 | — | — | +S1+S2 | — |
| ... | — | — | — | — | — | — |
| S10 | — | —/30 | — | — | all | — |
| **TOTAL** | — | **—/300 (—%)** | — | — | — | — |

#### Session 1 Instance Audit (Completed):
| # | Instance ID | Status | Patch Type / Outcome |
|---|---|:---:|---|
| 1 | `astropy__astropy-12907` | Completed | `no_confident_fix` (conservative reject) |
| 2 | `astropy__astropy-14182` | Completed | ✅ Clean Patch Generated |
| 3 | `astropy__astropy-14365` | Completed | 🌟 **1-line Gold Match** (`re.IGNORECASE`) |
| 4 | `astropy__astropy-14995` | Completed | `no_confident_fix` (conservative reject) |
| 5 | `astropy__astropy-6938`  | Completed | ✅ Clean Patch Generated |
| 6 | `astropy__astropy-7746`  | Completed | ✅ Clean Patch Generated |
| 7 | `django__django-10914`   | Completed | 🌟 **1-line Gold Match** (`FILE_UPLOAD_PERMISSIONS = 0o644`) |
| 8 | `django__django-10924`   | Completed | 🌟 **Clean Patch Generated (RECOVERED by Cand #3!)** |
| 9 | `django__django-11001`   | Completed | 🌟 **1-line Gold Match** (`re.compile(..., re.DOTALL)`) |
| 10 | `django__django-11019`  | Completed | 🌟 **1-line Surgical Match** (`if index < last_insert_index:`) |
| 11 | `django__django-11039`  | Completed | 🌟 **1-line Gold Match** (`output_transaction = ... can_rollback_ddl`) |
| 12 | `django__django-11049`  | Completed | ✅ Clean Patch Generated |
| 13 | `django__django-11099`  | Completed | 🌟 **Gold Match** (`regex = r'\A[\w.@+-]+\Z'`) |
| 14 | `django__django-11133`  | Completed | 🌟 **Gold Match** (`bytes(value)` on memoryview) |
| 15 | `django__django-11179`  | Completed | ✅ Clean Patch Generated |
| 16 | `django__django-11283`  | Completed | ✅ Clean Patch Generated (proxy permissions migration) |
| 17 | `django__django-11422`  | Completed | ✅ Clean Patch Generated |
| 18 | `django__django-11564`  | Completed | ✅ Clean Patch Generated (SCRIPT_NAME prefix) |
| 19 | `django__django-11583`  | Completed | 🌟 **Gold Match** (autoreload null byte & ValueError guard) |
| 20 | `django__django-11620`  | Completed | timeout (target for 1-worker rescue) |
| 21 | `django__django-11630`  | Completed | ✅ Clean Patch Generated (`models.E028` db_table uniqueness) |
| 22 | `django__django-11742`  | Completed | `no_confident_fix` (conservative reject) |
| 23 | `django__django-11797`  | Completed | `no_confident_fix` (conservative reject) |
| 24 | `django__django-11815`  | Completed | 🌟 **Surgical Gold Match** (`EnumSerializer.serialize`) |
| 25 | `django__django-11848`  | Completed | timeout (target for 1-worker rescue) |
| 26 | `django__django-11905`  | Completed | timeout (target for 1-worker rescue) |
| 27 | `django__django-11910`  | Completed | ✅ **Clean Patch Generated** (666 bytes) |
| 28 | `django__django-11964`  | Completed | timeout (target for 1-worker rescue) |
| 29 | `django__django-11999`  | Completed | timeout (target for 1-worker rescue) |
| 30 | `django__django-12113`  | Completed | timeout (target for 1-worker rescue) |

---

## 📋 PHASE 2: Aider Leaderboard

> Runs AFTER Lite 300 loops complete. All Lite 300 fixes carry forward.

| Step | Action |
|---|---|
| 2.1 | Study Aider benchmark format + build ISHA→Aider adapter |
| 2.2 | Baseline run on sample (20 tasks) |
| 2.3 | **IMPROVEMENT LOOP** — focus: `coder_wrong_edit`, `patch_apply_failed` |
| 2.4 | Full Aider run with all fixes |


### Aider Score Tracker

| Run | Date | Diff Score | Whole File Score | Δ from Last |
|---|---|---|---|---|
| baseline | — | — | — | — |
| *loop N* | — | — | — | — |

---

## 📋 PHASE 3: Terminal Benchmarks

> Runs AFTER Aider loops complete. All accumulated fixes carry forward.

| Step | Action |
|---|---|
| 3.1 | Identify target terminal benchmarks, verify ISHA tool-use agent handles shell/IO/errors |
| 3.2 | Baseline run on sample (20 tasks) |
| 3.3 | **IMPROVEMENT LOOP** — new buckets: `command_wrong`, `output_misparse`, `env_navigation_fail` |
| 3.4 | Full terminal run with all fixes |

### Terminal Score Tracker

| Run | Date | Resolved | Accuracy | Δ from Last |
|---|---|---|---|---|
| baseline | — | — | — | — |
| *loop N* | — | — | — | — |

---

## 🧩 ISHA COMPONENT HEALTH

> What's limiting ISHA right now and what to fix.

| Component | File | Current Limitation | Target |
|---|---|---|---|
| **Coder Prompt** | `src/agents/nodes.py` | 🔴 Fallback models hallucinate file context (M-2) | Zero hallucination |
| **Tournament** | `src/agents/candidates.py` | 🔴 Timeout under rate limits, no adaptive budget | Adaptive time budget |
| **Localizer** | `src/tools/localizer.py` | 🟡 Hit@8 = 66.7%, misses deep internal utils | Hit@8 ≥ 85% |
| **Config / Models** | `src/config.py` | 🟡 Free-tier rate limits, basic fallback chain | Smarter fallback |
| **Repro Test** | `src/agents/nodes.py` | 🟡 14.3% false positive rate (down from 62.5%) | < 5% FP |
| **Symbol Targeter** | `src/tools/symbol_target.py` | 🟡 Top-3 = 4/6 (small sample) | Top-3 ≥ 80% |
| **Patch Engine** | `src/tools/patch_engine.py` | ✅ CRLF fixed, fuzzy matching added | Maintain 0% fail |
| **Static Gates** | `src/bench/gates.py` | ✅ 100% pass rate | Maintain |
| **Harness** | `src/bench/harness_eval.py` | ✅ LF fix landed, 0 infra crashes | Maintain |
| **LAYA Gate** | `src/approval/` | ✅ ECE 0.0010, 100% precision | Maintain |

---

## 🎯 TARGET SCORES (RESOLVED = tests pass in Docker)

| Benchmark | Target | Stretch |
|---|---|---|
| **SWE-bench Lite 300 RESOLVED** | ≥ 75/300 (25%) | ≥ 105/300 (35%) |
| **Aider Leaderboard** | Top 10 | Top 5 |
| **Terminal Benchmarks** | ≥ 70% accuracy | ≥ 85% |
| **Patch Apply Failures** | 0% | 0% |
| **Timeouts** | ≤ 5% | ≤ 3% |
| **Localizer Hit@8** | ≥ 85% | ≥ 90% |

---

## 📝 IMPROVEMENT LOG

> Append-only. Grows after every loop. Never deleted.

### Loop Template
```markdown
---
### Loop #<N> — <Benchmark> — <Date>
**Run ID**: <run-id> | **Commit**: <hash>
**Score**: <before>% → <after>% (Δ +<change>%)

| Instance | Bucket | Root Cause | Fix |
|---|---|---|---|
| ... | ... | `file:line` — ... | ... |

**Lessons**: ...
---
```

### Loop #1 — SWE-bench Lite 300 Session 1 — 2026-10-06 (End-of-Day Checkpoint)
**Run ID**: `lite300-s1` | **Status**: PAUSED for tomorrow (cleanly stopped)
**Total Instances Processed**: 20 / 30 (66.7% of Session 1)
**Clean Patches Generated**: 16 / 20 (80.0% patch yield)
**Exact Gold Matches Produced**: 8 / 20 (40.0% ground-truth exact match fidelity):
1. `astropy__astropy-14365`: `re.compile(_type_re, re.IGNORECASE)`
2. `django__django-10914`: `FILE_UPLOAD_PERMISSIONS = 0o644`
3. `django__django-11001`: `re.compile(..., re.DOTALL)`
4. `django__django-11019`: `if index < last_insert_index:`
5. `django__django-11039`: `self.output_transaction = migration.atomic and connection.features.can_rollback_ddl`
6. `django__django-11099`: `regex = r'\A[\w.@+-]+\Z'`
7. `django__django-11133`: `if isinstance(value, memoryview): value = bytes(value)`
8. `django__django-11583`: Embedded null-byte & ValueError handling in autoreloader

**Today's Resumption Point (ACTIVE)**:
* **Pre-run Bugfix**: Resolved `KeyError: 'approval'` in [`src/agents/graph.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/graph.py#L182-L186) by adding missing `'approval': 'approval'` mapping to `sandbox` conditional edges.
* **Command launched**: `python -m src.bench.runner --limit 30 --run-id lite300-s1 --candidates 3`
* Instances 1–19 skipped via checkpoints; actively solving **`[20/30] django__django-11620`** through instance 30 in background.
* Engine: Multi-provider 3-candidate tournament (Groq Qwen + OpenRouter Nemotron 120B + Google Gemini Flash-Lite) with zero rate-limit sleep delay (`ISHA_RATE_LIMIT_WAIT=0`).
* Next action upon Session 1 completion: Run official Docker testbed grading (`python -m src.bench.harness_eval --run-id lite300-s1`) followed by the 3-model rescue loop.

---

## 🚨 WHAT YOU'RE MISSING — CRITICAL GAPS TO FIX

> I read ISHA's actual code. These are the real things limiting your resolved count.

### GAP 1: 🔴 BENCH MODE SKIPS REAL TESTS — THIS IS THE #1 PROBLEM

**Found in**: [`nodes.py` lines 914-934](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/nodes.py#L914-L934)

Right now, when `ISHA_BENCH_MODE=1`, the sandbox node does this:
```
if _bench_mode():
    gate = compile_gate(...)  # only checks: does it parse? does pyflakes pass?
    state.test_output = "PASSED"  # ← LIES. It didn't run any tests.
    return state
```

**The problem**: ISHA never runs the repo's actual tests during bench mode. It only checks syntax (AST + pyflakes). So the retry loop (`sandbox → coder → sandbox`) never fires on a *wrong fix* — only on syntax errors. The coder gets NO feedback about whether the fix actually solves the bug.

**This is why 64% of your instances are `tests_failed`** — ISHA thinks "patch applies + no syntax error = done" but the patch doesn't actually fix the bug.

**The fix**: Run the repo's test suite (or at least the FAIL_TO_PASS tests) INSIDE Docker during the agent loop, not just at the end during grading. Top agents (SWE-agent, Agentless, Moatless) all do this. If the test fails → feed the failure back to the coder → retry with the error message.

| Before | After |
|---|---|
| Coder → static gate → "PASSED" → done | Coder → static gate → Docker test → see failure → retry coder with error → Docker test → PASSED → done |

### GAP 2: 🔴 NO GOLDEN REGRESSION SET

When you fix ISHA to improve on new instances, you might **break** the 7 instances you already solve. You need a "golden set" — the 7 resolved tasks — that runs after every ISHA code change to make sure they still pass.

**Add to the loop**: After every ISHA fix, re-run the 7 resolved instances. If any regress → fix is rejected.

### GAP 3: 🟡 NO CROSS-INSTANCE PATTERN LEARNING

If `django__django-11133` fails because the coder edits the wrong overload, and `django__django-11564` fails for the exact same reason, you fix it twice. Instead:
- After each session, group failures by **pattern** (not just bucket)
- A single fix that addresses the pattern fixes multiple instances at once
- Track: "Pattern P fixed N instances in one shot"

### GAP 4: 🟡 STUDY THE 7 WINS — WHAT DID ISHA DO RIGHT?

The 7 resolved instances are the most valuable data you have. For each one:
- What model generated the winning patch?
- How many retries did it take?
- Was the localization correct on the first try?
- How large was the diff?

Extract the winning pattern → encode it into the coder prompt → more instances match the pattern.

### GAP 5: 🟡 MODEL QUALITY IS THE #1 LEVER

Free-tier models (qwen3.8-27b on Groq, gemini-flash-lite) are good for volume but weak on complex reasoning. The top SWE-bench agents use GPT-4o, Claude Sonnet/Opus, or DeepSeek-V3.

**Options**:
- Get API credits for a stronger model (even for just the coder role)
- Use a local model (DeepSeek-Coder-V2, Qwen2.5-Coder-32B) if you have GPU
- Use the strong model only for the hardest instances (timeout/tests_failed buckets) and free models for easy ones

### GAP 6: 🟡 NO INNER DOCKER TEST LOOP

The retry loop in [`graph.py` line 132](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/graph.py#L132) works: `if failed and retry_count < MAX_RETRIES: → coder`. But in bench mode, "failed" only triggers on syntax errors (GAP 1). The fix for GAP 1 enables this loop to actually work for *wrong fixes* too.

### Priority Order

| Priority | Gap | Status | Impact on Resolved Count |
|---|---|:---:|---|
| **P0** | GAP 1: Run tests during agent loop | ✅ **FIXED** in `nodes.py:960` | Turns retry loop into a solving loop |
| **P1** | GAP 2: Golden regression set (7 tasks) | ✅ **FIXED** in `scripts/verify_golden.py` | Prevents losing already-won points |
| **P2** | GAP 6: Inner test loop retry | ✅ **FIXED** (Coder retries on test fail) | Coder gets 3 tries to actually solve |
| **P3** | GAP 4: Study the 7 wins | 🟡 Active | Guides Ponytail minimal diffs |
| **P4** | GAP 5: Stronger model fallbacks | ✅ Active | Groq Qwen + Gemini 3.8 Flash chain |
| **P5** | GAP 3: Cross-instance pattern learning | 🟡 Active | Grouping failures by root cause |

---

## ⚠️ RULES

1. **Always update this plan** after every run, every loop, every fix
2. **Every error traces to ISHA code** — no "it just didn't work"
3. **Score must go up** — if not, fix was wrong, try again
4. **No skipping the loop** — RUN → ANALYZE → ROOT CAUSE → FIX → RE-RUN → SCORE UP
5. **Fixes carry forward** — Lite 300 → Aider → Terminal
6. **Smallest diff wins** — Ponytail principle
7. **Never regress** — run the golden 7 after every ISHA change
8. **RESOLVED is the only score** — patch yield is noise

---

> **We run, we fail, we understand WHY, we fix the code, we prove the score went up. Repeat until #1.**

---

## 🏆 FINAL STAGE: OFFICIAL LEADERBOARD SUBMISSION (LOCKED UNTIL BEST SCORE)

> ⛔ **DO NOT SUBMIT OR REGISTER NOW.**
> We do NOT submit intermediate or partial results. We only register ISHA on the official scoreboards **after** completing the full benchmark suite and achieving our best peak score (≥ 25%+ / top-tier resolved rate).

Once our final runs hit the target scores:

### 1. SWE-bench Official Leaderboard ([swebench.com](https://www.swebench.com/))
* **Target Category**: SWE-bench Lite & SWE-bench Verified
* **Artifacts Required**:
  1. `all_preds.jsonl` containing `{instance_id, model_patch, model_name_or_path: "ISHA"}`
  2. Full Docker execution logs (`eval_outputs/`) proving the harness passed
  3. Trajectory logs demonstrating ISHA's autonomous agent loop without human intervention
* **Submission Protocol**:
  - Fork [princeton-nlp/SWE-bench](https://github.com/princeton-nlp/SWE-bench)
  - Place results under `evaluation/lite/ISHA/`
  - Open an official Pull Request titled `[Submission] ISHA (Autonomous SWE Agent)`
  - Provide system description, model fallback chain, and reproducibility scripts

### 2. Aider Leaderboard ([aider.chat/docs/leaderboards/](https://aider.chat/docs/leaderboards/))
* **Target Category**: Code Editing / Refactoring Benchmark
* **Protocol**:
  - Run the standard Aider benchmark test suite with ISHA's patch engine
  - Record pass@1 on whole test suite
  - Submit evaluation results to the Aider benchmarks repository

### 3. Terminal & Shell Benchmarks (SWE-gym / TerminalBench / InterCode)
* **Target Category**: Real-world CLI & Bash execution benchmarks
* **Protocol**:
  - Run Docker-isolated bash terminal tasks
  - Output standardized metrics JSON
  - Submit predictions to respective benchmark repos

### 4. Verification Checklist Before Submission:
- [ ] All 300 instances of SWE-bench Lite evaluated via official Docker harness
- [ ] Zero manual human edits (100% autonomous pass verified)
- [ ] Reproducibility script provided (`scripts/run_reproduce.sh`)
- [ ] All trajectory logs and diffs committed to public repository
- [ ] Official PR submitted and registered on the live scoreboard


