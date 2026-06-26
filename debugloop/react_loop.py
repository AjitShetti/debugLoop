from typing import Callable, Dict

from debugloop.trace import Step, Trace


AgentFn = Callable[[str, Trace], Step]
ToolFn = Callable[[str], str]


class ReActLoop:
    TERMINAL_ACTION = "submit_fix"

    def __init__(self, agent: AgentFn, tools: Dict[str, ToolFn], max_steps: int = 8):
        self.agent = agent
        self.tools = tools
        self.max_steps = max_steps

    def run(self, question: str) -> Trace:
        trace = Trace(question=question)

        print(f"\n{'═' * 55}")
        print("🐛 DebugLoop — ReAct Agent")
        print(f"{'═' * 55}")
        print(f"📝 Task: {question[:200]}")

        for _ in range(self.max_steps):
            step = self.agent(question, trace)

            if step.action == self.TERMINAL_ACTION:
                step.observation = "Fix submitted to harness."
                trace.add_step(step)
                trace.complete(step.action_input)
                return trace

            observation = self._dispatch(step.action, step.action_input)
            step.observation = observation
            trace.add_step(step)

        trace.fail()
        return trace

    def _dispatch(self, action: str, action_input: str) -> str:
        if action not in self.tools:
            available = list(self.tools.keys())
            return f"[ToolError] Unknown tool '{action}'. Available tools: {available}"
        try:
            return self.tools[action](action_input)
        except Exception as exc:  # pragma: no cover - defensive path
            return f"[ToolError] {type(exc).__name__}: {exc}"
