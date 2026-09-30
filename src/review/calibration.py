"""
ISHA LAYA Calibration — Phase 6 of the SWE-bench upgrade.

LAYA's `noul` values are probabilities but they are *not* calibrated on our
patch distribution: a model that says 0.8 does not mean 80% of those patches
are right.  This module turns "LAYA said so" into a number we can actually
act on, using only data we produce ourselves:

  * **temperature scaling** on the raw probability (fits T on labelled data,
    monotonic so it never reorders candidates),
  * **ECE / Brier** as the honesty metrics, reported before and after,
  * a **logistic combiner** over Laya scores *and* hard signals
    (apply gate, static gate, repro result, diff size, regressions),
  * a **decision threshold** chosen on the labelled data instead of guessed.

Nothing here runs a model: it is pure numeric fitting on
``data/laya_labels.jsonl`` (written by the label collector during a run).

No labels yet?  ``combine()`` falls back to a documented hand-weighted
score and says so in ``model["mode"]`` — an uncalibrated number is never
silently passed off as a calibrated one.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = ROOT / "data" / "laya_labels.jsonl"
MODEL_PATH = ROOT / "data" / "laya_combiner.json"

EPS = 1e-9

# Feature order is a contract: it must match the file written by fit().
FEATURES = [
    "laya_fix_quality",       # 0..2 raw score
    "laya_matches_issue",     # 0..1
    "laya_safe_to_apply",     # 0..1
    "gate_ok",                # 0/1 static gates + apply
    "repro_ok",               # 0/1 repro fails-before / passes-after
    "regression_count",       # integer, normalised downstream
    "diff_size",              # added+removed lines, normalised downstream
    "files_changed",          # integer, normalised downstream
]


# ── Label collection ───────────────────────────────────────────────────────
def append_label(payload: dict, path: Path | str = LABELS_PATH) -> None:
    """Append one (features, outcome) pair to the label store."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def load_labels(path: Path | str = LABELS_PATH) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def features_for(laya: dict, gate_ok: bool, repro: dict,
                 diff_size: int, files_changed: int) -> dict:
    """Turn a candidate's evidence into the fixed feature vector."""
    repro_flag = 0.0
    if (repro or {}).get("available"):
        repro_flag = 1.0 if (repro.get("before_ok") and repro.get("after_ok")) else 0.0
    return {
        "laya_fix_quality": float((laya or {}).get("fix_quality", 0) or 0) / 2.0,
        "laya_matches_issue": float((laya or {}).get("matches_issue", 0) or 0),
        "laya_safe_to_apply": float((laya or {}).get("safe_to_apply", 0) or 0),
        "gate_ok": 1.0 if gate_ok else 0.0,
        "repro_ok": repro_flag,
        "regression_count": float((repro or {}).get("regressions", 0) or 0),
        "diff_size": float(diff_size or 0),
        "files_changed": float(files_changed or 0),
    }


def vector(features: dict) -> list[float]:
    """Raw features -> scaled numeric vector (scaling constants are fitted)."""
    return [
        features["laya_fix_quality"],
        features["laya_matches_issue"],
        features["laya_safe_to_apply"],
        features["gate_ok"],
        features["repro_ok"],
        min(features["regression_count"], 5.0) / 5.0,
        min(features["diff_size"], 400.0) / 400.0,
        min(features["files_changed"], 10.0) / 10.0,
    ]


# ── Numeric helpers (numpy-free on purpose: no new runtime dependency) ─────
def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-min(z, 60.0))
        return (1.0 - ez) / (1.0 + ez)
    ez = math.exp(max(z, -60.0))
    return ez / (1.0 + ez)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def temperature_scale(probs: list[float], temperature: float) -> list[float]:
    t = max(temperature, 1e-3)
    return [sigmoid(math.log(max(p, EPS) / (1 - max(min(p, 1 - EPS), EPS))) / t)
            for p in probs]


def ece(probs: list[float], labels: list[int], bins: int = 10) -> float:
    """Expected calibration error over equal-width bins."""
    if not probs:
        return 0.0
    total = len(probs)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [
            i for i, p in enumerate(probs)
            if (p == hi if b == bins - 1 else lo <= p < hi)
        ]
        if not idx:
            continue
        conf = _mean([probs[i] for i in idx])
        acc = _mean([float(labels[i]) for i in idx])
        err += (len(idx) / total) * abs(conf - acc)
    return err


def brier(probs: list[float], labels: list[int]) -> float:
    if not probs:
        return 0.0
    return _mean([(p - float(y)) ** 2 for p, y in zip(probs, labels)])


