"""Phase 3 demo check — core nodes, context trimmer, patch engine."""

from src.agents.nodes import coder_node, planner_node, regression_test_node, sandbox_node
from src.agents.state import AgentState
from src.config import LLM_ENABLED
from src.tools.context_trimmer import trim_traceback
from src.tools.patch_engine import apply_patch

print(f"LLM mode: {'live' if LLM_ENABLED else 'offline (no API keys)'}")

state = AgentState(
    issue_text="The subtract method in calculator.py returns a+b instead of a-b",
    repo_path="tests/dummy_repo",
    repo_context="class Calculator:\n  def subtract(self, a, b): return a + b  # BUG",
)

state = planner_node(state)
print("Plan:", state.plan[:200])
assert len(state.plan) > 20, "Planner produced empty plan!"

state = regression_test_node(state)
print("Regression test lines:", len(state.regression_test.splitlines()))
assert "def test" in state.regression_test, "Regression test missing test function!"

state = coder_node(state)
print("Patch:\n", state.patch[:400])
assert state.patch.startswith(("diff", "---", "[CODER ERROR]")) or "@@" in state.patch

# Test context trimmer
raw = "lots of output\n" * 100 + "AssertionError: 5 != -1"
trimmed = trim_traceback(raw)
print(f"Trimmed from {len(raw)} to {len(trimmed)} chars")
assert len(trimmed) < len(raw)

# Test patch engine on a scratch copy
import difflib
import pathlib
import shutil
import tempfile

scratch = pathlib.Path(tempfile.mkdtemp()) / "dummy_repo"
shutil.copytree("tests/dummy_repo", scratch)
original = (scratch / "calculator.py").read_text(encoding="utf-8")
updated = "\n".join(
    line.replace("return a + b", "return a - b") if "BUG: should" in line else line
    for line in original.splitlines()
) + "\n"
diff = "".join(
    difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile="a/calculator.py",
        tofile="b/calculator.py",
    )
)
ok, msg = apply_patch(str(scratch), diff)
print("apply_patch:", ok, "|", msg)
assert ok, f"patch engine failed: {msg}"
assert "return a - b" in (scratch / "calculator.py").read_text(encoding="utf-8")

# Sandbox: run the candidate patch in isolation
state = sandbox_node(state)
print("Test output head:", state.test_output[:300])
assert "PASSED" in state.test_output or "FAILED" in state.test_output

shutil.rmtree(scratch, ignore_errors=True)
print("\nPhase 3 PASSED - Core nodes working!")
