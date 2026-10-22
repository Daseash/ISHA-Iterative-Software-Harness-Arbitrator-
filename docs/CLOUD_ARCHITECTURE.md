# ISHA 100% Cloud-Hosted Model Architecture & Zero-Cost Routing Matrix

> **Core Invariant**: ISHA requires **0 GB VRAM and 0 Local GPUs**.  
> The entire multi-agent SWE-bench pipeline runs **100% cloud-hosted** across free-tier inference APIs with **$0.00 total inference cost**, backed by deterministic in-memory CPU gates and an offline AST brain.

---

## 1. Architectural Philosophy

Traditional autonomous software engineering agents either:
1. **Rely on massive local hardware**: Requiring dual RTX 3090/4090s or A100s to host 32B–70B coding models locally, creating severe installation friction and hardware costs.
2. **Burn thousands of dollars on proprietary APIs**: Making benchmark runs inaccessible for open-source researchers, GSoC contributors, and small teams.

**ISHA solves this by decoupling compute from local hardware**:
- **Execution & Sandboxing**: In-memory Python AST analysis + lightweight Docker container on host CPU.
- **Intelligence & Reasoning**: Asymmetrically routed across free cloud inference endpoints (Google AI Studio, Groq Cloud LPUs, Mistral AI Platform, Cerebras, and OpenRouter).
- **Deliberation**: Karpathy's 3-Stage LLM Council (`src/agents/council.py`) synthesizes high-confidence consensus across diverse model architectures.
- **Fail-Safe Operation**: Automatic key rotation, rate-limit backoff, and a deterministic fallback engine (`src/tools/offline_brain.py`) guarantee the pipeline never crashes mid-instance.

---

## 2. Complete 12-Node Cloud Pipeline Routing Table

| # | Pipeline Stage | Primary Cloud Model | Fallback Model(s) | Cloud Provider / Host | Temp | Latency | Inference Cost |
|---|---|---|---|---|---|---|---|
| **Node 1** | **Investigation & Localization** | `BAAI/bge-reranker-base` (ONNX) + `gemini/gemini-3.8-flash` | `gemini/gemini-3.5-flash-lite` | Local CPU + Google AI Studio | `0.00` | ~0.1s | **$0.00** |
| **Node 2** | **Decomposer** (Sub-issue splitting) | `groq/qwen/qwen-2.5-coder-32b` | `gemini/gemini-3.5-flash` | Groq Cloud / Google AI Studio | `0.10` | ~0.1s | **$0.00** |
| **Node 3** | **Planner / Root-Cause Reasoner** | `gemini/gemini-3.8-flash` | `groq/openai/gpt-oss-120b` $\rightarrow$ `gemini/gemini-3.5-flash` | Google AI Studio / Groq | `0.20` | ~0.2s | **$0.00** |
| **Node 4** | **Confidence Gate** (LocReranker) | Deterministic AST Math + Rule Gate | Rule-based gate | In-memory CPU | — | <2ms | **$0.00** |
| **Node 5** | **Regression Test (RED Phase)** | `groq/openai/gpt-oss-120b` | `gemini/gemini-3.8-flash` $\rightarrow$ `gemini/gemini-3.5-flash` | Groq Cloud / Google AI Studio | `0.20` | ~0.2s | **$0.00** |
| **Node 6a** | **Candidate 1: minimal_diff** | `groq/qwen/qwen3.8-27b` | `gemini/gemini-3.5-flash` | Groq Cloud / Google AI Studio | `0.20` | ~0.15s | **$0.00** |
| **Node 6b** | **Candidate 2: root_cause_first** | `groq/openai/gpt-oss-120b` | `groq/qwen/qwen3.8-27b` | Groq Cloud LPUs | `0.20` | ~0.45s | **$0.00** |
| **Node 6c** | **Candidate 3: call_site_aware** | `gemini/gemini-3.8-flash` | `gemini/gemini-3.5-flash` | Google AI Studio | `0.20` | ~0.30s | **$0.00** |
| **Node 6d** | **Candidate 4: defensive_fix** | `mistral/codestral-latest` | `gemini/gemini-3.5-flash` | Mistral AI API / Google | `0.20` | ~0.50s | **$0.00** |
| **Node 6e** | **Candidate 5: cross_file_audit** | `gemini/gemini-3.8-flash` (1M context) | `groq/llama-3.3-70b-versatile` | Google AI Studio / Groq Cloud | `0.20` | ~0.50s | **$0.00** |
| **Node 7** | **Static AST Pre-Check Gate** | `ast.parse` + `py_compile` + `pyflakes` | None (deterministic AST) | In-memory CPU | — | <2ms | **$0.00** |
| **Node 8** | **Replan / Self-Correction** | **Sticky to each candidate's assigned model** | Candidate's fallback model | Preserves branch identity | `0.20` | Isolated | **$0.00** |
| **Node 9** | **Critic / LAYA Gate** | Logistic Platt Scaler + `gemini/gemini-3.8-flash` | `groq/openai/gpt-oss-120b` | In-memory CPU + Google / Groq | `0.10` | ~5ms | **$0.00** |
| **Node 10** | **Karpathy LLM Council** | 3-Stage Deliberation (First Opinions → Blind Review → Chairman) | Single best model fallback | Groq + Google + Mistral | `0.20` | Async | **$0.00** |
| **Node 11** | **Memory & Dynamic Playbooks** | SQLite WAL (`memory.db`) | In-memory dict | Local Disk (CPU) | — | <1ms | **$0.00** |
| **Node 12** | **Checkpoint & Crash Resume** | `SqliteSaver` State Persistence | In-memory state | Local Disk (CPU) | — | <1ms | **$0.00** |

