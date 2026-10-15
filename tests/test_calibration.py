"""P0-01 regression tests: calibration math must be logistic, finite, and honest.

- sigmoid(0) == 0.5 (was tanh bug: old code returned 0.0)
- temperature_scale monotonic + finite on saturated probs (0.0/1.0)
- fit_logistic separates trivially separable data
- combine() exposes threshold_balanced / threshold_auto_approve / fitted_n (n_total)
"""

import math

from src.review import calibration as C


def test_sigmoid_zero_is_half():
    assert C.sigmoid(0.0) == 0.5


def test_sigmoid_limits_and_symmetry():
    assert C.sigmoid(60.0) > 1 - 1e-9
    assert C.sigmoid(-60.0) < 1e-9
    for z in (-3.0, -0.7, 0.2, 1.5, 4.0):
        assert abs(C.sigmoid(z) + C.sigmoid(-z) - 1.0) < 1e-12


def test_sigmoid_monotonic():
    zs = [-10, -2, -0.5, 0, 0.5, 2, 10]
    ps = [C.sigmoid(z) for z in zs]
    assert all(b > a for a, b in zip(ps, ps[1:]))
    assert all(0.0 < p < 1.0 for p in ps)


def test_temperature_scale_monotonic_and_finite():
    probs = [0.0, 0.05, 0.5, 0.95, 1.0]
    scaled = C.temperature_scale(probs, 0.35)
    assert all(math.isfinite(p) for p in scaled)
    assert all(0.0 <= p <= 1.0 for p in scaled)
    assert all(b >= a for a, b in zip(scaled, scaled[1:]))
    # Interior probs stay interior (only the clamped rails may saturate).
    mid = C.temperature_scale([0.05, 0.5, 0.95], 0.35)
    assert all(0.0 < p < 1.0 for p in mid)


def test_temperature_scale_t1_identityish():
    probs = [0.1, 0.5, 0.9]
    scaled = C.temperature_scale(probs, 1.0)
    for p, s in zip(probs, scaled):
        assert abs(p - s) < 1e-6


def test_fit_logistic_separates():
    x = [[0.0], [0.1], [0.9], [1.0]]
    y = [0, 0, 1, 1]
    m = C.fit_logistic(x, y)
    assert m["weights"][0] > 0
    assert m["n"] == 4


def test_combine_keys_and_fitted_n():
    feats = {
        "laya_fix_quality": 0.9, "laya_matches_issue": 1.0,
        "laya_safe_to_apply": 1.0, "gate_ok": 1.0, "repro_ok": 1.0,
        "regression_count": 0.0, "diff_size": 10.0, "files_changed": 1.0,
    }
    model = {"fitted": True, "mode": "logistic", "threshold": 0.7,
             "threshold_balanced": 0.55, "threshold_auto_approve": 0.8,
             "temperature": 0.35, "n_total": 212,
             "weights": [0.5] * 8, "bias": -1.0}
    out = C.combine(feats, model)
    assert out["threshold_balanced"] == 0.55
    assert out["threshold_auto_approve"] == 0.8
    assert out["fitted_n"] == 212
    assert 0.0 < out["score"] < 1.0


def test_combine_fallback_marks_mode():
    out = C.combine({k: 0.0 for k in C.FEATURES})
    assert out["mode"] == "hand_weighted"
