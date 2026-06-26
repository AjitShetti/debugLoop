import re
import subprocess
import textwrap

# Fix knowledge base
_KB: dict[str, str] = {
    "NameError": "Variable used before assignment. Check spelling and scope.",
    "TypeError": "Wrong type passed. Check argument types, count, and operator compatibility.",
    "IndexError": "Index out of range. Check list length before indexing.",
    "AttributeError": "Object doesn't have that attribute. Check the object's type.",
    "ZeroDivisionError": "Division by zero. Add guard: `if denominator != 0`.",
    "KeyError": "Dict key missing. Use `.get(key)` or check with `key in dict`.",
    "ValueError": "Invalid value passed. Check input validation and type conversion.",
    "RecursionError": "Infinite recursion. Check base case in recursive function.",
    "second largest": "Deduplicate with set(), sort, check len >= 2 before indexing.",
    "off by one": "Last valid index is len(lst) - 1. Range end is exclusive.",
    "none comparison": "Use `is None` not `== None`.",
    "mutable default": "Use None as default, initialise inside function body.",
    "string int concat": "Convert int to str with str() before concatenation.",
    "empty list": "Check `if not lst` or `len(lst) == 0` before accessing elements.",
    "infinite loop": "Ensure loop variable is modified inside the loop body.",
    "logic bug": "Trace through with a concrete example. Check condition direction (</>).",
}


def run_code(code: str) -> str:
    try:
        result = subprocess.run(
            ["python", "-c", textwrap.dedent(code)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()

        if stderr:
            lines = stderr.splitlines()
            trimmed = "\n".join(lines[-3:])
            return f"STDERR:\n{trimmed}"

        return f"STDOUT:\n{stdout}" if stdout else "(no output produced)"
    except subprocess.TimeoutExpired:
        return "[ToolError] Execution timed out (5s limit). Possible infinite loop."
    except FileNotFoundError:
        return "[ToolError] Python executable not found."


def read_error(tb: str) -> str:
    if not tb:
        return "(no traceback)"

    lines = [line.strip() for line in tb.splitlines() if line.strip()]
    if not lines:
        return "(no traceback)"

    for line in lines:
        if line.startswith("Traceback"):
            continue
        if "Error" in line or "Exception" in line:
            return line
    return lines[-1]


def search_fix(query: str) -> str:
    q = query.lower()
    for key, advice in _KB.items():
        if key.lower() in q:
            return advice
    return "No known fix pattern found; inspect the traceback and code manually."


def submit_fix(code: str) -> str:
    return code


TOOLS = {
    "run_code": run_code,
    "read_error": read_error,
    "search_fix": search_fix,
    "submit_fix": submit_fix,
}