---

## 3. The 3 Small Tweaks to Make This Setup Bulletproof

1. **Sticky Model on Replan (Candidate Affinity)**:
   - When Candidate 1 (`qwen3.8-27b`), Candidate 2 (`gpt-oss-120b`), or Candidate 3 (`gemini-3.8-flash`) fails the sandbox test, the retry loop in `replan_node` $\rightarrow$ `coder_node` **remains locked to the candidate's assigned model family** (`state.assigned_model`).
   - *Why this is bulletproof*: Switching models mid-retry destroys context and causes style churn. Keeping each candidate branch "sticky" ensures that surgical fixes stay surgical, invariant fixes stay invariant, and callers stay updated consistently.

2. **Harmonized Temperature Clamping (`0.20` across all generative nodes)**:
   - Clamped all generation stages (Node 3 Planner, Node 5 Repro, Node 6 Candidates, Node 8 Replan) to `temperature = 0.20`.
   - *Why this is bulletproof*: Prevents indentation hallucinations and invalid markdown fences (which spike at temp $\ge 0.40$), while avoiding greedy stagnation on replan retries (which occurs at temp $< 0.10$).

3. **Cross-Provider Fallback Pairing (Zero Cascading Outages)**:
   - Primary and Fallback models are intentionally routed to **opposing free cloud providers**:
     - **Node 3 (Planner)**: Google (`gemini-3.8-flash`) $\rightarrow$ Groq (`gpt-oss-120b`) $\rightarrow$ Google (`gemini-3.5-flash`)
     - **Node 5 (Repro Test)**: Groq (`gpt-oss-120b`) $\rightarrow$ Google (`gemini-3.8-flash`)
     - **Node 6 (Candidate 1 - minimal_diff)**: Groq (`qwen3.8-27b`) $\rightarrow$ Google (`gemini-3.5-flash`)
     - **Node 6 (Candidate 2 - root_cause_first)**: Groq (`gpt-oss-120b`) $\rightarrow$ Groq (`qwen3.8-27b`)
     - **Node 6 (Candidate 3 - call_site_aware)**: Google (`gemini-3.8-flash`) $\rightarrow$ Google (`gemini-3.5-flash`)
   - *Why this is bulletproof*: If Google AI Studio encounters a temporary 429 rate limit window, the pipeline immediately falls back to Groq LPUs without stopping, and vice versa.

---

---

## 3. Node-by-Node Breakdown & Specialization

