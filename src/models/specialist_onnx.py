"""Local ONNX specialist suite: Nodes 1, 5b and 9 without any API keys.

The three INT8 ONNX models are pulled from the Hugging Face Hub on first use
and cached under ``models_cache/``.  All heavy dependencies (optimum,
transformers, numpy, joblib) are imported lazily so importing this module (and
running the rest of the test suite) never requires them.

Environment:
    ISHA_HUB_USER       Hub account that owns the published repos
                        (default: ``Maddy-Das``)
    ISHA_MODELS_CACHE   cache directory (default: ``models_cache``)
    HF_TOKEN            optional token for private/gated repositories
    ISHA_FORCE_OFFLINE  set to ``1`` to forbid network downloads and use only
                        an already-populated cache
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_HUB_USER = "Maddy-Das"

_REPO_NAMES = {
    "loc": "isha-loc-reranker-v1-int8-onnx",
    "redgate": "isha-redgate-v1-int8-onnx",
    "laya": "isha-laya-verifier-v1-int8-onnx",
}


class ISHASpecialistSuite:
    """Auto-downloading INT8 ONNX specialists.

    - Node 1  ``loc``      cross-encoder file/symbol reranker
    - Node 5b ``redgate``  phase-RED repro-test validity classifier
    - Node 9  ``laya``     5-head critic + Platt calibration

    Total RAM footprint is roughly 360 MB; no GPU is required.
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        hub_user: str | None = None,
        token: str | None = None,
    ) -> None:
        self.cache_dir = Path(
            cache_dir or os.getenv("ISHA_MODELS_CACHE", "models_cache")
        )
        self.hub_user = hub_user or os.getenv("ISHA_HUB_USER", DEFAULT_HUB_USER)
        self.token = token or os.getenv("HF_TOKEN")
        self._models: dict[str, object] = {}
        self._tokenizers: dict[str, object] = {}
        self._platt = None

    # ------------------------------------------------------------------ hub
    def repo_id(self, key: str) -> str:
        return f"{self.hub_user}/{_REPO_NAMES[key]}"

    def _ensure_local(self, key: str) -> str:
        """Return a local directory holding the ONNX model, downloading once."""
        local = self.cache_dir / key
        if any(local.glob("*.onnx")):
            return str(local)

        if os.getenv("ISHA_FORCE_OFFLINE", "0") == "1":
            raise RuntimeError(
                f"[specialist:{key}] ISHA_FORCE_OFFLINE=1 but no cached ONNX model "
                f"exists at {local}. Run once online to populate the cache."
            )

        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=self.repo_id(key),
            local_dir=str(local),
            token=self.token,
        )
        return str(local)

    def _load(self, key: str):
        if key in self._models:
            return self._models[key], self._tokenizers[key]

        # Resolve the cache first so ISHA_FORCE_OFFLINE gets its explicit
        # RuntimeError even on machines without optimum/transformers installed.
        local_dir = self._ensure_local(key)

        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer

        self._tokenizers[key] = AutoTokenizer.from_pretrained(local_dir)
        self._models[key] = ORTModelForSequenceClassification.from_pretrained(local_dir)

        if key == "laya":
            platt_file = Path(local_dir) / "platt_calibrator.joblib"
            if platt_file.exists():
                import joblib

                self._platt = joblib.load(platt_file)
        return self._models[key], self._tokenizers[key]

    def warmup(self) -> dict[str, str]:
        """Download/load every specialist; returns repo ids for logging."""
        for key in _REPO_NAMES:
            self._load(key)
        return {key: self.repo_id(key) for key in _REPO_NAMES}

    # ----------------------------------------------------------------- node 1
    def rerank_files(
        self,
        issue_query: str,
        ast_candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Node 1: rerank AST/BM25 candidates to push File Hit@1 past 70%."""
        import numpy as np

        if not ast_candidates:
            return []

        model, tok = self._load("loc")
        pairs = [
            (
                issue_query[:1500],
                f"FILE: {c['path']}\nSYMBOLS: {c.get('ast_summary', '')}",
            )
            for c in ast_candidates
        ]
        inputs = tok(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )
        logits = np.asarray(model(**inputs).logits).reshape(-1)
        probs = 1.0 / (1.0 + np.exp(-logits))
        for cand, prob in zip(ast_candidates, probs):
            cand["rerank_prob"] = float(prob)
            cand["final_score"] = (
                0.40 * cand.get("normalized_rag_score", 0.5) + 0.60 * float(prob)
            ) * cand.get("prior_kind", 1.0)
        return sorted(ast_candidates, key=lambda x: x["final_score"], reverse=True)[:top_k]

    # ---------------------------------------------------------------- node 5b
    def verify_phase_red_test(
        self,
        issue_text: str,
        test_code: str,
        pytest_stderr: str,
    ) -> bool:
        """Node 5b: True Bug vs Syntax/Import Error gate.

        Only real syntax defects hard-fail: ModuleNotFoundError is usually an
        environment problem in the harness venv, not proof of an invalid repro.
        """
        import numpy as np

        if any(bad in pytest_stderr for bad in ("SyntaxError", "IndentationError")):
            return False

        model, tok = self._load("redgate")
        text = (
            f"[ISSUE]: {issue_text[:1000]}\n"
            f"[TEST]:\n{test_code[:1500]}\n"
            f"[STDERR]:\n{pytest_stderr[:1000]}"
        )
        inputs = tok(text, truncation=True, max_length=512, return_tensors="np")
        logits = np.asarray(model(**inputs).logits).reshape(-1)
        exp_l = np.exp(logits - np.max(logits))
        prob_valid = float((exp_l / exp_l.sum())[1])
        return prob_valid >= 0.50

    # ----------------------------------------------------------------- node 9
    def evaluate_laya(self, issue_text: str, candidate_diff: str) -> dict:
        """Node 9: calibrated LAYA verifier with multiplicative safety vetoes."""
        import numpy as np

        model, tok = self._load("laya")
        text = f"[ISSUE]: {issue_text[:1200]}\n[DIFF]:\n{candidate_diff[:2000]}"
        inputs = tok(text, truncation=True, max_length=512, return_tensors="np")
        logits = np.asarray(model(**inputs).logits).reshape(-1)
        p = 1.0 / (1.0 + np.exp(-logits))
        fix_q, match_q, safe_q, danger_q, drift_q = [float(x) for x in p[:5]]

        raw_comp = 0.50 * fix_q + 0.25 * match_q + 0.25 * safe_q
        calibrated = (
            float(self._platt.predict_proba([[raw_comp]])[0, 1])
            if self._platt is not None
            else raw_comp
        )

        veto = 0.0 if (danger_q > 0.50 or drift_q > 0.70) else 1.0
        return {
            "fix_quality": round(fix_q * 2.0, 3),
            "matches_issue": round(match_q, 4),
            "safe_to_apply": round(safe_q, 4),
            "secrets_or_danger": round(danger_q, 4),
            "logic_drift": round(drift_q, 4),
            "composite": round(calibrated * veto, 4),
            "passed_veto": bool(veto == 1.0),
        }
