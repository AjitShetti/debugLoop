from dataclasses import dataclass
 
 
@dataclass
class TestCase:
    id: int
    category: str
    buggy_code: str
    expected_output: str   # exact string the fixed code should print
    max_steps: int = 6
 
    @property
    def question(self) -> str:
        result = run_buggy_code(self.buggy_code)
        return (
            f"Fix this buggy Python code:\n"
            f"```python\n{self.buggy_code.strip()}\n```\n\n"
            f"When run, it produces:\n{result}\n\n"
            f"Expected output: {self.expected_output}"
        )
 
 
def run_buggy_code(code: str) -> str:
    """Run the buggy code and return its actual output (error or wrong result)."""
    import subprocess, textwrap
    try:
        result = subprocess.run(
            ["python3", "-c", textwrap.dedent(code)],
            capture_output=True, text=True, timeout=5,
        )
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        if stderr:
            lines = stderr.splitlines()
            return "\n".join(lines[-3:])
        return stdout or "(no output)"
    except subprocess.TimeoutExpired:
        return "(timeout)"
 
 
# ── Category 1: NameError (5 cases) ──────────────────────────────────────────
 
NAMEERROR_CASES = [
    TestCase(
        id=1,
        category="NameError",
        buggy_code="""
def greet(name):
    message = f"Hello, {name}!"
    print(mesage)
 
greet("Ajit")
""",
        expected_output="Hello, Ajit!",
    ),
    TestCase(
        id=2,
        category="NameError",
        buggy_code="""
def circle_area(r):
    return PI * r * r
 
print(circle_area(5))
""",
        expected_output="78.53981633974483",
    ),
    TestCase(
        id=3,
        category="NameError",
        buggy_code="""
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Average: {total / lenght}")
""",
        expected_output="Average: 3.0",
    ),
    TestCase(
        id=4,
        category="NameError",
        buggy_code="""
def factorial(n):
    if n == 0:
        return 1
    return n * factorail(n - 1)
 
print(factorial(5))
""",
        expected_output="120",
    ),
    TestCase(
        id=5,
        category="NameError",
        buggy_code="""
x = 10
y = 20
print(X + y)
""",
        expected_output="30",
    ),
]
 
 
# ── Category 2: TypeError (5 cases) ──────────────────────────────────────────
 
TYPEERROR_CASES = [
    TestCase(
        id=6,
        category="TypeError",
        buggy_code="""
def add(a, b):
    return a + b
 
print(add("5", 3))
""",
        expected_output="8",
    ),
    TestCase(
        id=7,
        category="TypeError",
        buggy_code="""
age = input if True else 25
print(f"Age is: {age + 1}")
""",
        expected_output="Age is: 26",
    ),
    TestCase(
        id=8,
        category="TypeError",
        buggy_code="""
def repeat_char(char, times):
    return char * times
 
print(repeat_char("x", "3"))
""",
        expected_output="xxx",
    ),
    TestCase(
        id=9,
        category="TypeError",
        buggy_code="""
scores = [85, 90, 78, 92]
print("Total: " + sum(scores))
""",
        expected_output="Total: 345",
    ),
    TestCase(
        id=10,
        category="TypeError",
        buggy_code="""
def power(base, exp):
    return base ** exp
 
print(power(2, "3"))
""",
        expected_output="8",
    ),
]
 
 
# ── Category 3: IndexError (5 cases) ─────────────────────────────────────────
 
INDEXERROR_CASES = [
    TestCase(
        id=11,
        category="IndexError",
        buggy_code="""
items = ["a", "b", "c"]
print(items[3])
""",
        expected_output="c",
    ),
    TestCase(
        id=12,
        category="IndexError",
        buggy_code="""
def last_two(lst):
    return lst[-1], lst[-2]
 
print(last_two([42]))
""",
        expected_output="(42, None)",
    ),
    TestCase(
        id=13,
        category="IndexError",
        buggy_code="""
matrix = [[1, 2], [3, 4]]
for i in range(3):
    print(matrix[i][0])
""",
        expected_output="1\n3",
    ),
    TestCase(
        id=14,
        category="IndexError",
        buggy_code="""
word = "hello"
print(word[5])
""",
        expected_output="o",
    ),
    TestCase(
        id=15,
        category="IndexError",
        buggy_code="""
def first_and_last(lst):
    return lst[0], lst[len(lst)]
 
print(first_and_last([10, 20, 30]))
""",
        expected_output="(10, 30)",
    ),
]
 
 
# ── Category 4: LogicBug (5 cases) ───────────────────────────────────────────
# These run without error but produce wrong output — hardest for the agent
 
LOGICBUG_CASES = [
    TestCase(
        id=16,
        category="LogicBug",
        buggy_code="""
def is_even(n):
    return n % 2 == 1
 
print(is_even(4))
""",
        expected_output="True",
    ),
    TestCase(
        id=17,
        category="LogicBug",
        buggy_code="""
def celsius_to_fahrenheit(c):
    return (c - 32) * 5 / 9
 
print(round(celsius_to_fahrenheit(100), 2))
""",
        expected_output="212.0",
        max_steps=4,  # Should be straightforward — tighter budget
    ),
    TestCase(
        id=18,
        category="LogicBug",
        buggy_code="""
def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for char in s:
        if char in vowels:
            count += 1
        count += 1
    return count
 
print(count_vowels("hello"))
""",
        expected_output="2",
    ),
    TestCase(
        id=19,
        category="LogicBug",
        buggy_code="""
def second_largest(nums):
    nums.sort()
    return nums[-2]
 
print(second_largest([5, 5, 5]))
""",
        expected_output="None",
    ),
    TestCase(
        id=20,
        category="LogicBug",
        buggy_code="""
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a
    return a
 
print(fibonacci(6))
""",
        expected_output="8",
    ),
]
 
 
# ── Category 5: AttributeError (5 cases) ─────────────────────────────────────
 
ATTRIBUTEERROR_CASES = [
    TestCase(
        id=21,
        category="AttributeError",
        buggy_code="""
name = "ajit"
print(name.upper)
""",
        expected_output="AJIT",
    ),
    TestCase(
        id=22,
        category="AttributeError",
        buggy_code="""
numbers = [3, 1, 4, 1, 5]
numbers.sort()
print(numbers.length())
""",
        expected_output="5",
    ),
    TestCase(
        id=23,
        category="AttributeError",
        buggy_code="""
x = 42
print(x.append(1))
""",
        expected_output="[42, 1]",
    ),
    TestCase(
        id=24,
        category="AttributeError",
        buggy_code="""
data = {"name": "Ajit", "age": 22}
print(data.name)
""",
        expected_output="Ajit",
    ),
    TestCase(
        id=25,
        category="AttributeError",
        buggy_code="""
items = (1, 2, 3)
items.append(4)
print(items)
""",
        expected_output="(1, 2, 3, 4)",
    ),
]
 
 
# ── Full dataset ──────────────────────────────────────────────────────────────
 
DATASET: list[TestCase] = (
    NAMEERROR_CASES
    + TYPEERROR_CASES
    + INDEXERROR_CASES
    + LOGICBUG_CASES
    + ATTRIBUTEERROR_CASES
)