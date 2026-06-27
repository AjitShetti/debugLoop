# 🐛 DebugLoop

**Autonomous Python debugging agent built on the ReAct architecture.**  
DebugLoop takes buggy Python code, loops through fix attempts using a structured
think → act → observe cycle, and evaluates itself with a deterministic 25-case harness.

> Built to demonstrate agentic engineering, ReAct loop design, and eval harness engineering —  
> the three core patterns in production AI agent systems.

---

## Demo

<!-- Replace with your screen recording GIF -->
![DebugLoop Demo](assets/demo.gif)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     DebugLoop System                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Input: buggy_code + error_message                     │
│              │                                          │
│              ▼                                          │
│   ┌─────────────────────┐                               │
│   │     ReActLoop       │  ← loops engineering          │
│   │                     │                               │
│   │  ┌───────────────┐  │                               │
│   │  │  DebugAgent   │  │  ← agentic engineering        │
│   │  │  (Groq LLM)   │  │                               │
│   │  └──────┬────────┘  │                               │
│   │         │ Thought   │                               │
│   │         ▼           │                               │
│   │  ┌─────────────┐    │                               │
│   │  │ Tool Router │    │                               │
│   │  └──┬──┬──┬──┬─┘    │                               │
│   │     │  │  │  │      │                               │
│   │  run_code  search_fix│                               │
│   │  read_error submit_fix                              │
│   │         │            │                              │
│   │         ▼ Observation│                              │
│   │    [next iteration]  │                              │
│   └─────────────────────┘                               │
│              │                                          │
│              ▼                                          │
│   ┌─────────────────────┐                               │
│   │    EvalHarness      │  ← harness engineering        │
│   │  25 test cases      │                               │
│   │  3 metrics          │                               │
│   └─────────────────────┘                               │
│              │                                          │
│              ▼                                          │
│         EvalReport                                      │
│  fix_accuracy · step_efficiency · regression_safe       │
└─────────────────────────────────────────────────────────┘
```

---

## The Three Engineering Patterns

### 1. ReAct Loop (Loops Engineering)
Each iteration the agent emits a structured `Thought / Action / Action Input` triple.
The loop dispatches to the matching tool, attaches the `Observation`, and feeds the
full trace back into the next LLM call — giving the agent working memory across steps.

```python
for iteration in range(max_steps):
    step = agent(question, trace)      # think
    if step.action == "submit_fix":
        trace.complete(step.action_input)
        return trace
    observation = tools[step.action](step.action_input)  # act
    step.observation = observation
    trace.add_step(step)               # observe
```

### 2. Agent + Tool Dispatch (Agentic Engineering)
`DebugAgent` wraps a Groq LLM call with a strict ReAct system prompt and builds
full conversation history from the trace on every turn — no framework, no LangChain.

Four tools, each with a distinct purpose:
| Tool | Purpose |
|---|---|
| `run_code` | Execute code in a sandboxed subprocess, observe real stdout/stderr |
| `read_error` | Parse traceback — extract error type and line number |
| `search_fix` | Search a curated fix knowledge base by error pattern |
| `submit_fix` | Terminal action — end the loop, submit the fix |

### 3. Eval Harness (Harness Engineering)
25 deterministic test cases across 5 bug categories. Each case has a known correct
output — the harness scores the agent empirically, not by vibes.

Three metrics per case:
| Metric | Definition |
|---|---|
| `fix_accuracy` | `fixed_code_output == expected_output` |
| `step_efficiency` | `1 - (steps_used - 1) / (max_steps - 1)` |
| `regression_safe` | Fixed code runs without raising any exception |

---

## Benchmark Results

<!-- Replace with your actual harness output -->

| Category | Cases | Fix Accuracy | Avg Efficiency |
|---|---|---|---|
| NameError | 5 | — | — |
| TypeError | 5 | — | — |
| IndexError | 5 | — | — |
| LogicBug | 5 | — | — |
| AttributeError | 5 | — | — |
| **Total** | **25** | **—** | **—** |

> Run `python run_harness.py` to reproduce. Results will vary slightly per run due to LLM non-determinism.

### Prompt Comparison

The harness enables empirical prompt evaluation — swap the system prompt, re-run, compare:

```bash
python run_compare.py --category LogicBug
```

| Prompt Variant | Fix Accuracy | Avg Efficiency | Overall Score |
|---|---|---|---|
| Strict (forced tool order) | — | — | — |
| Flexible (agent decides) | — | — | — |

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/AjitShetti/debugloop.git
cd debugloop

# 2. Install
pip install -r requirements.txt

# 3. Set API key (free at console.groq.com)
export GROQ_API_KEY=your_key_here

# 4. Verify loop works (no API calls)
python test_loop.py

# 5. Run agent on one bug
python main.py

# 6. Run the Streamlit UI
streamlit run app.py

# 7. Run the eval harness
python run_harness.py --category NameError   # one category
python run_harness.py                         # all 25 cases

# 8. Compare prompt variants
python run_compare.py --category LogicBug
```

---

## Project Structure

```
debugloop/
├── debugloop/
│   ├── trace.py        # Step + Trace dataclasses — everything plugs into this
│   ├── react_loop.py   # ReAct loop engine — think → act → observe
│   ├── tools.py        # 4 tools with subprocess sandbox
│   └── agent.py        # Groq-powered agent + ReAct output parser
├── harness/
│   ├── dataset.py      # 25 TestCase objects across 5 bug categories
│   ├── harness.py      # HarnessRunner — runs cases, scores metrics
│   └── report.py       # EvalResult + EvalReport with terminal printer
├── configs/
│   └── prompts.py      # System prompt variants for comparative eval
├── app.py              # Streamlit trace viewer + harness dashboard
├── main.py             # CLI entry point — run agent on one bug
├── run_harness.py      # CLI — full harness run with --case/--category flags
├── run_compare.py      # CLI — prompt A vs B comparison
├── test_loop.py        # Dummy agent test — verifies loop with no API calls
└── inspect_dataset.py  # Dataset validation — confirms all 25 cases are broken
```

---

## Stack

- **LLM**: Groq (`gpt-oss-120b`) — chosen for low latency in a tight loop
- **Agent**: Custom ReAct implementation — no LangChain, no frameworks
- **Sandbox**: Python `subprocess` with 5-second timeout
- **UI**: Streamlit with live trace streaming
- **Eval**: Custom harness — deterministic, reproducible, comparable

---

## Why No LangChain

The entire ReAct loop — conversation history, tool dispatch, trace logging,
stop conditions — is implemented from scratch in ~150 lines.
This was intentional: building the mechanism is how you understand why the
abstractions exist, not just how to use them.

---

## Author

**Ajit Shetti** · [github.com/AjitShetti](https://github.com/AjitShetti)  
B.E. Computer Science (AI & ML) · KLS VDT, Karnataka