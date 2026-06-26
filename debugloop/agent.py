import os
import re

from groq import Groq

from debugloop.trace import Step, Trace


SYSTEM_PROMPT = """You are DebugLoop, an autonomous Python debugging agent.
Your job is to fix buggy Python code by reasoning step by step.

You have access to exactly 4 tools:
  run_code(code)       — executes Python code, returns stdout or stderr
  read_error(tb)       — parses a traceback, returns error type and line number
  search_fix(query)    — searches a fix knowledge base, returns a fix pattern
  submit_fix(code)     — submits your fixed code and ends the loop (use ONLY when confident)

You MUST respond in this exact format every single turn — no exceptions:

Thought: <your reasoning about what to do next and why>
Action: <exactly one of: run_code, read_error, search_fix, submit_fix>
Action Input: <the input string to pass to the action>

Rules:
- Always run_code first to see the actual error before guessing
- Use read_error to parse the traceback if the error is complex
- Use search_fix with the error type or a short description of the bug
- Only call submit_fix when you have verified the fix logic is correct
- The fixed code in submit_fix must be complete and runnable
- Never add explanation outside of the Thought/Action/Action Input format
"""


def _build_messages(question: str, trace: Trace) -> list[dict]:
    messages = [{"role": "user", "content": question}]

    for step in trace.steps:
        messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Thought: {step.thought}\n"
                    f"Action: {step.action}\n"
                    f"Action Input: {step.action_input}"
                ),
            }
        )
        messages.append({"role": "user", "content": f"Observation: {step.observation}"})

    return messages


def _parse(response_text: str) -> Step:
    thought = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", response_text, re.DOTALL)
    action = re.search(r"Action:\s*(\w+)", response_text)
    action_input = re.search(r"Action Input:\s*(.+)", response_text, re.DOTALL)

    return Step(
        thought=thought.group(1).strip() if thought else "(no thought)",
        action=action.group(1).strip() if action else "run_code",
        action_input=action_input.group(1).strip() if action_input else "",
    )


class DebugAgent:
    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key or os.environ["GROQ_API_KEY"])
        self.model = model

    def __call__(self, question: str, trace: Trace) -> Step:
        messages = _build_messages(question, trace)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            temperature=0.2,
            max_tokens=512,
        )
        text = response.choices[0].message.content
        return _parse(text)
