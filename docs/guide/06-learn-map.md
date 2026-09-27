# 06 · Learn Map — key topics → where they live → how to prove you learned them

> Use this as a study checklist. For each topic: **read the file**, **run the demo**,
> **answer the check question out loud**. If you can't answer the check question, you
> haven't learned it yet.

Legend: ⬜ not started · 🟨 reading · ✅ can explain it cold

## A. The agent itself

| ⬜ | Topic | Read this | Run this | Check question |
|---|---|---|---|---|
| ⬜ | What makes something an agent | `docs/guide/02-ai-agent-explained.md` | — | Name the 4 ingredients and where each lives in ISHA |
| ⬜ | State & reducers | `src/agents/state.py` | — | Why does every field need `Annotated[..., _last]`? What breaks without it? |
| ⬜ | The state machine | `src/agents/graph.py` | `python src/main.py` | Draw both graphs from memory; where is the retry edge? |
| ⬜ | Node roles | `src/agents/nodes.py` | `python src/main.py --repo <path>` | What does each of planner/regression/coder/sandbox read and write? |
| ⬜ | Bounded retry + context trimming | `nodes.py`, `src/tools/context_trimmer.py` | `pytest tests/test_context_trimmer.py` | Why trim, and why cap at 3? |
| ⬜ | Multi-agent fan-out | `dispatch.py`, `attempt.py` | `python src/main.py --multi` | Why are nodes named `attempt1..3` instead of one shared node? |
| ⬜ | Arbitration ledger | `src/review/arbitration.py` | same run → `candidates: 3` | How do 3 parallel branches agree on one winner without racing? |
| ⬜ | Human-in-the-loop | `src/approval/gate.py` | `python src/main.py --repo <path> --approve cli` | Difference between `auto`, `cli`, `interrupt` modes? |

## B. LLM integration

| ⬜ | Topic | Read this | Run this | Check question |
|---|---|---|---|---|
| ⬜ | Model routing & fallbacks | `src/config.py` | `python src/main.py` | Draw the fallback chain. What happens if Gemini 503s? |
| ⬜ | Offline degradation | `src/tools/offline_brain.py` | `ISHA_FORCE_OFFLINE=1 python src/main.py` | How does the brain know which function to edit? |
| ⬜ | Prompt section parsing | `offline_brain.py:_sections` | — | Why `SECTION_RE` uses `[ \t]*` and not `\s*` after the colon? |
| ⬜ | litellm specifics | `config.py:90-120` | — | Correct shape of `fallbacks=` and why a bare list silently fails |
| ⬜ | Live vs offline detection | `config.py:32-36` | — | What makes `OFFLINE_MODE` true? |

## C. Code understanding & retrieval

| ⬜ | Topic | Read this | Run this | Check question |
|---|---|---|---|---|
| ⬜ | Repo parsing/chunking | `src/ingestion/parser.py` | `python src/main.py --repo <path>` | What gets skipped when walking the tree? |
| ⬜ | AST map (tree-sitter) | `src/tools/ast_mapper.py` | `python src/main.py --repo <path>` | Why a compact map instead of full file contents in the prompt? |
| ⬜ | Embeddings (hashing) | `src/rag/indexer.py:22` | `python src/main.py --repo <path>` | How does a bag-of-tokens hash produce a 384-d vector? |
| ⬜ | Vector DB + fallback | `indexer.py:54`, `retriever.py:24` | small script → watch `mode: local` | What are the two degradation points in retrieval? |
| ⬜ | Context assembly | `src/agents/context.py` | `python src/main.py` | What's the 4000-char budget spent on? |

## D. Verification & judgment

| ⬜ | Topic | Read this | Run this | Check question |
|---|---|---|---|---|
| ⬜ | Patch application | `src/tools/patch_engine.py` | `python src/main.py --repo <path>` | Two strategies used, and when does it fall back? |
| ⬜ | Sandbox isolation | `src/tools/sandbox.py` | `python src/main.py --repo <path>` | Where does the patch actually get written? |
| ⬜ | Worktrees | `src/tools/worktree_manager.py` | `python src/main.py --repo <path> --multi` | What happens for a repo with no `.git`? |
| ⬜ | LAYA typed questions | `src/review/laya_judge.py` | `python laya_pipeline.py` | Why typed `score`/`noul` instead of free text? |
| ⬜ | Composite scoring | `laya_judge.py:89` | `python laya_pipeline.py` | Write the formula; what does `<0.4` mean? |
| ⬜ | Input compaction for LAYA | `laya_judge.py:_compact_diff` | — | Why did golden & corrupted patches score identically before? |
| ⬜ | Critic & verdicts | `src/review/critic.py` | `python laya_pipeline.py` | Three verdict values and what triggers each? |
| ⬜ | Guardrail scanner | `src/guardrails/scanner.py` | `python src/main.py --repo <path> --approve cli` | Why are only `+` lines scanned for secrets? |
| ⬜ | Approval audit | `src/approval/gate.py` | same → `approvals.jsonl` | What's written for a clean vs flagged patch? |

## E. Evaluation & product

| ⬜ | Topic | Read this | Run this | Check question |
|---|---|---|---|---|
| ⬜ | Eval methodology | `tests/eval_suite.py` | — read-only (calculator fixture retired) | Why apply the patch to a *pristine copy* to score it? |
| ⬜ | Resolution definition | `eval_suite.py:verify_patch` | — read-only | What exactly counts as "resolved"? |
| ⬜ | SWE-bench harness | `tests/swebench_runner.py` | `python tests/swebench_runner.py --limit 3` | What does `--mode judge` measure vs `--mode full`? |
| ⬜ | Negative controls | `swebench_runner.py` (corrupt/unrelated/dangerous) | `python tests/swebench_runner.py --limit 3` | Why are 4 controls better than 1? |
| ⬜ | Dashboard | `src/dashboard/app.py` | `streamlit run src/dashboard/app.py` | How does approval resume work end-to-end? |
| ⬜ | Results reporting | `README.md` § Results | — | Can you defend every number in that table, including its caveats? |

## F. Things to be able to write on a whiteboard

1. **Both graphs**, nodes and edges, single and multi.
2. **The retry condition** and what feeds it.
3. **The composite score formula** and the three thresholds.
4. **The fallback chain** for planner and coder (live → alternate model → offline brain).
5. **The guardrail stack** in order: injection scan → patch apply → sandbox tests →
   regex secret scan → LAYA danger → approval gate.
6. **Eval data flow**: issue → graph → patch → pristine copy → pytest → selector check → JSON.

## G. Suggested order if you only have 90 minutes

1. `01-what-is-isha.md` + `03-architecture-dataflow.md` (15 min)
2. Run `python src/main.py` and `--multi`, read `graph.py` while it runs (20 min)
3. `05-interview-pitch.md`, say the 60-second pitch out loud twice (10 min)
4. Read `laya_judge.py` + run `laya_pipeline.py` (15 min)
5. Read `dispatch.py`, `attempt.py`, `arbitration.py` (15 min)
6. Skim `config.py` + `offline_brain.py` so you can answer "what if the API is down?" (10 min)
7. Re-answer every **Check question** in section A and D from memory (5 min)