# ── Logistic combiner ──────────────────────────────────────────────────────
def fit_logistic(x: list[list[float]], y: list[int], l2: float = 1e-2,
                 epochs: int = 400, lr: float = 0.5) -> dict:
    """Plain gradient-descent logistic regression with a bias term."""
    n, d = len(x), len(x[0]) if x else 0
    if n == 0 or d == 0:
        return {"weights": [0.0] * d, "bias": 0.0, "temperature": 1.0, "n": 0}

    w = [0.0] * d
    b = 0.0
    for _ in range(epochs):
        gw = [0.0] * d
        gb = 0.0
        for row, label in zip(x, y):
            p = sigmoid(sum(wi * xi for wi, xi in zip(w, row)) + b)
            e = p - label
            for j in range(d):
                gw[j] += e * row[j]
            gb += e
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * w[j])
        b -= lr * (gb / n)

    probs = [sigmoid(sum(wi * xi for wi, xi in zip(w, row)) + b) for row in x]
    t = _fit_temperature(probs, y)
    return {"weights": w, "bias": b, "temperature": t, "n": n,
            "brier_raw": round(brier(probs, y), 4),
            "ece_raw": round(ece(probs, y), 4)}


def _fit_temperature(probs: list[float], labels: list[int]) -> float:
    """1-parameter temperature scaling (grid search, keeps it robust)."""
    best_t, best_loss = 1.0, brier(probs, labels)
    for i in range(1, 41):
        t = 0.25 + i * 0.1
        scaled = temperature_scale(probs, t)
        loss = brier(scaled, labels)
        if loss < best_loss:
            best_t, best_loss = t, loss
    return round(best_t, 3)


def find_threshold(probs: list[float], labels: list[int]) -> dict:
    """Pick the threshold that maximises balanced accuracy on the labels."""
    if not probs:
        return {"threshold": 0.5, "balanced_accuracy": 0.0}
    candidates = sorted({round(p, 2) for p in probs} | {0.5})
    best = {"threshold": 0.5, "balanced_accuracy": -1.0}
    for t in candidates:
        tp = sum(1 for p, y in zip(probs, labels) if p >= t and y == 1)
        fn = sum(1 for p, y in zip(probs, labels) if p < t and y == 1)
        tn = sum(1 for p, y in zip(probs, labels) if p < t and y == 0)
        fp = sum(1 for p, y in zip(probs, labels) if p >= t and y == 0)
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        tnr = tn / (tn + fp) if (tn + fp) else 0.0
        bal = 0.5 * (tpr + tnr)
        if bal > best["balanced_accuracy"]:
            best = {"threshold": round(t, 3), "balanced_accuracy": round(bal, 4)}
    return best


def find_precision_threshold(probs: list[float], labels: list[int], target_precision: float = 0.90) -> dict:
    """Pick threshold that achieves at least target_precision on validation data; below it routes to human review."""
    if not probs:
        return {"threshold": 0.8, "precision": 0.0, "coverage": 0.0}
    candidates = sorted({round(p, 2) for p in probs} | {0.5, 0.7, 0.8, 0.9})
    best_matching = None
    best_overall = {"threshold": 0.8, "precision": 0.0, "coverage": 0.0}
    best_precision = -1.0

    for t in candidates:
        tp = sum(1 for p, y in zip(probs, labels) if p >= t and y == 1)
        fp = sum(1 for p, y in zip(probs, labels) if p >= t and y == 0)
        total_pos = tp + fp
        if total_pos == 0:
            continue
        prec = tp / total_pos
        cov = total_pos / len(probs)
        if prec > best_precision:
            best_precision = prec
            best_overall = {"threshold": round(t, 3), "precision": round(prec, 4), "coverage": round(cov, 4)}
        if prec >= target_precision:
            if best_matching is None or cov > best_matching["coverage"]:
                best_matching = {"threshold": round(t, 3), "precision": round(prec, 4), "coverage": round(cov, 4)}

    return best_matching or best_overall


