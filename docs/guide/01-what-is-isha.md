# 01 · What ISHA Is — Plain-English Project Description

> One-liner: **ISHA is an autonomous AI software-engineering agent that takes a written
> bug report and returns a tested, reviewed, human-approvable patch — without anyone
> opening an editor.**

---

## The 30-second version

You paste a bug report like *"the subtract method returns a+b instead of a-b"*. ISHA:

1. **Reads the repository** — parses it into a compact AST map and indexes it for search.
2. **Plans** — a long-context LLM writes a 2-step root-cause plan.
3. **Proves the bug first** — it writes a regression test and runs it in a sandbox. Red.
4. **Patches** — an LLM emits a unified diff into an isolated git worktree.
5. **Retries itself** — sandbox test fails → trimmed traceback goes back to the coder, up to 3 times.
6. **Gets judged** — a calibrated on-device model (LAYA) scores the patch for quality,
   relevance and danger; a regex guardrail scans it for secrets/`eval`/`os.system`.
7. **Asks a human if needed** — flagged diffs pause at an approval gate with a JSONL audit log.
8. **Merges and reports** — the winning attempt is merged back, results exported.

Everything above runs from one command (`python src/main.py`) or one button in a
Streamlit dashboard.

---

## Why this project exists (the problem it solves)

Most "AI coding agent" demos show a single happy-path fix on a toy repo. That proves
very little, because **"the tests are green" ≠ "the bug is fixed"**:

- An agent can hard-code the expected answer instead of fixing the logic.
- It can rewrite or delete the failing test and declare victory.
- It can touch unrelated code and introduce a regression elsewhere.
- There's no proof the bug ever reproduced in the first place.

ISHA is built around the parts that make an autonomous fix *trustworthy* instead:

| Trust problem | How ISHA answers it |
|---|---|
| Was the bug real? | Regression test is written **before** the patch and must go RED→GREEN |
| Did it fix what was asked? | LAYA scores `matches_issue` + `fix_quality` against the original report |
| Did it break anything? | Sandbox runs the patch in an isolated copy, never the real repo |
| Is it dangerous? | Regex guardrail (secrets/eval/os.system) + LAYA `secrets_or_danger`/`logic_drift` |
| One bad attempt? | 3 strategies fan out in parallel git worktrees, LAYA arbitrates a winner |
| Who is accountable? | Human approval gate for flagged diffs → `approvals.jsonl` audit trail |
| Does it generalize? | Eval suite + SWE-bench Lite harness with exported JSON results |

---

## What it is NOT (be precise in interviews)

- **Not a fine-tuned model.** ISHA *orchestrates* off-the-shelf models (Gemini, Groq)
  plus a small on-device judgment model (LAYA). The engineering is in the loop, the
  state machine and the verification, not in training.
- **Not a chatbot.** There is no free-form conversation — it's a state machine with a
  defined start, defined nodes and a defined end.
- **Not yet an autonomous committer.** `--apply` writes the patch; commits are gated and
  logged. Containerised SWE-bench execution is scoped to "Next Steps".

---

## Project shape (numbers you can quote)

- ~**2,700 lines of Python** across **28 modules**, no framework scaffolding beyond LangGraph.
- **10 build phases**, one git branch/commit each, tagged `v1.0.0`.
- **2 graphs**: single-agent (7 nodes) and multi-agent (fan-out → arbitration → approval → merge).
- **2 seeded bugs** in the target fixture repo, **3 eval cases** → **3/3 resolved**.
- **LAYA judgment**: composite scores in the 0.83–0.86 band on real runs; danger detection
  **100%** on injected malicious patches in the SWE-bench judge run.
- **Fallback by design**: no API keys? the deterministic offline brain answers. No Qdrant?
  lexical retrieval answers. The pipeline never hard-fails.

---

## Where to look first

| You want… | Open |
|---|---|
| The entry point | `src/main.py` |
| The state machine | `src/agents/graph.py` |
| What data flows between nodes | `src/agents/state.py` |
| The judgment engine | `src/review/laya_judge.py` |
| Numbers/benchmarks | `tests/eval_suite.py`, `tests/swebench_runner.py` |
| The rest of this guide | [`02-ai-agent-explained.md`](02-ai-agent-explained.md) |
