**Name:** Anahid Sherieff

**Reg No:** 23BME1034

# AI Research Agent (Agentic AI)

An autonomous agent that takes a goal, plans, chooses tools on its own, observes results, and loops until it can give a final answer. It also has long-term memory (saved notes).

## Architecture / Schema

```
                 ┌──────────────┐
   User task ──▶ │   agent.py   │  (system prompt + loop, max 8 steps)
                 └──────┬───────┘
                        │ messages + tool schemas
                        ▼
                 ┌──────────────┐
                 │  LLM (Claude)│  reasons / plans
                 └──────┬───────┘
          stop_reason = tool_use │ stop_reason = end_turn
                        │              └──────▶ Final answer to user
                        ▼
                 ┌──────────────┐
                 │  tools.py    │  executes the chosen tool
                 └──────┬───────┘
     ┌──────────┬───────┼────────────┬─────────────┐
     ▼          ▼       ▼            ▼             ▼
 calculator  wikipedia  get_datetime save_note  read_notes
  (safe AST)  _search                 └──── notes.json (memory)
                        │
                        ▼
              tool_result fed back to LLM  ──▶ loop continues
```

### Agent loop (pseudo-code)
```
messages = [user task]
repeat up to MAX_STEPS:
    response = LLM(messages, tools)
    if response has no tool call: return its text
    for each tool call: result = run(tool, args)
    append tool results to messages
```

### Tool schema table
| Tool | Input | Purpose |
|------|-------|---------|
| calculator | expression (str) | Safe math evaluation (AST, no eval) |
| wikipedia_search | query (str) | Fetch factual summary from Wikipedia |
| get_datetime | – | Current date and time |
| save_note | title, content | Write to long-term memory |
| read_notes | – | Recall saved notes |

## Setup
```bash
git clone <your-repo-url>
cd ai-research-agent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
python agent.py
```

## Example prompts
- "Find out when the Eiffel Tower was built, compute how many years ago that was, and save a note."
- "What notes have I saved so far?"
- "Compare the populations of India and Japan on Wikipedia and calculate the ratio."

## Agentic features
- Autonomous planning and multi-step tool use
- Tool selection by the model via JSON schemas
- Observation loop with a step limit for safety
- Persistent memory (`notes.json`)
- Error handling for tool failures
