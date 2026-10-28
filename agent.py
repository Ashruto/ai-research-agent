"""Agentic research assistant: plan -> act (tools) -> observe -> repeat -> answer."""
import os
import sys

import anthropic
from dotenv import load_dotenv

from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
MAX_STEPS = 8  # safety cap on the agent loop

SYSTEM_PROMPT = """You are a research assistant agent.
For every task: (1) briefly plan the steps, (2) call tools as needed
(wikipedia_search for facts, calculator for math, read_notes/save_note for memory),
(3) use tool results to continue until the task is done, (4) give a clear final answer.
Always check read_notes first if the user refers to earlier work."""

client = anthropic.Anthropic()


def run_tool(name: str, args: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Error: unknown tool {name}"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"Error running {name}: {e}"


def run_agent(task: str, history: list | None = None, verbose: bool = True) -> str:
    messages = (history or []) + [{"role": "user", "content": task}]

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(
            model=MODEL, max_tokens=1500, system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":  # agent decided it is done
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"  [step {step}] tool: {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    return "Stopped: reached max steps without a final answer."


if __name__ == "__main__":
    print("Research Agent ready. Type 'exit' to quit.")
    while True:
        task = input("\nYou: ").strip()
        if task.lower() in {"exit", "quit"}:
            sys.exit(0)
        print("\nAgent:", run_agent(task))
