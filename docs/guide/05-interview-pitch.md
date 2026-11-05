# 05 · Interview Pitch — what to say, what you can claim, what they'll ask

## The pitches

### 20 seconds (elevator / screening call)
> "I built **ISHA**, an autonomous AI software-engineering agent. You give it a bug
> report and it plans a fix, writes a regression test *first*, patches in an isolated
> git worktree, self-corrects against failing tests, and has every patch judged by an
> on-device model that returns calibrated probabilities instead of text opinions. Three
> strategies run in parallel and are arbitrated, and anything flagged stops at a human
> approval gate with an audit log."

### 60 seconds (recruiter / first-round)
> "Most AI agent demos show one happy-path fix on a toy repo. I wanted to build the
> parts that make autonomous fixes *trustworthy*, so ISHA does four things differently.
>
> **First, prove-before-patch** — the agent must write a test that fails on the current
> code before it's allowed to touch anything, so 'green tests' actually means the bug
> is gone. **Second, isolation** — three fix strategies run in parallel in separate git
> worktrees, so they can't clobber each other, and a LangGraph fan-out/fan-in graph
> arbitrates the best attempt by score. **Third, calibrated judgment** — instead of
> asking an LLM 'is this good?', I integrated LAYA, an on-device decision engine that
> answers typed questions (fix quality, does it match the issue, is it safe) with
> probabilities I can threshold and rank; a regex guardrail independently scans for
> secrets and dangerous calls. **Fourth, bounded autonomy** — flagged diffs stop at a
> human gate with a JSONL audit trail, and the whole loop degrades gracefully: no API
> keys, it falls back to a deterministic brain; no vector DB, it falls back to lexical
> search.
>
> It's about 2,700 lines across 28 modules, ten build phases with a commit each, and it
> ships with an eval suite (3/3 on my fixtures) plus a SWE-bench Lite harness that
> measures the judge's discrimination, not just its accuracy."

### 2 minutes (technical deep-dive, expect to be stopped here)
Walk the state machine: `planner → regression_test → coder → sandbox ⇄ critic → approval → merger`,
mention the four LangGraph gotchas you solved (node-name dedup of parallel Sends, `_last`
reducers for concurrent writes, `Send` payloads arriving as dicts, keeping branch state
inside a single `attempt` node), then the judgment layer (typed questions, composite
score, single inference lock), then the evaluation story and the honest limitations.

---

## Skills you can legitimately claim expertise in

| Claim level | Area | Evidence in the repo |
|---|---|---|
| **Strong** | Agent orchestration / state machines | `graph.py` (2 graphs), retries, fan-out/fan-in, interrupts |
| **Strong** | Multi-agent isolation & arbitration | `worktree_manager.py`, `dispatch.py`, `arbitration.py` |
| **Strong** | LLM integration & resilience | `config.py` — routing, fallback chains, offline degradation, litellm |
| **Strong** | Evaluation & benchmarking | `eval_suite.py`, `swebench_runner.py`, negative-control design |
| **Strong** | Safety / guardrails / HITL | `scanner.py`, `rails.co`, `approval/gate.py` + audit log |
| **Solid** | RAG & code intelligence | parser, tree-sitter AST map, Qdrant indexer/retriever + fallback |
| **Solid** | Observability & product surface | Streamlit dashboard, approvals export, Langfuse wiring |
| **Working** | Systems/Git internals | worktrees, `git apply --3way`, patch fallback applier |

**Do not claim:** model training/fine-tuning, production multi-tenant scale, container
orchestration (Docker is explicitly *not* integrated), or a verified SWE-bench score.

---

## Likely questions → short answers

**Q: Why LangGraph instead of just a Python loop?**
Cycles with conditional edges, checkpointed state per thread (resume/approval flows),
and built-in parallel `Send` fan-out. I hit real issues with it — parallel Sends being
deduped by node name and concurrent state writes — and solved both, which I can walk through.

**Q: Why ask a *model* to judge instead of just running the tests?**
Tests tell you the patch didn't break known behaviour; they can't tell you the patch
addresses the *reported* issue, or that it didn't hard-code a case or drift into
unrelated edits. LAYA gives me a calibrated `matches_issue`/`fix_quality`/`safe_to_apply`
triple I can threshold (`<0.4 → low_quality`) and rank candidates by — and it's a single
forward pass, no text parsing, no extra token cost.

**Q: What happens when the model returns garbage?**
Guardrails in layers: the sandbox never touches the real repo; `FAILED` output feeds a
trimmed traceback back to the coder up to 3 times; the patch must still apply
(`git apply --3way` + fallback); regex guardrails hard-block secrets/`eval`/`os.system`;
LAYA can flag; humans gate anything flagged. And if the API is down entirely, a
deterministic brain produces a valid plan/test/diff so the demo still runs.

**Q: Is it actually autonomous if a human approves?**
It's autonomous within a boundary I chose: routine, passing, LAYA-clean patches merge
automatically; anything flagged waits. That's the trade I'd want in production — full
autonomy on the happy path, accountability on the risky one.

**Q: How do you know it works?**
Three layers: unit tests for the platform, an eval suite on seeded bugs (3/3, patch
applied to a pristine copy and verified by the target test class going green), and a
SWE-bench Lite harness that scores the *judge* against negative controls — golden,
inverted, unrelated, and malicious patches. Current numbers: danger detection 100%,
golden approval 67%, all-four-correct 33%. I report those as measured, not rounded up.

**Q: What would you do next?**
Containerised SWE-bench execution for a comparable resolution rate, real vector
retrieval (Qdrant is currently falling back to lexical), and Langfuse-backed
cost/latency dashboards.

---

## Resume bullets (pick 2–3)

- Built an autonomous SWE agent (**LangGraph**) that plans, writes a RED regression test,
  patches, and self-corrects against sandboxed pytest output (bounded to 3 retries with
  trimmed-traceback context management).
- Designed multi-agent **fan-out/fan-in**: 3 fix strategies in isolated **git worktrees**,
  arbitrated by calibrated on-device scores; solved concurrent-state and Send-dedup
  failure modes in LangGraph.
- Integrated **LAYA** typed decision questions for patch quality, relevance and danger;
  composite scoring drives approval/low-quality thresholds across candidates.
- Added **guardrails** (secret/`eval`/prompt-injection scanning, NeMo rails config) and a
  human approval gate with a JSONL audit trail.
- Wrote the **eval suite** (3/3 resolved) and a **SWE-bench Lite** harness with negative
  controls; shipped a 4-tab Streamlit ops dashboard.

---

## 30-second demo script (if they say "show me")

1. `python src/main.py` → point at plan → RED test → diff → `PASSED` → LAYA 0.86 approved.
2. `python src/main.py --multi` → `candidates: 3` and the winning strategy.
3. `streamlit run src/dashboard/app.py` → Run tab, Diff tab with guardrail scan,
   Telemetry bars, Approvals export.
4. Optional mic-drop: `python laya_pipeline.py` → show the `eval()` candidate flagged.
