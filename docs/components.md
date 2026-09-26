# ISHA — Component Breakdown

| Component | Category | Role | Why Chosen |
|:---|:---|:---|:---|
| **`langgraph`** | Orchestration | Cyclic state graph, fan-out/fan-in, checkpoints | Supports the retry loops and parallel dispatch that simple chains can't |
| **`litellm`** | Model Gateway | Unified API across Gemini + Groq with auto-fallback | Swap providers with a one-line change |
| **Gemini 2.5 Flash** | Planning | 1M+ context for repo ingestion and fix planning | Free tier, huge context window |
| **Groq Llama 3.3 70B** | Patching + Critic | Fast code generation (~300-500 tok/s) | Speed keeps the retry loop responsive |
| **LAYA Decision Engine** | Judgment | Calibrated scoring, danger detection, arbitration | On-device probabilities replace text-based heuristics |
| **`docling`** | Ingestion | Structural parsing of code + docs | Preserves hierarchy, no naive chunking |
| **Qdrant** | Vector DB | Hybrid dense + BM25 search | Exact symbol name retrieval via keyword matching |
| **`tree-sitter`** | AST Analysis | Compact repo map + structural patch fallback | Token-efficient codebase understanding |
| **`nemoguardrails`** | Security | Input injection blocking + secret scanning | Enterprise safety boundaries |
| **`langfuse`** | Observability | End-to-end traces, token burn, latency tracking | Production visibility |
| **Streamlit** | Dashboard | Live ops UI with 4 tabs | Simple, free deployment |
| **`git worktree`** | Isolation | Independent directories per parallel agent | No race conditions between agents |
| **SWE-bench** | Benchmark | Standardized evaluation against real GitHub issues | Comparable, credible results |
| **`pydantic` v2** | Validation | Strict state schemas across all nodes | Type-safe data flow |
| **`pytest`** | Testing | Ground truth for fix verification | Industry standard |