def fit(path: Path | str = LABELS_PATH, out: Path | str = MODEL_PATH) -> dict:
    """Fit the combiner on labelled candidates, evaluate on held-out validation split, and persist."""
    import random
    import time

    rows = load_labels(path)
    usable = [r for r in rows if "features" in r and "label" in r]
    if len(usable) < 8:
        return {"fitted": False, "n": len(usable),
                "reason": "need at least 8 labelled candidates"}

    positives = sum(1 for r in usable if r["label"])
    negatives = len(usable) - positives
    if positives == 0 or negatives == 0:
        return {"fitted": False, "n": len(usable),
                "positives": positives, "negatives": negatives,
                "reason": (
                    f"labels have a single class ({positives} positive, "
                    f"{negatives} negative) — fit() needs resolved and "
                    f"unresolved candidates to learn what separates them"
                )}

    # Deterministic train/validation split: if >= 300, hold out at least 100 for validation
    rng = random.Random(42)
    indices = list(range(len(usable)))
    rng.shuffle(indices)
    if len(usable) >= 300:
        val_size = max(100, int(len(usable) * 0.33))
        split_point = len(usable) - val_size
    else:
        split_point = max(1, int(len(usable) * 0.8))
    train_rows = [usable[i] for i in indices[:split_point]]
    val_rows = [usable[i] for i in indices[split_point:]]
    if not val_rows:
        val_rows = train_rows

    x_train = [vector(r["features"]) for r in train_rows]
    y_train = [1 if r["label"] else 0 for r in train_rows]
    x_val = [vector(r["features"]) for r in val_rows]
    y_val = [1 if r["label"] else 0 for r in val_rows]

    model = fit_logistic(x_train, y_train)

    val_probs = [sigmoid(sum(w * v for w, v in zip(model["weights"], row)) + model["bias"])
                 for row in x_val]
    # Temperature scaling fit on validation split
    temp = _fit_temperature(val_probs, y_val)
    model["temperature"] = temp

    val_scaled = temperature_scale(val_probs, temp)
    thr_bal = find_threshold(val_scaled, y_val)
    thr_prec = find_precision_threshold(val_scaled, y_val, target_precision=0.90)

    val_ece_raw = ece(val_probs, y_val)
    val_ece_scaled = ece(val_scaled, y_val)
    val_brier_raw = brier(val_probs, y_val)
    val_brier_scaled = brier(val_scaled, y_val)

    model.update({
        "fitted": True,
        "mode": "logistic",
        "features": FEATURES,
        "n_total": len(usable),
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "temperature": temp,
        "val_ece_raw": round(val_ece_raw, 4),
        "val_ece_scaled": round(val_ece_scaled, 4),
        "val_brier_raw": round(val_brier_raw, 4),
        "val_brier_scaled": round(val_brier_scaled, 4),
        "threshold_balanced": thr_bal["threshold"],
        "balanced_accuracy": thr_bal["balanced_accuracy"],
        "threshold_auto_approve": thr_prec["threshold"],
        "target_precision": thr_prec["precision"],
        "auto_approve_coverage": thr_prec["coverage"],
        "threshold": thr_prec["threshold"],
    })

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model, indent=2), encoding="utf-8")

    # Persist calibration results artifact in results/
    res_cal_path = ROOT / "results" / "calibration.json"
    res_cal_path.parent.mkdir(parents=True, exist_ok=True)
    cal_artifact = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "Logistic regression combiner with temperature scaling on held-out validation split",
        "labels_source": str(path),
        "n_total": len(usable),
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "temperature": temp,
        "val_ece_raw": round(val_ece_raw, 4),
        "val_ece_scaled": round(val_ece_scaled, 4),
        "val_brier_raw": round(val_brier_raw, 4),
        "val_brier_scaled": round(val_brier_scaled, 4),
        "threshold_balanced": thr_bal["threshold"],
        "balanced_accuracy": thr_bal["balanced_accuracy"],
        "threshold_auto_approve_90_precision": thr_prec["threshold"],
        "validation_precision": thr_prec["precision"],
        "validation_coverage": thr_prec["coverage"],
        "weights": {f: round(w, 4) for f, w in zip(FEATURES, model["weights"])},
        "bias": round(model["bias"], 4),
    }
    res_cal_path.write_text(json.dumps(cal_artifact, indent=2), encoding="utf-8")
    return model


def load(path: Path | str = MODEL_PATH) -> dict | None:
    path = Path(path)
    if not path.is_file():
        return None
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return model if model.get("fitted") else None


# ── Scoring ────────────────────────────────────────────────────────────────
# Hand-weighted fallback. Documented as *uncalibrated*: it is a tie-breaker
# heuristic, not a probability.
_FALLBACK = {"mode": "hand_weighted", "threshold": 0.5, "temperature": 1.0,
             "weights": [0.30, 0.20, 0.15, 0.15, 0.35, -0.10, -0.08, -0.05],
             "bias": -0.60}


def combine(features: dict, model: dict | None = None) -> dict:
    """Score one candidate. Returns probability-ish score + provenance."""
    model = model if (model or {}).get("fitted") else _FALLBACK
    row = vector(features)
    raw = sigmoid(sum(w * v for w, v in zip(model["weights"], row)) + model.get("bias", 0.0))
    score = sigmoid(math.log(max(raw, EPS) / (1 - max(raw, EPS))) / max(model.get("temperature", 1.0), 1e-3))
    return {
        "score": round(score, 4),
        "raw": round(raw, 4),
        "mode": model.get("mode", "hand_weighted"),
        "threshold": model.get("threshold", 0.5),
        "temperature": model.get("temperature", 1.0),
        "fitted_n": model.get("n_labels", 0),
        "features": dict(features),
    }
