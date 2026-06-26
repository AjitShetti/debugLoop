from debugloop.agent import _parse


def main() -> None:
    parsed = _parse("Thought: I should inspect the code\nAction: run_code\nAction Input: print(1)")
    print(parsed.thought)
    print(parsed.action)
    print(parsed.action_input)


if __name__ == "__main__":
    main()
