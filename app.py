import os
import time
import streamlit as st
import sys
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from debugloop.agent import DebugAgent
from debugloop.tools import TOOLS
from debugloop.react_loop import ReActLoop
from debugloop.trace import Trace, Step
from harness.harness import HarnessRunner
from harness.dataset import DATASET
 
# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DebugLoop",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ── Custom CSS — dark terminal aesthetic ──────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');
 
  /* Base */
  html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
  }
  [data-testid="stSidebar"] { background-color: #161b22; }
  [data-testid="stHeader"]  { background-color: #0d1117; }
 
  /* Hide default Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
 
  /* Typography */
  h1 { font-family: 'JetBrains Mono', monospace; color: #00ff88; letter-spacing: -1px; }
  h2, h3 { font-family: 'Inter', sans-serif; color: #e6edf3; font-weight: 600; }
  label, .stTextArea label, .stSelectbox label {
    color: #8b949e !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace !important;
  }
 
  /* Code textarea */
  .stTextArea textarea {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    caret-color: #00ff88;
  }
  .stTextArea textarea:focus {
    border-color: #00ff88 !important;
    box-shadow: 0 0 0 2px rgba(0,255,136,0.15) !important;
  }
 
  /* Buttons */
  .stButton > button {
    background-color: #00ff88 !important;
    color: #0d1117 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
    letter-spacing: 0.05em;
    transition: opacity 0.15s ease;
  }
  .stButton > button:hover { opacity: 0.85 !important; }
  .stButton > button:disabled { background-color: #30363d !important; color: #8b949e !important; }
 
  /* Step cards */
  .step-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.80rem;
    line-height: 1.6;
  }
  .step-card.terminal { border-left: 3px solid #00ff88; }
  .step-card.active   { border-left: 3px solid #f78166; }
 
  .step-label {
    font-size: 0.68rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
  }
  .step-thought { color: #a5d6ff; }
  .step-action  { color: #ff9f0a; font-weight: 600; }
  .step-observe { color: #7ee787; }
 
  /* Metric cards */
  .metric-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
  }
  .metric-card {
    flex: 1;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
  }
  .metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: #00ff88;
  }
  .metric-label {
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
  }
 
  /* Status badge */
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .badge-model { background: #1f2937; color: #8b949e; border: 1px solid #30363d; }
  .badge-pass  { background: rgba(0,255,136,0.12); color: #00ff88; }
  .badge-fail  { background: rgba(247,129,102,0.12); color: #f78166; }
 
  /* Divider */
  hr { border-color: #21262d; margin: 24px 0; }
 
  /* Harness table */
  .stDataFrame { border: 1px solid #30363d !important; border-radius: 8px !important; }
  [data-testid="stDataFrameResizable"] { background: #161b22 !important; }
 
  /* Section headers */
  .section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
  }
 
  /* Selectbox */
  [data-testid="stSelectbox"] > div > div {
    background-color: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
  }
</style>
""", unsafe_allow_html=True)
 
 
# ── Session state init ────────────────────────────────────────────────────────
if "trace_steps" not in st.session_state:
    st.session_state.trace_steps    = []
if "trace_complete" not in st.session_state:
    st.session_state.trace_complete = False
if "final_answer" not in st.session_state:
    st.session_state.final_answer   = None
if "running" not in st.session_state:
    st.session_state.running        = False
if "harness_report" not in st.session_state:
    st.session_state.harness_report = None
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
def render_step(step: Step, idx: int, is_terminal: bool = False) -> str:
    cls = "step-card terminal" if is_terminal else "step-card"
    icon = "✅" if is_terminal else f"[{idx}]"
    obs_html = (
        f'<div class="step-label">Observation</div>'
        f'<div class="step-observe">{step.observation}</div>'
        if step.observation else ""
    )
    return f"""
    <div class="{cls}">
      <div class="step-label">{icon} — Step {idx}</div>
      <div class="step-label" style="margin-top:8px">Thought</div>
      <div class="step-thought">{step.thought}</div>
      <div class="step-label" style="margin-top:8px">Action → <span class="step-action">{step.action}()</span></div>
      <div style="color:#e6edf3; white-space:pre-wrap">{step.action_input[:300]}{'…' if len(step.action_input)>300 else ''}</div>
      {obs_html}
    </div>
    """
 
def get_agent():
    api_key = st.session_state.get("api_key") or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    return DebugAgent(api_key=api_key, model="llama3-70b-8192")
 
def efficiency_bar(score: float) -> str:
    filled = round(score * 5)
    return "█" * filled + "░" * (5 - filled)
 
 
# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:baseline; gap:16px; margin-bottom:4px">
  <h1 style="margin:0">🐛 DebugLoop</h1>
  <span class="badge badge-model">llama3-70b · groq</span>
</div>
<p style="color:#8b949e; font-size:0.88rem; margin:0 0 24px 0">
  Autonomous Python debugging via ReAct — think → act → observe → fix
</p>
""", unsafe_allow_html=True)
 
# ── API key (sidebar) ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    api_key_input = st.text_input(
        "GROQ API KEY",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        help="Get a free key at console.groq.com"
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#8b949e'>"
        "Built with Groq · llama3-70b-8192<br>"
        "ReAct loop · Eval harness · Streamlit"
        "</div>", unsafe_allow_html=True
    )
 
# ── Main layout ───────────────────────────────────────────────────────────────
col_input, col_trace = st.columns([1, 1], gap="large")
 
# ── LEFT: Code input ──────────────────────────────────────────────────────────
with col_input:
    st.markdown('<div class="section-label">Buggy Python Code</div>', unsafe_allow_html=True)
 
    # Quick examples
    examples = {
        "Select an example…": "",
        "NameError — typo in variable": (
            "def greet(name):\n"
            "    message = f'Hello, {name}!'\n"
            "    print(mesage)\n\n"
            "greet('Ajit')"
        ),
        "LogicBug — wrong palindrome check": (
            "def is_palindrome(s):\n"
            "    for i in range(len(s)):\n"
            "        if s[i] != s[len(s) - i]:\n"
            "            return False\n"
            "    return True\n\n"
            "print(is_palindrome('racecar'))"
        ),
        "TypeError — string + int": (
            "scores = [85, 90, 78, 92]\n"
            "print('Total: ' + sum(scores))"
        ),
        "IndexError — off by one": (
            "def first_and_last(lst):\n"
            "    return lst[0], lst[len(lst)]\n\n"
            "print(first_and_last([10, 20, 30]))"
        ),
        "LogicBug — second largest": (
            "def second_largest(nums):\n"
            "    nums.sort()\n"
            "    return nums[-2]\n\n"
            "print(second_largest([5, 5, 5]))"
        ),
    }
 
    selected = st.selectbox("QUICK EXAMPLES", list(examples.keys()))
 
    default_code = examples[selected] if selected != "Select an example…" else (
        "# Paste your buggy Python code here\n"
        "def add(a, b):\n"
        "    return a + b\n\n"
        "print(add('5', 3))"
    )
 
    buggy_code = st.text_area(
        "CODE",
        value=default_code,
        height=280,
        label_visibility="collapsed",
    )
 
    expected = st.text_input(
        "EXPECTED OUTPUT (optional — helps the agent)",
        placeholder="e.g. Hello, Ajit!",
    )
 
    run_clicked = st.button(
        "▶  Run DebugLoop",
        disabled=st.session_state.running,
        use_container_width=True,
    )
 
    # Stats if trace exists
    if st.session_state.trace_steps:
        st.markdown("---")
        steps = st.session_state.trace_steps
        complete = st.session_state.trace_complete
        badge = '<span class="badge badge-pass">✅ Fixed</span>' if complete else '<span class="badge badge-fail">❌ Not fixed</span>'
        st.markdown(
            f"{badge} &nbsp; "
            f"<span style='color:#8b949e; font-size:0.82rem; font-family:JetBrains Mono'>"
            f"{len(steps)} steps used</span>",
            unsafe_allow_html=True,
        )
 
# ── RIGHT: Trace stream ───────────────────────────────────────────────────────
with col_trace:
    st.markdown('<div class="section-label">Agent Trace</div>', unsafe_allow_html=True)
 
    trace_placeholder = st.empty()
 
    # Render existing steps
    def render_trace():
        if not st.session_state.trace_steps:
            trace_placeholder.markdown(
                '<div style="color:#8b949e; font-family:JetBrains Mono; font-size:0.82rem; '
                'padding:24px; text-align:center; border:1px dashed #30363d; border-radius:8px">'
                '← paste code and click Run<br><br>'
                'Trace will stream here step by step'
                '</div>',
                unsafe_allow_html=True,
            )
            return
 
        html = ""
        for i, step in enumerate(st.session_state.trace_steps, 1):
            is_last = (i == len(st.session_state.trace_steps))
            is_terminal = is_last and st.session_state.trace_complete
            html += render_step(step, i, is_terminal=is_terminal)
 
        if st.session_state.trace_complete and st.session_state.final_answer:
            html += f"""
            <div class="step-card" style="border-left:3px solid #00ff88; margin-top:4px">
              <div class="step-label">✅ Fixed Code</div>
              <pre style="color:#7ee787; margin:8px 0 0 0; font-size:0.78rem; white-space:pre-wrap">{st.session_state.final_answer[:600]}</pre>
            </div>
            """
 
        trace_placeholder.markdown(html, unsafe_allow_html=True)
 
    render_trace()
 
 
# ── Run logic ─────────────────────────────────────────────────────────────────
if run_clicked:
    agent = get_agent()
    if not agent:
        st.error("Add your Groq API key in the sidebar first.")
    elif not buggy_code.strip():
        st.warning("Paste some buggy code first.")
    else:
        # Reset state
        st.session_state.trace_steps    = []
        st.session_state.trace_complete = False
        st.session_state.final_answer   = None
        st.session_state.running        = True
 
        question = (
            f"Fix this buggy Python code:\n```python\n{buggy_code.strip()}\n```"
            + (f"\n\nExpected output: {expected}" if expected else "")
        )
 
        # Streaming callback — updates trace after each step
        def on_step(step: Step):
            st.session_state.trace_steps.append(step)
            html = "".join(
                render_step(s, i + 1) for i, s in enumerate(st.session_state.trace_steps)
            )
            trace_placeholder.markdown(html, unsafe_allow_html=True)
            time.sleep(0.3)  # brief pause so user sees each step arrive
 
        # Monkey-patch loop to accept callback
        original_run = ReActLoop.run
 
        def run_with_callback(self, question: str) -> Trace:
            trace = Trace(question=question)
            for _ in range(self.max_steps):
                step = self.agent(question, trace)
                if step.action == ReActLoop.TERMINAL_ACTION:
                    step.observation = "Fix submitted."
                    trace.add_step(step)
                    trace.complete(step.action_input)
                    on_step(step)
                    return trace
                observation = self._dispatch(step.action, step.action_input)
                step.observation = observation
                trace.add_step(step)
                on_step(step)
            trace.fail()
            return trace
 
        ReActLoop.run = run_with_callback
 
        loop = ReActLoop(agent=agent, tools=TOOLS, max_steps=8)
 
        try:
            trace = loop.run(question)
            st.session_state.trace_complete = trace.completed
            st.session_state.final_answer   = trace.final_answer
        except Exception as e:
            st.error(f"Agent error: {e}")
        finally:
            ReActLoop.run = original_run
            st.session_state.running = False
 
        st.rerun()
 
 
# ── Harness section ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Eval Harness — 25 Test Cases</div>', unsafe_allow_html=True)
 
harness_col1, harness_col2 = st.columns([1, 3], gap="large")
 
with harness_col1:
    category_options = ["All (25 cases)", "NameError", "TypeError", "IndexError", "LogicBug", "AttributeError"]
    harness_category = st.selectbox("CATEGORY", category_options)
 
    run_harness_btn = st.button(
        "▶  Run Harness",
        use_container_width=True,
        key="harness_btn",
    )
    st.markdown(
        "<div style='font-size:0.72rem; color:#8b949e; margin-top:8px'>"
        "⚠️ Full run uses ~100 Groq API calls. Start with one category."
        "</div>",
        unsafe_allow_html=True,
    )
 
with harness_col2:
    harness_display = st.empty()
 
    if st.session_state.harness_report:
        report = st.session_state.harness_report
        import pandas as pd
 
        # Metrics row
        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-card">
            <div class="metric-value">{report.fix_accuracy:.0%}</div>
            <div class="metric-label">Fix Accuracy</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{report.avg_step_efficiency:.2f}</div>
            <div class="metric-label">Avg Efficiency</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{report.regression_rate:.0%}</div>
            <div class="metric-label">Regression Safe</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{report.overall_score:.2f}</div>
            <div class="metric-label">Overall Score</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
 
        # Results table
        rows = []
        for r in report.results:
            rows.append({
                "ID":        r.case_id,
                "Category":  r.category,
                "Steps":     r.steps_used,
                "Correct":   "✅" if r.fix_correct    else "❌",
                "Efficiency": efficiency_bar(r.step_efficiency),
                "Regression": "✅ safe" if r.regression_safe else "⚠️ risk",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=280)
 
    else:
        harness_display.markdown(
            '<div style="color:#8b949e; font-family:JetBrains Mono; font-size:0.82rem; '
            'padding:24px; text-align:center; border:1px dashed #30363d; border-radius:8px">'
            'Run the harness to benchmark your agent across 25 test cases'
            '</div>',
            unsafe_allow_html=True,
        )
 
 
if run_harness_btn:
    agent = get_agent()
    if not agent:
        st.error("Add your Groq API key in the sidebar first.")
    else:
        runner = HarnessRunner(agent=agent, model_name="llama3-70b-8192")
        with st.spinner("Running harness… this may take a few minutes"):
            if harness_category == "All (25 cases)":
                report = runner.run_all(verbose=False)
            else:
                report = runner.run_category(harness_category, verbose=False)
        st.session_state.harness_report = report
        st.rerun()
 