import subprocess
import textwrap
from typing import Callable
 
from harness.dataset import TestCase, DATASET
from harness.report import EvalResult, EvalReport
from debugloop.react_loop import ReActLoop
from debugloop.tools import TOOLS
 
 
AgentFn = Callable
 
 
# ── Metric helpers ────────────────────────────────────────────────────────────
 
def _run_fixed(code: str) -> tuple[str, bool]:
    """
    Execute the fixed code.
    Returns (stdout, exception_free).
    """
    try:
        result = subprocess.run(
            ["python3", "-c", textwrap.dedent(code)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        if stderr and ("Error" in stderr or "Traceback" in stderr):
            return stdout, False          # raised an exception → regression risk
        return stdout, True
    except subprocess.TimeoutExpired:
        return "(timeout)", False
 
 
def _step_efficiency(steps_used: int, max_steps: int) -> float:
    """
    Score how efficiently the agent used its step budget.
      1 step  used → 1.0  (perfect)
      max_steps    → 0.0  (burned the whole budget)
    """
    if max_steps <= 1:
        return 1.0
    raw = 1 - (steps_used - 1) / (max_steps - 1)
    return max(0.0, min(1.0, raw))
 
 
# ── Runner ────────────────────────────────────────────────────────────────────
 
class HarnessRunner:
    def __init__(self, agent: AgentFn, model_name: str = "llama3-70b-8192"):
        self.agent = agent
        self.model_name = model_name
 
    def run_all(
        self,
        dataset: list[TestCase] | None = None,
        verbose: bool = True,
    ) -> EvalReport:
        """Run every case and return a populated EvalReport."""
        dataset = dataset or DATASET
        report = EvalReport(model=self.model_name)
 
        total = len(dataset)
        for i, case in enumerate(dataset, 1):
            if verbose:
                print(f"\n[{i:02d}/{total}] Case {case.id} — {case.category}")
                print(f"{'─' * 55}")
 
            result = self._run_case(case, verbose=verbose)
            report.results.append(result)
 
            if verbose:
                status = "✅ PASS" if result.fix_correct else "❌ FAIL"
                print(f"  → {status}  |  steps: {result.steps_used}  |  efficiency: {result.step_efficiency:.2f}")
 
        return report
 
    def run_category(self, category: str, verbose: bool = True) -> EvalReport:
        """Run only cases from a specific category."""
        subset = [c for c in DATASET if c.category == category]
        if not subset:
            raise ValueError(f"No cases found for category '{category}'")
        return self.run_all(dataset=subset, verbose=verbose)
 
    def run_single(self, case_id: int, verbose: bool = True) -> EvalResult:
        """Run a single case by ID. Useful for debugging."""
        case = next((c for c in DATASET if c.id == case_id), None)
        if not case:
            raise ValueError(f"No case with id={case_id}")
        return self._run_case(case, verbose=verbose)
 
    # ── Internal ──────────────────────────────────────────────────────────────
 
    def _run_case(self, case: TestCase, verbose: bool) -> EvalResult:
        try:
            loop = ReActLoop(
                agent=self.agent,
                tools=TOOLS,
                max_steps=case.max_steps,
            )
            trace = loop.run(case.question)
 
        except Exception as e:
            # Loop itself crashed — record as total failure
            return EvalResult(
                case_id         = case.id,
                category        = case.category,
                completed       = False,
                fix_correct     = False,
                steps_used      = 0,
                step_efficiency = 0.0,
                regression_safe = False,
                actual_output   = "",
                expected_output = case.expected_output,
                error           = f"{type(e).__name__}: {e}",
            )
 
        # ── Evaluate metrics ──────────────────────────────────────────────────
 
        steps_used = len(trace.steps)
 
        # fix_accuracy
        if trace.completed and trace.final_answer:
            actual_output, regression_safe = _run_fixed(trace.final_answer)
            fix_correct = actual_output.strip() == case.expected_output.strip()
        else:
            actual_output  = ""
            regression_safe = False
            fix_correct    = False
 
        efficiency = _step_efficiency(steps_used, case.max_steps)
 
        return EvalResult(
            case_id         = case.id,
            category        = case.category,
            completed       = trace.completed,
            fix_correct     = fix_correct,
            steps_used      = steps_used,
            step_efficiency = efficiency,
            regression_safe = regression_safe,
            actual_output   = actual_output,
            expected_output = case.expected_output,
        )
 