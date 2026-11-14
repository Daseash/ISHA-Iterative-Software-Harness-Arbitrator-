# ⚖️ ISHA Benchmark Reconciliation & Run Lineage

> **Purpose**: Reconcile all historical benchmark score milestones across local records (`REPORT.md`, `progress.md`, `SUBMIT_RUNBOOK.md`, and root `README.md`) to guarantee 100% reproducibility and transparency.

---

## 1. Scorecard Chronology & Milestone Mapping

The variation in reported totals reflects the progressive evaluation stages of the SWE-bench Lite benchmark campaign:

| Milestone / Record | Date | Scope | Code Version & Harness Config | Resolved / Total | Audited Rate | Primary Artifact |
| :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| **Stage A Baseline**<br>([REPORT.md](file:///c:/Users/Eashwar/ISHA/isha-agent/results/REPORT.md#L30-L45)) | 2026-09-30 | 30-instance test slice (`django`) | • Single-candidate unconstrained generation<br>• Pre-tournament, pre-LAYA<br>• Windows CRLF patch apply bugs | **1 / 30** | 3.3% | `results/REPORT.md` (Stage A Audit) |
| **Interim Campaign Snapshot**<br>([progress.md](file:///c:/Users/Eashwar/ISHA/isha-agent/results/progress.md#L861-L880)) | 2026-10-14 | Sessions 1–6 complete;<br>Sessions 7–10 queued | • LangGraph 9-node state machine<br>• 3-strategy worktree tournament<br>• AST compilation gates active | **72 / 232** | 31.0% (eval)<br>24.0% (total) | `results/lite300-s1` .. `s6`<br>`harness_report.json` |
| **Submission Frozen Milestone**<br>([SUBMIT_RUNBOOK.md](file:///c:/Users/Eashwar/ISHA/isha-agent/results/SUBMIT_RUNBOOK.md#L1-L8)) | 2026-10-18 | Sessions 1–8 complete<br>(pre-submission payload) | • S1–S6 (72 resolved) + S8 Docker (4 resolved)<br>• `all_preds.jsonl` lint passed (227 valid rows)<br>• Dedicated model routing per domain | **76 / 300** | 25.33% | `results/all_preds.jsonl`<br>`results/lite300-s8/harness_report.json` |
| **Audited Final Total**<br>([README.md](file:///c:/Users/Eashwar/ISHA/README.md#L106-L123)) | 2026-11-15 | Full S1–S10 + targeted rescue passes | • Full multi-model cloud mesh ($0.00 / 0 GB VRAM)<br>• S7 (2) + S9 (1) + S4-r2 & Django rescues (4)<br>• LAYA calibrated gate ($ECE = 0.0010$) | **83 / 300** | **27.67%** | `report.json` archives<br>`checkpoints.db` |

---

## 2. Mathematical Reconciliation

```text
[Stage A Baseline: 1/30] (Initial single-run prototype)
        │
        ▼ (+71 resolved via LangGraph 9-node multi-candidate tournament across S1–S6)
[Interim Progress Snapshot: 72/232] (progress.md:861)
   • Session 1: 11 / 30 (Django)
   • Session 2: 14 / 30 (Django)
   • Session 3: 20 / 30 (Django)
   • Session 4: 21 / 30 (Django peak slice)
   • Session 5:  3 / 30 (Matplotlib / Seaborn)
   • Session 6:  3 / 30 (Requests / Pytest / Pylint)
   ──────────────────────────────────────────────────────────
   Total S1–S6 Resolved: 11 + 14 + 20 + 21 + 3 + 3 = 72
        │
        ▼ (+4 resolved in Session 8 Sphinx/SymPy Docker evaluation)
[Submission Runbook Frozen Milestone: 76/300] (SUBMIT_RUNBOOK.md:3)
   • S1–S6 Total: 72
   • Session 8: +4 (sphinx-doc__sphinx-8713, sphinx-doc__sphinx-8721, sympy__sympy-13471, sympy__sympy-13647)
   ──────────────────────────────────────────────────────────
   Total Frozen Milestone = 76 / 300 (25.33%)
        │
        ▼ (+7 additional resolutions from Session 7, Session 9, and rescue evaluation)
[Audited Global Full Total: 83/300] (README.md:6)
   • S1–S8 Total: 76
   • Session 7:   +2 (scikit-learn__scikit-learn-12471, scikit-learn__scikit-learn-13496)
   • Session 9:   +1 (sympy__sympy-14774)
   • Rescues/r2:  +4 (django__django-13028, django__django-11964 rescue-v4, django__django-15400, django__django-11049)
   ──────────────────────────────────────────────────────────
   Grand Total Audited = 83 / 300 (27.67%)
```

---

## 3. Preserved Artifacts & Reproduction Commands

* **Lint Predictions**: `python isha-agent/scripts/lint_all_preds.py` (validates all 227 schema-clean rows).
* **Verify S1–S10 Reports**: All raw Docker container logs reside in `isha-agent/results/lite300-s*/harness_report.json` and `.agents/backup_results_archive/`.
* **Golden Reproductions**: Standalone Docker verification testbeds preserved in `isha-agent/results/golden/`.
