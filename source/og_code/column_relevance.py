"""
column_relevance.py — decide, per table column, whether it records data worth
keeping in the biological database.

Refactor notes
--------------
* No LLM is created at import time. ``make_llm`` builds one on demand and is
  shared by callers, so importing this module (e.g. from table_to_data) is cheap
  and works even where Ollama isn't installed — only *calling* the agents needs it.
* Template descriptions are read from ./templates relative to this file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from text_manager import get_text

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
MODEL = "gemma4:e2b"
# MODEL = "gemma4:e4b-it-qat"


@lru_cache(maxsize=None)
def make_llm(model: str = MODEL, num_ctx: int = 32768):
    """Lazily import langchain_ollama and build a JSON-mode chat model.
    Cached per (model, num_ctx) so clients are reused across calls."""
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=0, format="json", num_ctx=num_ctx)


# Context sizing: pick a num_ctx just above the prompt size so small calls stay
# fast and only whole-paper calls allocate a big window. Sizes are rounded up to
# one of these buckets (cached clients are reused per bucket).
_CTX_BUCKETS = [4096, 8192, 16384, 32768, 49152, 65536]
_CTX_MAX = _CTX_BUCKETS[-1]
_CHARS_PER_TOKEN = 3.5      # rough; English prose ~4, tables/numbers denser
_CTX_OUTPUT_HEADROOM = 1024  # leave room for the JSON the model writes back


def _text_of(prompt):
    """Length of a prompt whether it's a string or a list of chat messages."""
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        return "\n".join(str(m.get("content", "")) if isinstance(m, dict) else str(m)
                         for m in prompt)
    return str(prompt)


def ctx_for(prompt, model: str = MODEL):
    """Return a cached LLM whose num_ctx is the smallest bucket that fits the
    prompt (plus output headroom), capped at _CTX_MAX."""
    est = int(len(_text_of(prompt)) / _CHARS_PER_TOKEN) + _CTX_OUTPUT_HEADROOM
    num_ctx = next((b for b in _CTX_BUCKETS if b >= est), _CTX_MAX)
    return make_llm(model, num_ctx)


def invoke_sized(prompt, model: str = MODEL):
    """Invoke with a context sized to the prompt; returns the .content string."""
    return ctx_for(prompt, model).invoke(prompt).content


COLUMN_CATEGORIES = """
Valid categories for a worth-recording column:
- "Categorical biological trait" — discrete classifications of the organism's biology
- "Morphological measurement" — physical/anatomical measurements
- "Behavioral observation" — recorded behaviors or where/how the organism was observed

If the column does not fit any of these categories, return null.
Examples that do NOT fit: percentages of occurrence, sample sizes (n=, N=),
p-values, statistical indices, citations, identifiers.
"""


def column_relevance_msg_builder_all(columns, text):
    system = f"""You analyze scientific papers and decide whether each table column
records data worth keeping in a biological database.

{COLUMN_CATEGORIES}

The columns being evaluated are: {columns}

Your task: read the text and decide, for each column, whether it fits one of
the valid categories based on what the paper says about it.

Return a JSON object keyed by column name, with this format:
{{
    "<column1>": {{
        "category": "<one of the categories, or null if not relevant>",
        "reasoning": "<brief explanation based on the text>"
    }},
    "<column2>": {{ ... }}
}}

Keep the reasoning concise but informative, focused on textual evidence.
If the text does not mention a column, return null for category and say
"not present in text"."""
    user = f"Here is the text:\n{text}"
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


def agent_define_columns_relevance(columns, paper_text, llm=None):
    """Run relevance for ALL columns in one pass, then (if chunked) judge.
    If no llm is supplied, context is sized to each prompt automatically."""
    chunks = get_text(paper_text, len(paper_text))
    merged = "\n\n".join(c["content"] for c in chunks)
    chunks = [{"content": merged}]

    per_column = {col: [] for col in columns}
    for chunk in chunks:
        messages = column_relevance_msg_builder_all(columns, chunk["content"])
        try:
            content = llm.invoke(messages).content if llm else invoke_sized(messages)
            parsed = json.loads(content)
        except json.JSONDecodeError:
            print("Skipping malformed chunk response")
            continue
        for col in columns:
            if col in parsed and isinstance(parsed[col], dict):
                per_column[col].append(parsed[col])

    if len(chunks) == 1:
        return {
            col: (per_column[col][0] if per_column[col]
                  else {"category": None, "reasoning": "not found in text"})
            for col in columns
        }

    final = {}
    for col in columns:
        judge_prompt = f"""The following JSON objects are per-chunk evaluations of whether
the column "{col}" represents data worth recording in a biological database.

{COLUMN_CATEGORIES}

Combine all chunk results. The strongest positive evidence wins.
A column is relevant if any chunk found genuine evidence that the paper records
this data per species/specimen. Generic background mentions do NOT count, and
citations to other studies should be ignored.

Return a JSON object:
{{
    "column": "{col}",
    "category": "<one of the categories, or null if not relevant>",
    "reasoning": "<consolidated explanation>"
}}

Per-chunk results:
{json.dumps(per_column[col], indent=2)}"""
        final[col] = json.loads(invoke_sized([{"role": "system", "content": judge_prompt}]))
        print(f"  {col} -> {final[col].get('category')}")
    return final