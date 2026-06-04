"""Service functions for task operations."""

from difflib import SequenceMatcher
from typing import NamedTuple, Optional

from apps.matters.models import Matter

# Scoring thresholds for inferring a matter from a typed prefix.
_MATCH_THRESHOLD = 0.5  # minimum score to accept a match at all
_AMBIGUITY_MARGIN = 0.05  # a runner-up within this of the best => ambiguous
_FUZZY_WORD_RATIO = 0.8  # typo tolerance when comparing single words


class QuickTaskMatch(NamedTuple):
    """Outcome of resolving a quick-add description to a matter.

    status is one of:
        "resolved"  - confidently matched a single matter (in ``matter``)
        "admin"     - prefix was "admin"; intentionally no matter
        "ambiguous" - prefix matched several matters equally; not guessed
        "unmatched" - a prefix was typed but nothing matched; not guessed
        "sticky"    - no prefix typed; reused the previous task's matter
        "filter"    - no prefix and no previous matter; caller uses its filter
    """

    description: str
    matter: Optional[Matter]
    use_smart_matching: bool
    status: str
    prefix: str


def _score_name(prefix, name):
    """Score how well a typed prefix identifies a matter name (0..1).

    Prefers prefix-of-word matches over typo similarity, and earlier words
    over later ones, so "Brown" matches "Estate of Margaret Brown" and a short
    "Sm" still matches "Smith Estate". Returns 0 when nothing meaningful lines
    up.
    """
    name_l = (name or "").lower().strip()
    p = prefix.lower().strip()
    if not name_l or not p:
        return 0.0

    if name_l == p:
        return 1.0
    if name_l.startswith(p):
        return 0.9

    name_words = name_l.split()
    p_words = p.split()

    if len(p_words) == 1:
        # Prefix-of-word match against any word in the name.
        for i, word in enumerate(name_words):
            if word.startswith(p):
                # The first word is the strongest signal; later words a touch less.
                return 0.8 if i == 0 else 0.7
        # Typo tolerance against individual words. Lengths are comparable here,
        # so SequenceMatcher.ratio behaves well (unlike prefix-vs-full-name).
        best = max(
            (SequenceMatcher(None, p, w).ratio() for w in name_words),
            default=0.0,
        )
        return 0.65 if best >= _FUZZY_WORD_RATIO else 0.0

    # Multi-word prefix: every typed token should line up with a distinct word.
    used = set()
    matched = 0
    for tok in p_words:
        for i, word in enumerate(name_words):
            if i in used:
                continue
            if (
                word.startswith(tok)
                or SequenceMatcher(None, tok, word).ratio() >= _FUZZY_WORD_RATIO
            ):
                used.add(i)
                matched += 1
                break
    if matched == len(p_words):
        return 0.85
    if matched:
        return 0.4 * (matched / len(p_words))
    return 0.0


def _match_matter(prefix, matters_list):
    """Resolve a typed prefix to a single matter without guessing.

    Returns (matter, status) where status is "resolved", "ambiguous", or
    "unmatched". A near-tie between two different matters is reported as
    ambiguous rather than silently picking one.
    """
    scored = [(_score_name(prefix, name), matter) for name, matter in matters_list]
    scored = [pair for pair in scored if pair[0] >= _MATCH_THRESHOLD]
    if not scored:
        return None, "unmatched"

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score, best_matter = scored[0]

    if len(scored) > 1:
        runner_score, runner_matter = scored[1]
        if (
            runner_matter.pk != best_matter.pk
            and runner_score >= best_score - _AMBIGUITY_MARGIN
        ):
            return None, "ambiguous"

    return best_matter, "resolved"


def process_quick_task_description(description, last_matter_id=None):
    """Process a quick task description with intelligent matter matching.

    Supports two modes:
    1. Dash notation: "Matter - task description" resolves the prefix to a
       matter (or to no matter when the prefix is "admin", unrecognised, or
       ambiguous). It never falls back to the previous matter, so a typo can no
       longer silently misfile a task.
    2. No dash: reuses the previous quick task's matter ("sticky") so a run of
       tasks for the same matter can be typed without repeating its name.

    Args:
        description: The raw task description from user input.
        last_matter_id: The matter ID from the last quick task (or None).

    Returns:
        QuickTaskMatch: the cleaned description plus the matched matter and the
        status/prefix the caller can surface to the user.
    """
    description = description.strip()

    # Dash notation, e.g. "Smith Estate - review will".
    if "-" in description:
        prefix, remainder = description.split("-", 1)
        prefix = prefix.strip()
        description = remainder.strip()
        if description:
            description = description[0].upper() + description[1:]

        if prefix.lower() == "admin":
            return QuickTaskMatch(description, None, True, "admin", prefix)

        matters = Matter.objects.filter(status__in=["Pending", "Open"])
        matters_list = [(m.name, m) for m in matters]
        matched_matter, status = _match_matter(prefix, matters_list)
        return QuickTaskMatch(description, matched_matter, True, status, prefix)

    # No dash - reuse the last matter so repeated tasks stay together.
    if description:
        description = description[0].upper() + description[1:]

    if last_matter_id:
        try:
            matched_matter = Matter.objects.get(pk=last_matter_id)
            return QuickTaskMatch(description, matched_matter, True, "sticky", "")
        except Matter.DoesNotExist:
            pass

    return QuickTaskMatch(description, None, False, "filter", "")
