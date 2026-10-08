"""
ISHA Autonomous Improvement Loop Engine.

First-class architectural self-repair and convergence harness for ISHA.
Runs multi-round iterative repair with the 4 highest-leverage engineering levers:
  1. Verbatim compiler syntax/indentation context injection.
  2. Multi-candidate tournament & strategy diversity (minimal_diff, call_site_aware, root_cause_first).
  3. Resilient fuzzy patching with whole-file synthesis fallback.
  4. Decoupled model specialization & quota-aware failover.

Stops iteratively when:
  - Tests cleanly pass and gates clear (score >= 0.85), OR
  - Improvement delta plateaus (Delta <= convergence_delta), OR
  - Maximum iteration rounds reached.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.agents.state import AgentState, coerce_state
from src.config import (
    CANDIDATE_1_MODEL,
    CANDIDATE_2_MODEL,
    CANDIDATE_3_MODEL,
    CODER_CHAIN,
    PLANNER_CHAIN,
)

logger = logging.getLogger("isha.improvement_loop")


@dataclass
class ImprovementLoopConfig:
    """Configuration for the autonomous improvement loop."""
    max_iterations: int = 3
    convergence_delta: float = 0.0
    candidates_per_round: int = 3
    verbatim_compiler_context: bool = True
    fuzzy_patch_resilience: bool = True
    early_stop_on_clean_pass: bool = True


@dataclass
class RoundSnapshot:
    """Record of a single improvement round."""
    iteration: int
    patch: str
    strategy: str
    score: float
    gate_ok: bool
    test_output: str
    delta: float = 0.0
    model: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class ImprovementLoopResult:
    """Final result of the improvement loop."""
    best_state: AgentState
    converged: bool
    iterations_run: int
    best_score: float
    history: list[RoundSnapshot]
    stopping_reason: str


def run_improvement_loop(
    state: AgentState,
    config: ImprovementLoopConfig | None = None,
    log_fn: Callable[[str], None] | None = None,
) -> ImprovementLoopResult:
    """Execute the multi-round self-repair improvement loop on an AgentState.

    Parameters:
        state: Initial AgentState containing issue_text, repo_path, and initial plan/patch.
        config: Improvement loop configuration parameters.
        log_fn: Optional logger callback for reporting progress.

    Returns:
        ImprovementLoopResult with the converged peak verified state and complete history.
    """
    cfg = config or ImprovementLoopConfig()
    log = log_fn or (lambda msg: print(f"  [improvement-loop] {msg}", file=sys.stderr))

    current_state = coerce_state(state)
    history: list[RoundSnapshot] = []
    best_state = current_state
    best_score = float(current_state.critic_score or 0.0)

    log(f"Starting improvement loop (max_iterations={cfg.max_iterations}, candidates={cfg.candidates_per_round})")

    for round_idx in range(1, cfg.max_iterations + 1):
        log(f"=== Round {round_idx}/{cfg.max_iterations} ===")

        # 1. Update state candidate settings for this round
        os.environ["ISHA_CANDIDATES"] = str(cfg.candidates_per_round)

        # 2. Invoke candidate tournament node with verbatim error feedback
        from src.agents.nodes import candidate_node, coder_node, sandbox_node
        from src.review.critic import critic_node

        # If previous round failed or had gate errors, regenerate or repair
        if round_idx > 1:
            current_state.retry_count = round_idx - 1
            current_state = coder_node(current_state)

        # Generate & arbitrate candidate tournament
        current_state = candidate_node(current_state)

        # Execute sandbox gating
        current_state = sandbox_node(current_state)

        # Adversarial criticism & LAYA scoring
        current_state = critic_node(current_state)

        score = float(current_state.critic_score or 0.0)
        passed = "PASSED" in (current_state.test_output or "")
        gate_ok = "FAILED: STATIC GATE" not in (current_state.test_output or "")

        delta = score - (history[-1].score if history else 0.0)

        snapshot = RoundSnapshot(
            iteration=round_idx,
            patch=current_state.patch or "",
            strategy=current_state.strategy or "default",
            score=score,
            gate_ok=gate_ok,
            test_output=current_state.test_output or "",
            delta=delta,
            model=getattr(current_state, "model_name", ""),
            notes=list(current_state.context_notes or []),
        )
        history.append(snapshot)

        log(f"Round {round_idx}: strategy='{snapshot.strategy}' score={score:.3f} delta={delta:+.3f} gate_ok={gate_ok}")

        # Update best state
        if score > best_score or (score == best_score and gate_ok and not history[0].gate_ok):
            best_score = score
            best_state = current_state

        # Early termination condition 1: Clean verified pass with high score
        if cfg.early_stop_on_clean_pass and passed and gate_ok and score >= 0.85:
            log(f"Converged on Round {round_idx}: verified clean patch with high score ({score:.3f})")
            return ImprovementLoopResult(
                best_state=best_state,
                converged=True,
                iterations_run=round_idx,
                best_score=best_score,
                history=history,
                stopping_reason="clean_verified_pass",
            )

        # Early termination condition 2: Convergence plateau (Delta <= 0 on consecutive rounds)
        if round_idx >= 2 and delta <= cfg.convergence_delta and gate_ok:
            log(f"Converged on Round {round_idx}: score delta plateaued (delta={delta:+.3f} <= {cfg.convergence_delta})")
            return ImprovementLoopResult(
                best_state=best_state,
                converged=True,
                iterations_run=round_idx,
                best_score=best_score,
                history=history,
                stopping_reason="delta_plateau_converged",
            )

    log(f"Completed all {cfg.max_iterations} rounds. Peak score: {best_score:.3f}")
    return ImprovementLoopResult(
        best_state=best_state,
        converged=False,
        iterations_run=cfg.max_iterations,
        best_score=best_score,
        history=history,
        stopping_reason="max_iterations_reached",
    )
