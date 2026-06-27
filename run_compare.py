import os
import sys
import argparse
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from debugloop.agent import DebugAgent
from harness.harness import HarnessRunner
from harness.report import EvalReport
from configs.prompts import PROMPT_REACT_STRICT, PROMPT_REACT_FLEXIBLE
 
 
# ── Comparison printer ────────────────────────────────────────────────────────
 
def print_comparison(report_a: EvalReport, report_b: EvalReport, label_a: str, label_b: str):
    W = 70
 
    def delta(a: float, b: float) -> str:
        d = b - a
        if abs(d) < 0.001:
            return "  —  "
        arrow = "▲" if d > 0 else "▼"
        color = "better" if d > 0 else "worse"
        return f"{arrow} {abs(d):.2f} ({color})"
 
    print(f"\n{'═' * W}")
    print(f"  DebugLoop — Prompt Comparison")
    print(f"{'═' * W}")
    print(f"\n  {'Metric':<22}  {label_a:<18}  {label_b:<18}  Delta")
    print(f"  {'──────':<22}  {'──────':<18}  {'──────':<18}  ─────")
 
    metrics = [
        ("Fix Accuracy",     report_a.fix_accuracy,       report_b.fix_accuracy),
        ("Avg Efficiency",   report_a.avg_step_efficiency, report_b.avg_step_efficiency),
        ("Regression Safe",  report_a.regression_rate,     report_b.regression_rate),
        ("Overall Score",    report_a.overall_score,       report_b.overall_score),
    ]
 
    for label, val_a, val_b in metrics:
        print(f"  {label:<22}  {val_a:<18.2f}  {val_b:<18.2f}  {delta(val_a, val_b)}")
 
    print(f"\n{'─' * W}")
 
    # Per-category breakdown
    cats = sorted(set(r.category for r in report_a.results))
    print(f"\n  Per-category fix accuracy:\n")
    print(f"  {'Category':<16}  {label_a:<12}  {label_b:<12}  Winner")
    print(f"  {'────────':<16}  {'──────':<12}  {'──────':<12}  ──────")
 
    for cat in cats:
        a_results = [r for r in report_a.results if r.category == cat]
        b_results = [r for r in report_b.results if r.category == cat]
        if not a_results or not b_results:
            continue
        acc_a = sum(r.fix_correct for r in a_results) / len(a_results)
        acc_b = sum(r.fix_correct for r in b_results) / len(b_results)
        winner = label_a if acc_a > acc_b else (label_b if acc_b > acc_a else "Tie")
        print(f"  {cat:<16}  {acc_a:<12.0%}  {acc_b:<12.0%}  {winner}")
 
    # Verdict
    print(f"\n{'─' * W}")
    score_a = report_a.overall_score
    score_b = report_b.overall_score
    if abs(score_a - score_b) < 0.01:
        verdict = "No significant difference between prompts."
    elif score_a > score_b:
        verdict = f"{label_a} wins overall ({score_a:.2f} vs {score_b:.2f})."
    else:
        verdict = f"{label_b} wins overall ({score_b:.2f} vs {score_a:.2f})."
 
    print(f"  Verdict: {verdict}")
    print(f"{'═' * W}\n")
 
 
# ── Main ──────────────────────────────────────────────────────────────────────
 
def main():
    parser = argparse.ArgumentParser(description="DebugLoop prompt comparison")
    parser.add_argument("--category", type=str, help="Run one category only (faster)")
    args = parser.parse_args()
 
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌  Set GROQ_API_KEY: export GROQ_API_KEY=your_key")
        sys.exit(1)
 
    print("\n🔬 Running comparative eval — this will make 2× harness API calls.")
    if args.category:
        print(f"   Category filter: {args.category}")
    print("   Ctrl+C to abort.\n")
 
    # ── Run A: Strict ─────────────────────────────────────────────────────────
    print("── Run 1/2: STRICT prompt ───────────────────────────────────")
    agent_strict = DebugAgent(api_key=api_key, model="llama3-70b-8192")
    agent_strict.system_prompt = PROMPT_REACT_STRICT  # override default
 
    # Patch the agent to use the custom prompt
    from debugloop.agent import _build_messages
    import groq as groq_mod
 
    def _call_with_prompt(agent, system_prompt, question, trace):
        messages = _build_messages(question, trace)
        response = agent.client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.2,
            max_tokens=512,
        )
        from debugloop.agent import _parse
        return _parse(response.choices[0].message.content)
 
    import functools
 
    def make_agent_fn(api_key, system_prompt):
        agent = DebugAgent(api_key=api_key)
        def call(question, trace):
            return _call_with_prompt(agent, system_prompt, question, trace)
        return call
 
    runner_strict = HarnessRunner(
        agent=make_agent_fn(api_key, PROMPT_REACT_STRICT),
        model_name="strict-prompt",
    )
    if args.category:
        report_a = runner_strict.run_category(args.category, verbose=False)
    else:
        report_a = runner_strict.run_all(verbose=False)
 
    print(f"   Done. Score: {report_a.overall_score:.2f}\n")
 
    # ── Run B: Flexible ───────────────────────────────────────────────────────
    print("── Run 2/2: FLEXIBLE prompt ─────────────────────────────────")
    runner_flexible = HarnessRunner(
        agent=make_agent_fn(api_key, PROMPT_REACT_FLEXIBLE),
        model_name="flexible-prompt",
    )
    if args.category:
        report_b = runner_flexible.run_category(args.category, verbose=False)
    else:
        report_b = runner_flexible.run_all(verbose=False)
 
    print(f"   Done. Score: {report_b.overall_score:.2f}\n")
 
    # ── Compare ───────────────────────────────────────────────────────────────
    print_comparison(report_a, report_b, "STRICT", "FLEXIBLE")
 
 
if __name__ == "__main__":
    main()
 