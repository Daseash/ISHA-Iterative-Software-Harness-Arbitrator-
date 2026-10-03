# 🔬 ISHA Benchmark Reproduction Guide

This guide details how to reproduce all empirical benchmark numbers and figures for **ISHA (Iterative Software Harness & Arbitrator)**.

Every figure and metric reported in `README.md`, `results/REPORT.md`, and `docs/RELEASE_CRITERIA.md` can be deterministically audited and regenerated using the commands below.

---

## 1. System Requirements & Setup

1. **Python Environment**: Python 3.10+ (tested on Python 3.13)
2. **Container Engine**: Docker Desktop with WSL2 backend (Linux engine)
3. **API Keys**: Groq and Google Gemini API keys configured in `.env`:
   ```bash
   GROQ_API_KEY=gsk_...
   GOOGLE_API_KEY=AQ....
   ```
4. **Environment Health Check**:
   ```bash
   python -m src.cli doctor
   ```
   Ensures that Python, Git, Docker, Qdrant fallback, and provider model chains are reachable.

---

## 2. Running Unit & Integration Tests

Verify that all 81 core agent tests pass without regressions:
```bash
python -m pytest --ignore=tests/dummy_repo
```
Expected output: `81 passed, 2 warnings in ~18s`.

---

## 3. Benchmark Dataset Splits

Fixed dataset splits are stored in [`data/splits.json`](data/splits.json) (seed 42):
- **DEV Slice** ($N=30$): Used for parameter tuning, localization calibration, and before/after component ablation.
- **FINAL Slice** ($N=30$): Held-out evaluation slice. Never used during development.
- **TRAIN Slice** ($N=240$): Label repository for LAYA calibration.

---

## 4. Reproducing Empirical Results

### A. Localization Recall Evaluation
To evaluate hierarchical BM25 + defs + prior re-ranking on the 30 DEV instances:
```bash
python -m src.bench.loc_eval --slice dev --limit 30
```
Metrics written to [`results/loc_eval_dev.json`](results/loc_eval_dev.json):
- Hit@1: 46.7%
- Hit@3: 60.0%
- Hit@5: 63.3%
- Hit@8: 66.7%
- MRR: 0.535

### B. Multi-Model Candidate Tournament Compilation
To aggregate candidate outcomes across the 3 distinct model families:
```bash
python -m src.bench.build_candidates_json
```
Metrics written to [`results/candidates.json`](results/candidates.json).

### C. LAYA Calibration & Combiner Evaluation
To fit the logistic combiner with temperature scaling on held-out validation labels:
```bash
python -m src.review.calibration
```
Metrics written to [`results/calibration.json`](results/calibration.json):
- ECE: 0.0010 ($N_{val}=103$)
- Brier Score: 0.0000
- Auto-approve threshold $\tau=0.50$ (100.0% precision)

### D. Before/After Synthesis & Wilson Confidence Intervals
To compile baseline vs. upgraded metrics with exact 95% Wilson confidence intervals:
```bash
python -m src.bench.build_before_after
```
Metrics written to [`results/before_after.json`](results/before_after.json).

### E. Regenerating Comparison Visualizations
To re-render the publication comparison plot:
```bash
python -m src.bench.make_plots
```
Graphic generated at [`assets/isha_vs_baselines.png`](assets/isha_vs_baselines.png).
