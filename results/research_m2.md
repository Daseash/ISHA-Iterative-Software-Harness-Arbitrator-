# ISHA M-2 — Research-before-changing: patch-context hallucination & apply-failure repair

Date: 2026-10-05 (Day 4, improvement loop). Method: targeted browse over the
SWE-agent line (SWE-agent, Agentless, SWE-Lancer, recent arXiv agent
architectures 2025-2026), adapted per standing instructions — take the
practical mechanisms, no framework copy-paste.

Question under study: the M-2 #1 bucket is `patch_apply_failed` (now 5 ids:
5859/11742/12481/13031/22835), all with fallback-dominated coder calls and
`expected context not found in file` rejects. What do the best systems do
to (1) ground coder output in verbatim file context, (2) validate cheaply
before apply, (3) self-repair by feeding the exact reject diagnostic back,
(4) gate repair rounds on model confidence?

## Sources (URL + date + one takeaway)

1. **SWE-agent: Agent-Computer Interfaces Enable Automated Software
   Engineering** — arXiv:2405.15793 (v1 2024-05-06, v3 2024-11-11),
   https://arxiv.org/abs/2405.15793
   Takeaway: the design that worked is an LM-friendly ACI — a small set of
   line-exact edit commands in which the model must quote the exact
   existing lines it is replacing, plus "specific, concise feedback about a
   command's effects at every turn" and guardrails against common mistakes;
   ACI ablation gave a 64% relative lift over shell-only. Grounding =
   verbatim line context; repair = structured per-edit reject feedback,
   not free-form retry.

2. **Agentless: Demystifying LLM-based Software Engineering Agents** —
   arXiv:2407.01489 (v1 2024-07-01, v2 2024-10-29),
   https://arxiv.org/abs/2407.01489
   Takeaway: patches are generated as Search/Replace edits against a
   +/-10-line VERBATIM context window around the localized edit location —
   explicitly "less chances for hallucination" than generating full code —
   and every candidate is filtered by cheap static checks (syntax) and
   regression tests before selection (32% SWE-bench Lite at ~$0.70/issue;
   a simple pipeline beat the complex autonomous agents of its day).

3. **SWE-Lancer: Can Frontier LLMs Earn $1 Million from Real-World
   Freelance Software Engineering?** — arXiv:2502.12115 (2025-02-17, v4
   2025-05-29, OpenAI), https://arxiv.org/abs/2502.12115 and
   https://openai.com/index/swe-lancer (2025-07-28 update)
   Takeaway: verification must match real user behavior (E2E tests
   triple-verified by professional engineers), and the July 2025 dataset
   update shows infra variability (internet access during evaluation) was
   "a primary source of variability in model performance" — compare patch
   quality only in a stable, controlled environment.

4. **Exploring the Potential of Conversational Test Suite Based Program
   Repair on SWE-bench** — arXiv:2410.04485 (2024-10),
   https://arxiv.org/abs/2410.04485
   Takeaway: feeding concrete failure information back into the repair
   conversation at the same LLM budget lifts valid-patch rate from 46% to
   62% — reject-diagnostic feedback measurably works; the authors also warn
   failure output "significantly increases the LLM request size," so the
   diagnostic must be filtered/truncated before re-prompting.

5. **Heterogeneous Prompting and Execution Feedback for SWE Issue Test
   Generation and Selection (e-Otter++)** — arXiv:2508.06365
   (2025-08-08, v3 2026-01-22, ICSE 2026), https://arxiv.org/abs/2508.06365
   Takeaway: a repair loop is only as good as its stop condition — they
   gate each iteration with an LLM critic that checks the failure is
   "failing for the right reason" (matches the issue), stop when the critic
   is satisfied or after a hard cap (10 iterations), and the repair prompt
   carries the test log plus extra context gathered from the critic's
   output.

6. **SWE-Dev: Building Software Engineering Agents with Training and
   Inference Scaling** — arXiv:2506.07636 (2025-06),
   https://arxiv.org/abs/2506.07636
   Takeaway: iteration scaling — more interaction rounds monotonically
   raise resolve rate (34.0% at 30 rounds -> 36.6% at 75 rounds,
   SWE-Dev-32B): "additional iterations allow the models to refine their
   reasoning and correct prior errors." One-shot repair is under-budgeted,
   but every round costs, so budget repair rounds explicitly.

7. **CI-Repair-Bench: A Repository-Aware Benchmark for Automated Patch
   Validation via CI Workflows** — arXiv:2604.27148 (2026-04-29, v2
   2026-05-04), https://arxiv.org/abs/2604.27148
   Takeaway: log-driven repair needs (a) log FILTERING that "reduces noise
   while preserving critical diagnostic information" before feeding
   diagnostics to the model, and (b) patch construction applied via
   three-way merge "to ensure conflict-free integration" — validate the
   patch against the live repo state, not a stale snapshot.