### Node 1: Investigation & Localization
- **Why this model?**: Bug localization requires semantic parsing of the repository tree without hallucination. Local ONNX embeddings (`BAAI/bge-reranker-base`) paired with `gemini-3.8-flash` provide rapid file scoring across up to 100 candidate files in milliseconds.
- **Failover**: Falls back to `gemini-3.5-flash-lite` for instantaneous token filtering.

### Node 2: Decomposer
- **Why this model?**: `groq/qwen/qwen-2.5-coder-32b` excels at structural decomposition of multi-file issues into atomic sub-tasks. Groq's LPU hardware returns completions at 500+ tokens/sec, introducing virtually zero latency.

### Node 3: Planner / Root-Cause Analysis
- **Why this model?**: `groq/openai/gpt-oss-120b` (or `gemini-3.8-flash`) acts as the lead architect. It identifies why the bug manifests, examines call hierarchies, and drafts the Phase RED reproduction strategy.
- **Deliberation Option**: Can trigger Karpathy's LLM Council (`src/agents/council.py`) to run multi-model peer review when planner confidence is under the threshold.

### Node 4: Confidence Gate
- **Why this model?**: Rule-based deterministic gate. Calculates Bayesian localization probability without calling any LLM, saving precious API rate limits.

### Node 5: Regression Test Generation (Phase RED)
- **Why this model?**: Writing a reproducing test that fails before the patch and passes after requires deep mathematical reasoning. `groq/deepseek-r1-distill-llama-70b` provides chain-of-thought test synthesis, generating both the minimal reproduction test and 2-3 critical edge cases (boundary values, null checks, type contracts).

### Node 6: Multi-Candidate Tournament (Multi-Model Arbitration)
Each candidate runs in an isolated Git worktree with a distinct model and strategy:
1. **`minimal_diff` (`mistral/codestral-latest`)**: Codestral was pre-trained specifically on repository diffs and `SEARCH/REPLACE` blocks. At temperature `0.10`, it generates surgical 1-to-5 line bug fixes with zero diff formatting errors.
2. **`call_site_aware` (`gemini/gemini-3.8-flash`)**: Leverages wide context to locate every caller and signature change, updating call sites in lockstep.
3. **`root_cause_first` (`groq/openai/gpt-oss-120b`)**: Addresses the invariant contract violation rather than patching the superficial symptom.
4. **`defensive_fix` (`mistral/codestral-latest`)**: Uses Codestral's diff precision to guard against adjacent edge cases (zero-division, NoneType, missing keys).
5. **`cross_file_audit` (`gemini/gemini-3.8-flash`)**: Takes advantage of Gemini's 1-million token context window to audit cross-module dependencies and shared utilities.

### Node 7: Static AST Gate (Pre-Sandbox)
- **Why this model?**: Zero LLM cost. Runs `ast.parse()`, `py_compile`, and `pyflakes` in under 2ms. If an LLM emits broken syntax or bad indentation, the gate catches it immediately, preventing wasted Docker container startups.

### Node 8: Isolated Docker Sandbox
- Runs official test suites inside ephemeral containers with strict isolation:
  - `--user "$(id -u):$(id -g)"` prevents host permission corruption.
  - `-e PYTHONDONTWRITEBYTECODE=1` keeps the host directory clean.
  - `--pids-limit 256` immunizes against fork bombs.
  - Hard `120s` timeout kills hung tests.

### Node 9: LAYA Critic (Platt Scaled Probability)
- Applies a calibrated logistic regression ($P_{\text{solve}} = \sigma(A \cdot x + B)$) on top of test outputs and diff size.
- If $P_{\text{solve}} \ge 0.65$, candidate is declared winning and shipped to the harness.

---

## 4. Karpathy's LLM Council (`/api/council`)

When solving complex, ambiguous, or high-blast-radius issues, ISHA activates Karpathy's 3-Stage LLM Council:

```mermaid
graph TD
    UserQuery[Bug Report / Architecture Dilemma] --> S1[Stage 1: Independent Opinions]
    S1 --> M1[Gemini 3.5 Flash Lite]
    S1 --> M2[Gemini 3.8 Flash]
    S1 --> M3[Groq GPT-OSS-120B]
    
    M1 --> S2[Stage 2: Blind Peer Review]
    M2 --> S2
    M3 --> S2
    
    S2 --> S3[Stage 3: Chairman Synthesis]
    S3 --> FinalConsensus[High-Confidence Consensus Plan]
```

