from dataclasses import dataclass, field
from typing import List
from datetime import datetime
 
 
@dataclass
class EvalResult:
    case_id:          int
    category:         str
    completed:        bool    # loop reached submit_fix within budget
    fix_correct:      bool    # fixed code output == expected output
    steps_used:       int
    step_efficiency:  float   # 1 - (steps_used - 1) / (max_steps - 1), clamped [0, 1]
    regression_safe:  bool    # fixed code runs without raising an exception
    actual_output:    str     # what the fixed code actually printed
    expected_output:  str
    error:            str = ""  # populated if the loop itself crashed
 
 
@dataclass
class EvalReport:
    model:      str
    results:    List[EvalResult] = field(default_factory=list)
    run_at:     str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
 
    # ── Aggregate metrics ─────────────────────────────────────────────────────
 
    @property
    def fix_accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.fix_correct for r in self.results) / len(self.results)
 
    @property
    def avg_step_efficiency(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.step_efficiency for r in self.results) / len(self.results)
 
    @property
    def regression_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.regression_safe for r in self.results) / len(self.results)
 
    @property
    def overall_score(self) -> float:
        """
        Weighted composite:
          fix_accuracy     × 0.6  (most important — did it actually fix the bug?)
          avg_efficiency   × 0.2  (how many steps did it burn?)
          regression_rate  × 0.2  (did the fix break anything?)
        """
        return (
            self.fix_accuracy      * 0.6
            + self.avg_step_efficiency * 0.2
            + self.regression_rate     * 0.2
        )
 
    # ── Terminal printer ──────────────────────────────────────────────────────
 
    def print_report(self) -> None:
        W = 70
 
        print(f"\n{'═' * W}")
        print(f"  DebugLoop — Eval Report")
        print(f"  Model : {self.model}")
        print(f"  Cases : {len(self.results)}  |  Run at: {self.run_at}")
        print(f"{'═' * W}")
 
        # Header
        print(f"\n  {'ID':>3}  {'Category':<14}  {'Steps':>5}  {'Correct':>7}  {'Effic':>6}  {'Regress':>8}")
        print(f"  {'──':>3}  {'──────────────':<14}  {'─────':>5}  {'───────':>7}  {'──────':>6}  {'────────':>8}")
 
        for r in self.results:
            correct   = "✅ pass" if r.fix_correct    else "❌ fail"
            regress   = "✅ safe" if r.regression_safe else "⚠️  risk"
            effic_bar = self._bar(r.step_efficiency)
            print(
                f"  {r.case_id:>3}  {r.category:<14}  {r.steps_used:>5}  "
                f"{correct:>7}  {effic_bar}  {regress:>8}"
            )
 
        # Per-category breakdown
        print(f"\n{'─' * W}")
        print("  By category:\n")
        categories = {}
        for r in self.results:
            categories.setdefault(r.category, []).append(r)
 
        for cat, results in categories.items():
            passed = sum(r.fix_correct for r in results)
            avg_eff = sum(r.step_efficiency for r in results) / len(results)
            print(f"    {cat:<16} {passed}/{len(results)} correct   avg efficiency {avg_eff:.2f}")
 
        # Summary
        print(f"\n{'─' * W}")
        print(f"  SUMMARY")
        print(f"  Fix Accuracy    : {sum(r.fix_correct for r in self.results)}/{len(self.results)}  ({self.fix_accuracy:.0%})")
        print(f"  Avg Efficiency  : {self.avg_step_efficiency:.2f}")
        print(f"  Regression Safe : {sum(r.regression_safe for r in self.results)}/{len(self.results)}  ({self.regression_rate:.0%})")
        print(f"  ── Overall Score: {self.overall_score:.2f} / 1.00")
        print(f"{'═' * W}\n")
 
    @staticmethod
    def _bar(score: float) -> str:
        """Render a 5-char efficiency bar."""
        filled = round(score * 5)
        return f"{'█' * filled}{'░' * (5 - filled)}"
 