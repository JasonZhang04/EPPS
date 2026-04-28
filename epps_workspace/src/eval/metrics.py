from typing import Dict, List

# ---------------------------------------------------------------------------
# DESTINATION SYNONYM MAP
#
# Maps canonical VirtualHome furniture names to alternative terms a language
# model might predict. Only genuine semantic equivalents *in this environment*
# are included. Exclusions are deliberate:
#
#   "table" is NOT a synonym for "kitchen_table" — too ambiguous (could mean
#     desk, dining table, coffee table, etc.). Models should learn the full name.
#
#   "cabinet" is NOT a synonym for either "closet" or "bathroom_cabinet" —
#     it maps to two different furniture items in different rooms, so accepting
#     it as correct would mask a real confusion.
#
#   "closet" is NOT a synonym for "bathroom_cabinet" — they are in different
#     rooms with different purposes. The persona's preference for one vs. the
#     other is meaningful and should be measured.
#
#   "desk" is NOT a synonym for any table — desk (bedroom workspace) and
#     kitchen_table (dining/entry area) carry completely different persona
#     signals. Confusing them would hide a substantive placement error.
# ---------------------------------------------------------------------------

DESTINATION_SYNONYMS: Dict[str, List[str]] = {
    # bedroom closet — "wardrobe" is an exact real-world synonym
    "closet": ["wardrobe", "clothes_closet", "bedroom_closet"],

    # kitchen appliance — "refrigerator" is the formal name, "fridge" the colloquial
    "fridge": ["refrigerator", "refrigerator_freezer", "cooler"],

    # bathroom storage — medicine cabinet / vanity all refer to the same unit
    "bathroom_cabinet": ["medicine_cabinet", "bathroom_shelf", "vanity_cabinet", "vanity"],

    # living room seating — couch and sofa are interchangeable everywhere
    "sofa": ["couch", "loveseat", "couch_sofa"],

    # bedroom shelving — bookcase and shelf are the same piece of furniture here
    "bookshelf": ["bookcase", "shelf", "bookshelves", "shelves", "book_shelf"],

    # dining/entry table — only accept explicit compound names, not bare "table"
    "kitchen_table": ["dining_table", "kitchen_counter", "counter_top"],

    # bedroom work surface — only formal variants, not bare "table"
    "desk": ["work_desk", "study_desk", "writing_desk"],

    # kitchen fixture
    "sink": ["kitchen_sink", "basin"],
}

# Build reverse lookup at import time: synonym → canonical name.
# Canonical names are also included so _resolve_synonym is safe for any input.
_SYNONYM_TO_CANONICAL: Dict[str, str] = {
    synonym: canonical
    for canonical, synonyms in DESTINATION_SYNONYMS.items()
    for synonym in synonyms
}
_SYNONYM_TO_CANONICAL.update({k: k for k in DESTINATION_SYNONYMS})  # identity for canonicals


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _normalize_destination(dest: str) -> str:
    """
    Strip relational prefix (ON / INSIDE / etc.) and lowercase.

    Handles two common failure modes:
    1. RagHistory copies the diff format verbatim: "ON desk", "INSIDE closet".
    2. Models add the relation word: "on the desk", "inside the closet".
    """
    dest = dest.strip().lower()
    # Remove leading article if present ("on the desk" -> "on desk")
    dest = dest.replace(" the ", " ")
    for prefix in ("on ", "inside ", "held_by ", "on_floor_in "):
        if dest.startswith(prefix):
            dest = dest[len(prefix):].strip()
            break
    return dest


def _resolve_synonym(dest: str) -> str:
    """Map a synonym to its canonical furniture name; return unchanged if unknown."""
    return _SYNONYM_TO_CANONICAL.get(dest, dest)


# ---------------------------------------------------------------------------
# PFS CALCULATION
# ---------------------------------------------------------------------------

def calculate_pfs(
    predicted: Dict[str, str],
    ground_truth: Dict[str, str],
    novel_items: List[str],
    use_synonyms: bool = False,
) -> float:
    """
    Pragmatic Faithfulness Score (PFS).

    PFS = (correct_items / total_novel_items) x 100

    Args:
        use_synonyms: If False (default), exact canonical match required.
            If True, synonymous furniture names (e.g. wardrobe == closet)
            count as correct. Use the relaxed version for secondary reporting;
            use the strict version as the primary metric in the paper.

    Normalization applied regardless of use_synonyms:
    - Strips relational prefixes: "ON desk" -> "desk"
    - Strips leading articles: "on the desk" -> "desk"
    - Lowercases and trims whitespace

    With use_synonyms=True, also maps synonyms to canonical names:
    - "wardrobe" -> "closet", "refrigerator" -> "fridge", etc.
    """
    if not novel_items:
        return 0.0

    correct_count = 0
    for item in novel_items:
        pred = _normalize_destination(predicted.get(item, ""))
        true = _normalize_destination(ground_truth.get(item, ""))

        if use_synonyms:
            pred = _resolve_synonym(pred)
            true = _resolve_synonym(true)

        if pred and pred == true:
            correct_count += 1

    return (correct_count / len(novel_items)) * 100.0


def generate_conflict_resolution_matrix(results_path: str):
    # Stub for computing conflict resolution metrics
    pass
