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
from urllib import request as _rq

from text_manager import get_text

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
# MODEL = "gemma4:e4b-it-qat"   # more accurate, but ~2x slower per call
MODEL = "gemma4:e2b"            # faster; used by every extraction agent (llm=None path)
# MODEL = "granite4.2:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"


@lru_cache(maxsize=None)
def make_llm(model: str = MODEL, num_ctx: int = 32768):
    """Build a langchain ChatOllama, cached per (model, num_ctx).

    Only for callers that pass an explicit ``llm=``. This module's own calls go
    through ollama_chat (raw HTTP to /api/chat) instead, which sends exactly the
    request we intend and hands back Ollama's done_reason/eval_count so an empty
    reply can be diagnosed rather than guessed at.
    """
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=0, format="json", num_ctx=num_ctx)


def _to_messages(prompt):
    """Accept either a plain string or a list of {role, content} dicts."""
    if isinstance(prompt, str):
        return [{"role": "user", "content": prompt}]
    if isinstance(prompt, list):
        out = []
        for m in prompt:
            if isinstance(m, dict):
                out.append({"role": m.get("role", "user"),
                            "content": str(m.get("content", ""))})
            else:
                out.append({"role": "user", "content": str(m)})
        return out
    return [{"role": "user", "content": str(prompt)}]


