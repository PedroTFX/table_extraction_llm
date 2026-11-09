"""Two options at a time (v11): a question with many options splits nimble's probability
(Luo2023 t4: the right species 0.58-0.69 against three others, never sure), so the options
meet in pairs until one is left, and that one then meets 'none' in its own question
(output/eval_split/DESIGN_names_v11.md). Code only orders the options and keeps the sure
answers; anything not sure stops the duels and changes nothing.
"""
import column_tree as ct
import decoder as v1

SURE = 0.8


class Nimble:
    """v1.ask on a decision client loaded at the first question (a paper with nothing to ask
    loads no model)."""

    def __init__(self):
        self.client = None

    def get(self):
        self.client = self.client or ct.DecisionClient(v1.NIMBLE, 1)
        return self.client

    def __call__(self, state, question, crit):
        return v1.ask(self.get(), state, question, crit)

    def unload(self):
        if self.client:
            v1.unload(v1.NIMBLE)
            self.client = None


def duel(ask, state, question, options):
    """options [(label, option text)] in the order code gives them: the first two, then the one
    kept against the next. A sure answer (p >= SURE) keeps one; anything less stops: (None, log).
    The one kept sits second on every other duel, so a lean towards the first option cannot keep
    it. -> (index of the one left, log); a single option is left without a question."""
    log, held = [], 0
    for i in range(1, len(options)):
        a, b = (held, i) if i % 2 else (i, held)
        ch, probs = ask(state, question, {"a": options[a][1], "b": options[b][1]})
        log.append({"a": options[a][0], "b": options[b][0], "choice": ch, "probs": probs})
        if ch not in ("a", "b") or probs.get(ch, 0) < SURE:
            return None, log
        held = a if ch == "a" else b
    return (held if options else None), log


def sure(ch, probs, *keys):
    """The answer when it is one of `keys` and sure, else None."""
    return ch if ch in keys and probs.get(ch, 0) >= SURE else None
