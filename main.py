import os
from dotenv import load_dotenv
from debugloop.agent import DebugAgent
from debugloop.tools import TOOLS
from debugloop.react_loop import ReActLoop


BUGGY_CODE = """
def second_largest(nums):
    nums.sort()
    return nums[-2]

print(second_largest([5, 5, 5]))
"""

QUESTION = (
    f"Fix this buggy Python code:\n"
    f"```python\n{BUGGY_CODE.strip()}\n```\n\n"
    f"Expected output: None\n"
    f"Actual output:   5\n\n"
    f"The function should return the second largest DISTINCT value, or None if it doesn't exist."
)


if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GROQ_API_KEY in .env file or environment variable")

    agent = DebugAgent(api_key=api_key)
    loop = ReActLoop(agent=agent, tools=TOOLS, max_steps=8)
    trace = loop.run(QUESTION)

    print(f"\n{'═' * 55}")
    print(f"Result  : {'✅ Fixed' if trace.completed else '❌ Not fixed'}")
    print(f"Steps   : {len(trace.steps)}")
    print(f"{'═' * 55}")