def ollama_chat(prompt, num_ctx: int, model: str = MODEL,
                json_format: bool = True, timeout: int = 600):
    """POST one chat completion to Ollama. Returns (content, response_dict).

    No langchain: the request that goes out is exactly the one printed by
    probe_json_mode.py, which is the request that demonstrably works.
    """
    body = {
        "model": model,
        "messages": _to_messages(prompt),
        "stream": False,
        "options": {"temperature": 0, "num_ctx": num_ctx},
    }
    if json_format:
        body["format"] = "json"
    req = _rq.Request(OLLAMA_URL, data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with _rq.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    return out.get("message", {}).get("content", "") or "", out, body



# Context sizing: pick a num_ctx just above the prompt size so small calls stay
# fast and only whole-paper calls allocate a big window. Sizes are rounded up to
# one of these buckets (cached clients are reused per bucket).
# 4096 is deliberately NOT a bucket. Measured on this model, every call sized to
# a 4096 window ran the generation to the very last token and returned nothing
# (done_reason='length', eval_count == num_ctx - prompt_eval_count, 3 times out
# of 3) — and it was not a space problem: one of those calls had 2832 tokens free
# and used all of them, then answered the SAME prompt in ~40 tokens once the
# window was 8192. The small window breaks the model's stopping behaviour rather
# than the reply being too long, so starting at 8192 costs a little KV cache and
# saves a wasted full-length generation plus a retry on every short call.
_CTX_BUCKETS = [8192, 16384, 32768, 49152, 65536]
_CTX_MAX = _CTX_BUCKETS[-1]
# Deliberately PESSIMISTIC. The two errors are not symmetric: overestimating the
# prompt costs one bucket of memory, while underestimating it wastes a whole
# generation and a retry. Prose runs ~4 chars/token but the whole-paper prompts
# are full of tables, numbers and LaTeX, which tokenize far denser — a 111k-char
# canonicalize prompt measured 3.39. At the old 3.5 that prompt was estimated at
# 31,744 tokens, landed in the 32,768 bucket, and actually needed 32,742 —
# leaving 26 tokens to reply in.
_CHARS_PER_TOKEN = 3.0
_CTX_OUTPUT_HEADROOM = 1024  # first guess at room for the JSON the model writes

# num_ctx is the TOTAL window (prompt + generation), so the headroom above has to
# cover the reply. There is no reliable way to predict that size: the SAME
# 3-column mapper prompt has answered in 165 tokens and, after the field
# descriptions grew, run away to 1549 and never closed the JSON. Estimating
# per-column budgets only moved the guess around. So the headroom is just an
# opening bid — when a reply is cut off, invoke_sized GROWS the window and
# retries, which needs no estimate to be correct.


def _text_of(prompt):
    """Length of a prompt whether it's a string or a list of chat messages."""
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        return "\n".join(str(m.get("content", "")) if isinstance(m, dict) else str(m)
                         for m in prompt)
    return str(prompt)


def ctx_size_for(prompt) -> int:
    """Smallest bucket that fits the prompt plus opening room for the reply."""
    est = int(len(_text_of(prompt)) / _CHARS_PER_TOKEN) + _CTX_OUTPUT_HEADROOM
    return next((b for b in _CTX_BUCKETS if b >= est), _CTX_MAX)


def ctx_for(prompt, model: str = MODEL):
    """Return a cached LLM whose num_ctx fits the prompt plus its reply."""
    return make_llm(model, ctx_size_for(prompt))


def invoke_sized(prompt, model: str = MODEL, retries: int = 1, max_growth: int = 2):
    """Invoke with a context sized to the prompt; returns the content string.

    An empty reply is handled by its cause, which Ollama reports in done_reason:

      'length'  The reply ran to the end of the window, so the JSON never closed
                and Ollama hands back no content at all. Retrying at the SAME
                num_ctx is pointless — temperature 0 replays the identical
                generation — but the next bucket up is a different request that
                can finish, so grow the window and retry. Bounded by max_growth
                so a model that never terminates cannot walk up to a 65536-token
                window and burn the run.
      'load'    Ollama answered a model load with no content. Transient; retry.
      other     Retry once, then give up.
    """
    num_ctx = ctx_size_for(prompt)
    content, tries, grown = "", 0, 0
    while True:
        content, out, _ = ollama_chat(prompt, num_ctx, model)
        if content.strip():
            if grown or tries:
                print(f"  [llm] recovered ({len(content)} chars, num_ctx={num_ctx})")
            return content

        done = out.get("done_reason")
        print(f"  [llm] empty reply  num_ctx={num_ctx} done_reason={done!r} "
              f"prompt_tokens={out.get('prompt_eval_count')} "
              f"generated={out.get('eval_count')}")

        if done == "length":
            # Ollama just told us the TRUE prompt size, so stop guessing: jump
            # straight to a bucket that fits that prompt plus real room to reply,
            # instead of stepping one bucket at a time and re-paying for a
            # 30k-token prompt evaluation on each hop.
            ptok = out.get("prompt_eval_count") or 0
            gen = out.get("eval_count") or 0
            need = ptok + max(_CTX_OUTPUT_HEADROOM, 2 * gen)
            nxt = next((b for b in _CTX_BUCKETS if b > num_ctx and b >= need),
                       next((b for b in _CTX_BUCKETS if b > num_ctx), None))
            if nxt is None or grown >= max_growth:
                print(f"        -> reply still cut off at num_ctx={num_ctx}; giving up. "
                      f"The prompt ({ptok} tokens) is too big for this model.")
                return content
            print(f"        -> prompt was {ptok} tokens, leaving {num_ctx - ptok} "
                  f"to reply in; growing num_ctx {num_ctx} -> {nxt}")
            num_ctx, grown = nxt, grown + 1
            continue

        tries += 1
        if tries > retries:
            return content
        print("        -> retrying")


def _describe(content) -> str:
    """A short, honest description of a response that would not parse. Printed on
    failure because 'Expecting value: line 1 column 1 (char 0)' is the same error
    for an empty reply, a markdown fence and a prose preamble, and you cannot fix
    what you cannot see."""
    if content is None:
        return "<None>"
    if content == "":
        return "<empty string — model returned nothing>"
    if not str(content).strip():
        return f"<whitespace only, {len(content)} char(s)>"
    head = str(content)[:300].replace("\n", "\\n")
    return f"{len(content)} char(s), starts: {head!r}"


def loads_salvaging(content: str) -> dict:
    """json.loads, but tolerant of the three ways a local model breaks JSON mode.

    1. EMPTY / whitespace reply           -> raises, having printed what came back
    2. FENCED or prose-prefixed JSON      -> the object is found and extracted
    3. TRUNCATED mid-value                -> the complete keys are recovered

    For (3): a response cut off mid-value is valid JSON right up to the last
    completed key, so walk back to the last comma at brace-depth 1 and close the
    object there. Anything genuinely malformed still raises, so a real bug does
    not get silently swallowed into an empty mapping."""
    if content is None or not str(content).strip():
        print(f"  [json] unparseable response: {_describe(content)}")
        raise json.JSONDecodeError("empty response from model", str(content or ""), 0)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # strip ```json fences / any preamble before the first brace
    start = content.find("{")
    if start == -1:
        print(f"  [json] no JSON object in response: {_describe(content)}")
        raise json.JSONDecodeError("no JSON object in response", content, 0)
    if start > 0:
        print(f"  [json] stripped {start} char(s) of preamble before the object")
    content = content[start:]
    end = content.rfind("```")
    if end > 0:
        content = content[:end]

    try:
        return json.loads(content)
    except json.JSONDecodeError as first_error:
        depth, in_str, esc, cut = 0, False, False, None
        for i, ch in enumerate(content):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
            elif ch == "," and depth == 1:
                cut = i
        if cut is None:
            print(f"  [json] unsalvageable response: {_describe(content)}")
            raise first_error
        try:
            out = json.loads(content[:cut] + "}")
        except json.JSONDecodeError:
            print(f"  [json] unsalvageable response: {_describe(content)}")
            raise first_error
        if not isinstance(out, dict):
            print(f"  [json] response was not an object: {_describe(content)}")
            raise first_error
        print(f"  [salvage] truncated JSON — kept {len(out)} complete key(s)")
        return out


def _template_def(field: str) -> str:
    """The canonical definition of one template field, read from
    template_descriptions/<field>.md — the SAME text the table mapper injects, so
    the two agents share one source of truth and cannot drift."""
    p = TEMPLATE_DIR / f"{field}.md"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


# What COUNTS as a trait (a measurementType) — organism vs site, the wide-table
# rule, the environment/abundance/taxonomic-rank exclusions — lives once in
# template_descriptions/measurementType.md and is pulled in here. This module adds
# ONLY the relevance-specific CATEGORY labels the model must choose among; edit the
# definition in the .md, not here.
COLUMN_CATEGORIES = f"""
The single test is whether a column is a measurementType — a trait of the
organism. Here is its definition, INCLUDING everything that does NOT qualify:

<measurementType definition>
{_template_def("measurementType")}
</measurementType definition>

A column that qualifies gets ONE of these category labels:
- "Categorical biological trait" — a discrete named state of the organism's
  biology/ecology/behaviour (colour, pattern, sociality, caste, activity mode,
  feeding guild, nesting type, the habitat class it occupies).
- "Morphological measurement" — a measured physical/anatomical dimension of the
  organism (body length, head width, wing length, tongue length, body mass).
- "Behavioral observation" — a recorded behaviour of the organism, or how/where it
  was observed behaving.
- "Trait-name column" — a column whose CELLS are literally the NAMES of traits
  (values like "body mass", "head length", "wingspan"), paired with a SEPARATE
  values column in the same table. Use ONLY when the cells are trait names AND
  another column holds the numbers — never for a numeric or coded data column.
"""


def column_relevance_msg_builder_all(columns, text, samples=None):
    samples = samples or {}
    # Show the model what each column actually CONTAINS. A column's own name and a
    # few of its cell values are the primary evidence for what it records; the
    # prose is only supporting context. Papers routinely ship traits in a data
    # table (often a supplement) without ever discussing them in the body, so a
    # trait column must not be rejected merely for being absent from the text.
    col_lines = []
    for c in columns:
        vals = samples.get(c) or []
        if vals:
            shown = ", ".join(repr(v) for v in vals[:6])
            col_lines.append(f'- "{c}"  (example values: {shown})')
        else:
            col_lines.append(f'- "{c}"')
    col_block = "\n".join(col_lines)

    system = f"""You analyze scientific papers and decide whether each table column
records data worth keeping in a biological database.

{COLUMN_CATEGORIES}

For EACH column, judge it by its own name and example values (the paper text is
only context — a real trait need not be mentioned in the prose). Work in this
order against the definition above:

1. FIRST look for a reason the column does NOT concur with the definition — one of
   the cases its "NOT a measurementType" list names:
     - a place / locality, or where the study worked (site, plot, transect);
     - a site condition: temperature, precipitation, wind, degree-days, elevation,
       distance to X, % sealed area, plant richness;
     - a human/socioeconomic or land-use variable of the site: income, population
       density, management, urbanisation;
     - an abundance or sample size: density, counts, n;
     - a statistic or derived index: SD, CV, p-value, a correlation or genetic-
       differentiation index (Gst, Dst, Fst), a diversity index, a principal-
       component score (PC1, PC2);
     - a sampling method; a taxonomic rank (Family, Genus, ...) or authorship.
   If one applies, set "category" to null and make "reasoning" that specific reason
   (e.g. "site climate variable", "genetic-differentiation index", "PC score",
   "taxonomic rank", "sampling statistic").
2. ONLY if no exclusion applies does the column qualify — then give it the fitting
   category from the list, with a one-line reason.

A number with a unit is NOT automatically a trait: a site temperature, a wind
speed, a distance, a p-value and a genetic index all carry numbers, and each
matches an exclusion above. When you cannot point to a concrete reason the column
qualifies, prefer null — in a wide dataset most columns are not traits.

The columns being evaluated are:
{col_block}

Return a JSON object keyed by column name, with this format:
{{
    "<column1>": {{
        "category": "<one of the categories, or null if not relevant>",
        "reasoning": "<brief explanation from the column's name/values, and text if useful>"
    }},
    "<column2>": {{ ... }}
}}

Keep the reasoning to AT MOST 15 words.
Return null for any column that is not a measurementType per the definition above."""
    user = f"Here is the paper text for context:\n{text}"
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]


def agent_define_columns_relevance(columns, paper_text, llm=None, samples=None):
    """Run relevance for ALL columns in one pass, then (if chunked) judge.
    If no llm is supplied, context is sized to each prompt automatically.

    `samples`: optional {column: [example cell values]} so the model can judge a
    column by its contents, not only its name and the prose."""
    chunks = get_text(paper_text, len(paper_text))
    merged = "\n\n".join(c["content"] for c in chunks)
    chunks = [{"content": merged}]

    per_column = {col: [] for col in columns}
    for chunk in chunks:
        messages = column_relevance_msg_builder_all(columns, chunk["content"],
                                                    samples=samples)
        try:
            content = (llm.invoke(messages).content if llm else
                       invoke_sized(messages))
            parsed = loads_salvaging(content)
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

Combine all chunk results. The strongest positive evidence wins. A column is
relevant if it is a biological trait/measurement/observation judged by its name
and values — it does NOT need to be discussed in the prose, since traits are
often recorded in a data table without being mentioned in the body. Only reject
a column that is a statistic, count, identifier, or citation.

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