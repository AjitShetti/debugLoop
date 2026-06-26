import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from harness.dataset import DATASET, run_buggy_code
 
 
def inspect():
    print(f"\n{'═' * 65}")
    print(f"  DebugLoop — Dataset Inspection ({len(DATASET)} test cases)")
    print(f"{'═' * 65}")
 
    categories = {}
    for case in DATASET:
        categories.setdefault(case.category, []).append(case)
 
    for category, cases in categories.items():
        print(f"\n── {category} ({len(cases)} cases) {'─' * (45 - len(category))}")
        for case in cases:
            actual = run_buggy_code(case.buggy_code)
            # Flag if actual == expected (means bug isn't actually broken)
            is_broken = actual.strip() != case.expected_output.strip()
            status = "🐛 broken" if is_broken else "⚠️  NOT BROKEN — fix this case"
 
            print(f"\n  [{case.id:02d}] {status}  (max_steps={case.max_steps})")
            print(f"       Actual  : {actual[:80].replace(chr(10), ' | ')}")
            print(f"       Expected: {case.expected_output}")
 
    print(f"\n{'═' * 65}")
    broken = sum(
        1 for c in DATASET
        if run_buggy_code(c.buggy_code).strip() != c.expected_output.strip()
    )
    print(f"  {broken}/{len(DATASET)} cases confirmed broken (agent has real work to do)")
    if broken == len(DATASET):
        print("\n  ✅ Hour 3 complete. All cases are valid — commit and move to Hour 4.")
    else:
        print(f"\n  ⚠️  {len(DATASET) - broken} case(s) need fixing before Hour 4.")
    print(f"{'═' * 65}\n")
 
 
if __name__ == "__main__":
    inspect()
 