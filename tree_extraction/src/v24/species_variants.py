"""New examples for the species tree's READ prompt (species_tree.py; the user, 2026-11-18: prompts must not carry
the dataset). The prompt's examples came from the papers: 'V. maculifrons' (Kovacs2008, Kovacs2010, Orr2024: the
single-species papers this step was built on), and the group names 'beetles' (79 papers), 'wild bees' (34) and
'Bombus spp.' (10).

Only the examples change, each keeping what it teaches (an abbreviated name; group names: a common group, another
common group, a genus with 'spp.'), with made-up names ('Velora', as in the column tree) and groups of other
organisms. Every new phrase was checked against the 271 papers (109, grit, Jakub): none prints it.

Adopted 2026-11-18 (the user): species_tree.py now carries these examples (species_ab SCORE.txt, tuning: one-species
tables right 36/37 as before; tables wrongly named in several-species papers 3 -> 0, Kratschmer2019 'honey bees').
"""
import species_tree as sp

PAIRS = [("not an abbreviation such as 'V. maculifrons' when", "not an abbreviation such as 'V. brevis' when"),
         ("(such as 'beetles', 'wild bees', 'Bombus spp.', a family or an order)",
          "(such as 'sea anemones', 'freshwater mussels', 'Velora spp.', a family or an order)")]


def _swap(text, pairs):
    """Old examples replaced by new; a prompt that already carries the new ones (adopted) is kept."""
    for old, new in pairs:
        if text.count(new) == 1 and old not in text:
            continue
        assert text.count(old) == 1, f"example not found once: {old[:60]}"
        text = text.replace(old, new)
    return text


READ = _swap(sp.READ, PAIRS)
VARIANTS = {"read": {"READ": READ}}
EXAMPLES = ["V. brevis", "Velora brevis", "sea anemones", "freshwater mussels", "Velora spp."]
