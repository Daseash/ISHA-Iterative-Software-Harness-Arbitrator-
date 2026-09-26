"""Phase 4 demo check — LAYA judge scoring, danger detection, verification, triage."""

from src.review.laya_judge import LayaJudge

judge = LayaJudge()

# Test patch scoring
scores = judge.score_patch(
    issue_text="subtract returns wrong result",
    plan="Change a+b to a-b in subtract method",
    patch="- return a + b\n+ return a - b",
)
print("Patch scores:", scores)
assert "composite" in scores, "Missing composite score!"
assert 0 <= scores["composite"] <= 1, "Composite out of range!"

# Test danger detection
dangers = judge.check_dangers("+ os.system('rm -rf /')")
print("Danger check:", dangers)
assert "flagged" in dangers

# Test output verification
verify = judge.verify_output(
    "def subtract(a, b): return a - b",
    "subtract should return a minus b",
)
print("Verification:", verify)
assert "correct_probability" in verify

# Test triage
triage = judge.classify_issue("Payment failed twice, please refund immediately")
print("Triage keys:", sorted(triage.keys()))

print("\nPhase 4 PASSED - LAYA integration working!")
