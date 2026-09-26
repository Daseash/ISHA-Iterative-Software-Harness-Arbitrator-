# 🤖 ISHA — Autonomous AI Software Engineering Agent

> An open-source autonomous SWE agent that ingests bug reports, plans a fix,
> writes code patches, self-corrects against failing tests, and commits a
> verified fix — with multi-agent parallel attempts, LAYA-powered judgment,
> and full observability.

**[▶ Live Demo](#)** &nbsp;|&nbsp; **[SWE-bench Results](#results)** &nbsp;|&nbsp; **[Architecture](#architecture)**

---

## The Problem

Most "AI coding agent" demos show a single happy-path fix on a toy repo.
ISHA instead builds out the parts that make autonomous fixes **trustworthy**:
a regression test proving the bug is real *before* patching, a LAYA decision
engine providing calibrated judgment (not text heuristics), multiple independent
agent attempts run in parallel and arbitrated, and a human approval gate before
anything commits unsupervised.

## Architecture

```
Bug Report → Planner (Gemini) → Regression Test (RED)
  → Multi-Agent Dispatch (3 worktrees, 3 strategies)
    → [Coder (Groq) → Sandbox → Self-Correct → Critic (LAYA)] ×3
  → Arbitration (LAYA picks best) → Approval Gate → Git Commit
  → Langfuse Telemetry → SWE-bench Scoring
```

Full diagram: [`docs/flow-diagram.txt`](docs/flow-diagram.txt)

## Tech Stack

`langgraph` · `litellm` · Gemini 2.5 Flash · Groq Llama 3.3 70B ·
**LAYA Decision Engine** · Qdrant · `tree-sitter` · Docker ·
`nemoguardrails` · `langfuse` · `pydantic` v2 · `pytest` · Streamlit

## Quickstart

```bash
git clone <your-repo-url>
cd isha-agent
pip install -r requirements.txt
cp .env.example .env        # add your free Gemini/Groq/Langfuse keys
python src/main.py
```

## LAYA Integration

Every judgment point uses the [LAYA decision engine](https://github.com/NandhaKishorM/laya)
for calibrated, on-device probability scoring:

- **Patch scoring**: `fix_quality` (score) + `matches_issue` (noul) + `safe_to_apply` (noul)
- **Arbitration**: Composite score ranking (0.5×quality + 0.25×match + 0.25×safety)
- **Danger detection**: `secrets_or_danger` + `logic_drift` checks
- **Final verification**: P(correct) ≥ 60% before success claim

## Current Phase

**Phase 1 — Skeleton** ✅ Complete. Pipeline nodes to be implemented in subsequent phases.

## License

MIT — see [`LICENSE`](LICENSE).