8. **SWE-CI: Evaluating Agent Capabilities in Maintaining Software** —
   arXiv:2603.03823 (2026-03), https://arxiv.org/abs/2603.03823
   Takeaway: Architect-Programmer dual-agent role split iterating in a
   generate -> modify -> test CI loop until all tests pass. LOW relevance
   for M-2: its loop is test-centric, not apply-centric; recorded for
   completeness, not adapted.

## What to adapt vs skip (honest read)

Worth adapting (each target mechanism has at least one working reference):
verbatim context windows (Agentless), cheap pre-apply filtering
(Agentless), per-hunk reject feedback (SWE-agent ACI, arXiv:2410.04485),
critic-gated capped repair loops (e-Otter++), explicit round budgets
(SWE-Dev 2), live-tree validation (CI-Repair-Bench).

Not worth copying, and why:
- **SWE-agent's full interactive ACI / shell tool loop** — ISHA is a fixed
  pipeline (planner -> coder -> critic -> gate -> apply); Agentless showed
  a simple pipeline beats agentic autonomy on SWE-bench-style benchmarks at
  a fraction of the cost. Take the line-exact edit contract + per-edit
  reject feedback, not the agent.
- **Agentless's 40-candidate sampling + majority voting** — cost
  structure (~$0.70/issue at GPT-4-class pricing) does not fit the
  free-tier TPM budget; ISHA's equivalent is 2-3 targeted repair rounds
  with the reject diagnostic, cheaper and aimed at the known failure mode
  (context drift) instead of broad search.
- **SWE-Lancer's triple-verified E2E browser tests** — verification is
  already the official swebench harness (the flask-4045 P2P break was
  caught precisely by it — see M-5). The fitting SWE-Lancer lesson is the
  infra-variability one: keep the environment stable before comparing
  patch quality (the Day-4 UTF-8 harness fix already did this).
- **SWE-Dev's offline-RL / SFT training** — out of scope for the
  improvement loop; only its iteration-scaling curve is useful, as the
  budgeting argument for giving repair 2 rounds instead of 1.

## Adaptation notes for ISHA

Mapping each adopted mechanism to the specific v2 / v2.1 change being
implemented today:

1. **Verbatim re-grounding in the coder prompt (v2, M-2 (b))** <- SWE-agent
   line-exact edits + Agentless +/-10-line verbatim window. For
   fallback-model answers and apply-repair retries, the coder prompt
   re-fetches and includes the exact target lines (line-numbered,
   byte-exact) as the ONLY context for the SEARCH/REPLACE blocks; the model
   must quote them verbatim instead of regenerating from memory. Targets the
   `expected context not found in file` reject class directly (all 5 apply
   ids).
2. **`validate_hunk_context` pre-apply check (v2, M-2 (a))** <- Agentless
   cheap pre-filter + CI-Repair-Bench live-tree merge validation. Before
   accepting a patch, run `git apply --check` against the real checkout; on
   failure the patch is rejected with the failing hunk + the ACTUAL current
   lines at that location — which is exactly the input for the re-grounded
   repair round. Millisecond-scale static check; catches context drift
   before a patch burns a whole attempt.
3. **Reject-diagnostic feedback (v2, repair loop)** <- arXiv:2410.04485
   (62% vs 46% with failure feedback) + SWE-agent specific-concise per-edit
   feedback + CI-Repair-Bench log filtering. The repair round receives the
   verbatim `git apply --check` reject message (file, hunk header, missing
   context line) plus the current on-disk lines at that location, truncated
   to the failing hunk +/- context (no full-stack noise). Capped at 2
   repair rounds per attempt — e-Otter++'s hard-iteration-cap pattern.
4. **Fallback `safe_to_apply` floor (v2, M-2 (c))** <- e-Otter++
   critic-gated stop condition, inverted. LAYA already has calibrated
   scores (temperature-scaled, auto-approve threshold fitted on real
   outcomes); the change is to apply a STRICTER safe_to_apply threshold to
   answers from fallback models than to qwen-primary answers. Evidence: all
   5 M-2 apply ids have fallback-dominated coder calls, zero on
   healthy-primary. This is the confidence-gating of repair rounds:
   low-confidence + weak-provenance answers fail the gate and trigger
   re-grounded regeneration instead of apply.
5. **Per-call event streaming + attempt early-abort (v2.1)** <- SWE-agent
   "concise feedback at every turn" + SWE-Dev iteration scaling. Stream
   model-try / fail / backoff events to log.jsonl as they happen (fixes the
   `model_log: []` forensics blind spot where in-flight entries are
   discarded on FutureTimeout), and early-abort an attempt when no model has
   answered and >~50% of the 1800 s attempt budget is spent — instead of
   burning the whole budget on backoff-dominated chain calls (the 10451/
   11445 signature, reproduced 3x).

## Net

The literature consensus matches the Day-4 diagnosis: the apply-failure
bucket is a context-grounding + feedback problem, not an apply-mechanism
problem (the hunk-locator infra fix already cleared the 4 uncontaminated
ids). All five v2/v2.1 changes correspond to a mechanism at least one
source shows working; the skipped items are cost/infra mismatches, not
doubts about the adapted ones.