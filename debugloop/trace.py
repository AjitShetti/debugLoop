from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Step:
    thought: str
    action: str
    action_input: str
    observation: Optional[str] = None


@dataclass
class Trace:
    question: str
    steps: List[Step] = field(default_factory=list)
    final_answer: Optional[str] = None
    completed: bool = False

    def add_step(self, step: Step) -> None:
        self.steps.append(step)
        self._print_step(step)

    def complete(self, answer: str) -> None:
        self.final_answer = answer
        self.completed = True
        print(f"\n✅ Fix submitted.")
        print(f"📊 Steps taken: {len(self.steps)}")
        print(f"\n{'─' * 55}")
        print("Fixed code:")
        print(answer)

    def fail(self) -> None:
        self.completed = False
        print(f"\n⚠️  Budget exhausted after {len(self.steps)} steps — no fix found.")

    def _print_step(self, step: Step) -> None:
        idx = len(self.steps)
        print(f"\n{'─' * 55}")
        print(f"[Step {idx}]")
        print(f"🤔 Thought:  {step.thought}")
        print(f"⚡ Action:   {step.action}")
        print(f"📥 Input:    {step.action_input[:120]}{'...' if len(step.action_input) > 120 else ''}")
        if step.observation:
            print(f"👁  Observe:  {step.observation[:200]}{'...' if len(step.observation) > 200 else ''}")
