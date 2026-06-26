import sys
import os
import argparse
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from harness.harness import HarnessRunner
from harness.dataset import DATASET
from debugloop.agent import DebugAgent
from debugloop.trace import Trace, Step
 
 
# ── Dummy agent for --dry-run ─────────────────────────────────────────────────
 
_dummy_steps = [
    Step(thought="Running the code to see the error.", action="run_code", action_input="print('fixed')"),
    Step(thought="I have enough to submit a fix.",     action="submit_fix", action_input="print('fixed')"),
]
 
def _dummy_agent(question: str, trace: Trace) -> Step:
    idx = min(len(trace.steps), len(_dummy_steps) - 1)
    return _dummy_steps[idx]
 
 
# ── CLI ───────────────────────────────────────────────────────────────────────
 
def main():
    parser = argparse.ArgumentParser(description="DebugLoop Eval Harness")
    parser.add_argument("--case",     type=int,   help="Run a single case by ID")
    parser.add_argument("--category", type=str,   help="Run one category (e.g. LogicBug)")
    parser.add_argument("--dry-run",  action="store_true", help="Use dummy agent — no Groq calls")
    parser.add_argument("--model",    type=str,   default="llama3-70b-8192")
    args = parser.parse_args()
 
    # ── Agent selection ───────────────────────────────────────────────────────
    if args.dry_run:
        print("\n⚡ Dry run — using dummy agent (no Groq calls)")
        agent = _dummy_agent
        model_name = "dummy"
    else:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("❌  Set GROQ_API_KEY before running: export GROQ_API_KEY=your_key")
            sys.exit(1)
        agent      = DebugAgent(api_key=api_key, model=args.model)
        model_name = args.model
 
    runner = HarnessRunner(agent=agent, model_name=model_name)
 
    # ── Run ───────────────────────────────────────────────────────────────────
    if args.case:
        result = runner.run_single(args.case, verbose=True)
        print(f"\nCase {result.case_id} result:")
        print(f"  Correct   : {result.fix_correct}")
        print(f"  Steps     : {result.steps_used}")
        print(f"  Efficiency: {result.step_efficiency:.2f}")
        print(f"  Regression: {'safe' if result.regression_safe else 'risk'}")
        print(f"  Output    : {result.actual_output}")
        print(f"  Expected  : {result.expected_output}")
        if result.error:
            print(f"  Error     : {result.error}")
 
    elif args.category:
        report = runner.run_category(args.category, verbose=True)
        report.print_report()
 
    else:
        report = runner.run_all(verbose=True)
        report.print_report()
 
 
if __name__ == "__main__":
    main()
 