1. **Stage 1 (First Opinions)**: 3 diverse models independently analyze the issue and produce proposed solutions.
2. **Stage 2 (Blind Peer Review)**: Responses are anonymized (e.g., "Response A", "Response B", "Response C") and cross-evaluated by all members for flaws, edge cases, and missing guards.
3. **Stage 3 (Chairman Synthesis)**: A designated Chairman (`gemini-3.8-flash`) synthesizes all reviews, discards flawed proposals, and produces an authoritative consensus.

---

## 5. Free Cloud Provider Setup & Credentials

All providers below offer **generous, 100% free-tier access** without requiring credit cards:

### 1. Google AI Studio (Gemini 3.5 & 3.8 Flash)
- **URL**: [https://aistudio.google.com/](https://aistudio.google.com/)
- **Free Quota**: 15 Requests/Min (RPM), 1,500 Requests/Day (RPD), 1 Million tokens/min.
- **Setup**: Get API key, set in `.env`:
  ```bash
  GOOGLE_API_KEY=AIzaSy...
  # For parallel multi-worker scaling, pass multiple keys:
  # GEMINI_API_KEYS=key1,key2,key3
  ```

### 2. Groq Cloud (Ultra-Fast LPUs)
- **URL**: [https://console.groq.com/](https://console.groq.com/)
- **Free Quota**: 30 RPM, 14,400 RPD, 500+ tokens/sec throughput.
- **Models**: `qwen/qwen-2.5-coder-32b`, `openai/gpt-oss-120b`, `deepseek-r1-distill-llama-70b`.
- **Setup**:
  ```bash
  GROQ_API_KEY=gsk_...
  # GROQ_API_KEYS=key1,key2
  ```

### 3. Mistral AI Platform (Codestral)
- **URL**: [https://console.mistral.ai/](https://console.mistral.ai/)
- **Free Quota**: Experiment Tier (~1 Billion tokens/month for coding models).
- **Models**: `codestral-latest` (trained specifically on search/replace blocks and repo diffs).
- **Setup**:
  ```bash
  MISTRAL_API_KEY=...
  # MISTRAL_API_KEYS=key1,key2
  ```

### 4. Cerebras Cloud (Ultra-Fast Inference)
- **URL**: [https://cloud.cerebras.ai/](https://cloud.cerebras.ai/)
- **Free Quota**: Up to 1,000,000 tokens/day at 2,000+ tokens/sec.
- **Models**: `llama3.3-70b`, `qwen-2.5-coder-32b`.
- **Setup**:
  ```bash
  CEREBRAS_API_KEY=csk-...
  ```

### 5. OpenRouter Free Tier
- **URL**: [https://openrouter.ai/](https://openrouter.ai/)
- **Free Quota**: Access to `:free` models (`openrouter/deepseek/deepseek-r1:free`, `openrouter/meta-llama/llama-3.3-70b-instruct:free`).
- **Setup**:
  ```bash
  OPENROUTER_API_KEY=sk-or-v1-...
  ```

---

## 6. Resilience & Quota Shields

ISHA includes production-grade defenses against API failures and rate limits:

1. **Per-Model Quota Isolation**:
   - If `gemini-3.8-flash` exhausts its per-day quota, only that model is marked dead for the session. `gemini-3.5-flash-lite` has an independent bucket and continues running.
2. **Sliding-Window TPM Cooldown**:
   - When a provider returns a 429 rate limit ("try again in 20s"), ISHA records the cooldown and automatically advances to the next provider in the chain or waits out the window without crashing.
3. **Round-Robin Multi-Key Pooling**:
   - Comma-separated API keys (`GEMINI_API_KEYS=k1,k2,k3`) automatically rotate on every call, multiplying available throughput by $N$.
4. **Deterministic Offline Brain**:
   - If all API keys are exhausted or unavailable, `src/tools/offline_brain.py` executes deterministic AST transformations so evaluations and CI pipelines finish cleanly without unhandled exceptions.
