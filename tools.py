"""Tools the agent can call. Each tool = a Python function + a JSON schema."""
import ast
import json
import operator
import os
from datetime import datetime

import requests

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.json")

# ---------- Tool implementations ----------

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Safely evaluate a math expression (no eval())."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


def wikipedia_search(query: str) -> str:
    """Return the intro summary of the best-matching Wikipedia article."""
    try:
        headers = {"User-Agent": "ai-research-agent/1.0 (student project)"}
        s = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": query, "limit": 1, "format": "json"},
            headers=headers, timeout=10,
        ).json()
        if not s[1]:
            return "No Wikipedia article found."
        title = s[1][0]
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            headers=headers, timeout=10,
        ).json()
        return f"{r.get('title')}: {r.get('extract', 'No summary available.')}"
    except Exception as e:
        return f"Error: {e}"


def get_datetime() -> str:
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")


def _load_notes() -> list:
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE) as f:
            return json.load(f)
    return []


def save_note(title: str, content: str) -> str:
    notes = _load_notes()
    notes.append({"title": title, "content": content, "saved_at": get_datetime()})
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)
    return f"Saved note '{title}'."


def read_notes() -> str:
    notes = _load_notes()
    return json.dumps(notes, indent=2) if notes else "No notes saved yet."


# ---------- Schemas given to the model ----------

TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Evaluate a math expression, e.g. '(12*8)/3 + 2**4'.",
        "input_schema": {"type": "object",
                         "properties": {"expression": {"type": "string"}},
                         "required": ["expression"]},
    },
    {
        "name": "wikipedia_search",
        "description": "Look up a topic on Wikipedia and get its summary. Use for facts.",
        "input_schema": {"type": "object",
                         "properties": {"query": {"type": "string"}},
                         "required": ["query"]},
    },
    {
        "name": "get_datetime",
        "description": "Get the current local date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "save_note",
        "description": "Save a finding to long-term memory (notes file) for later.",
        "input_schema": {"type": "object",
                         "properties": {"title": {"type": "string"},
                                        "content": {"type": "string"}},
                         "required": ["title", "content"]},
    },
    {
        "name": "read_notes",
        "description": "Read all notes previously saved to long-term memory.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "wikipedia_search": wikipedia_search,
    "get_datetime": get_datetime,
    "save_note": save_note,
    "read_notes": read_notes,
}
