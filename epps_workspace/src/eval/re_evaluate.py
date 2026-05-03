import json
import os
from typing import Dict, List

# ---------------------------------------------------------------------------
# DESTINATION SYNONYM MAP
# ---------------------------------------------------------------------------

DESTINATION_SYNONYMS: Dict[str, List[str]] = {
    "closet": ["wardrobe", "clothes_closet", "bedroom_closet"],
    "fridge": ["refrigerator", "refrigerator_freezer", "cooler"],
    "bathroom_cabinet": ["medicine_cabinet", "bathroom_shelf", "vanity_cabinet", "vanity"],
    "sofa": ["couch", "loveseat", "couch_sofa"],
    "bookshelf": ["bookcase", "shelf", "bookshelves", "shelves", "book_shelf"],
    "kitchen_table": ["dining_table", "kitchen_counter", "counter_top"],
    "desk": ["work_desk", "study_desk", "writing_desk"],
    "sink": ["kitchen_sink", "basin"],
}

_SYNONYM_TO_CANONICAL: Dict[str, str] = {
    synonym: canonical
    for canonical, synonyms in DESTINATION_SYNONYMS.items()
    for synonym in synonyms
}
_SYNONYM_TO_CANONICAL.update({k: k for k in DESTINATION_SYNONYMS})


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _normalize_destination(dest: str) -> str:
    """
    Strip relational prefix (ON / INSIDE / etc.), handle spaces/underscores, and lowercase.
    """
    dest = dest.strip().lower()
    
    # 1. Remove leading articles safely
    if dest.startswith("the "):
        dest = dest[4:]
    dest = dest.replace(" the ", " ")

    # 2. Strip relational prefixes (handling BOTH space and underscore formats)
    prefixes_to_strip = (
        "on ", "on_", 
        "inside ", "inside_", 
        "held_by ", "held_by_", "held by ",
        "on_floor_in ", "on_floor_in_", "on floor in "
    )
    
    for prefix in prefixes_to_strip:
        if dest.startswith(prefix):
            # Slice off the prefix and strip any residual whitespace
            dest = dest[len(prefix):].strip()
            break
            
    # 3. Standardize: Convert all spaces to underscores to match VirtualHome canonical names
    dest = dest.replace(" ", "_")
    
    # 4. Clean up any accidental double underscores from the replacement
    while "__" in dest:
        dest = dest.replace("__", "_")
        
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

        # REVISED: Substring check to capture descriptive answers (e.g., 'vanity' in 'bathroom_vanity_drawer')
        if pred and true in pred:
            correct_count += 1

    return (correct_count / len(novel_items)) * 100.0


def generate_conflict_resolution_matrix(results_path: str):
    # Stub for computing conflict resolution metrics
    pass


# ---------------------------------------------------------------------------
# RE-EVALUATION SCRIPT
# ---------------------------------------------------------------------------

def reevaluate_pfs(results_path: str = "eval_results.json"):
    # Fallback to data folder if not in root
    if not os.path.exists(results_path):
        results_path = "data/eval_results.json"
        
    print(f"Loading existing results from {results_path}...")
    if not os.path.exists(results_path):
        print(f"Results not found at {results_path}. Please check your path.")
        return
        
    with open(results_path, "r") as f:
        results = json.load(f)
        
    print("\nRecalculating scores using updated regex and substring metrics...")
    
    # Iterate through all baseline and EPPS models in the results
    for model_name, turns in results.items():
        for turn_data in turns:
            prediction = turn_data.get("prediction", {})
            ground_truth = turn_data.get("ground_truth", {})
            
            # The novel items are simply the items listed in the ground truth
            novel_items = list(ground_truth.keys())
            
            # Recalculate using the robust metric
            strict_pfs = calculate_pfs(prediction, ground_truth, novel_items, use_synonyms=False)
            relaxed_pfs = calculate_pfs(prediction, ground_truth, novel_items, use_synonyms=True)
            
            # Update the scores in the dictionary
            turn_data["pfs"] = strict_pfs
            turn_data["pfs_relaxed"] = relaxed_pfs

    # Save the updated results to a new file so you don't lose the original
    output_path = results_path.replace(".json", "_reevaluated.json")
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"\nRe-evaluation complete! Updated results safely saved to {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="data/eval_results.json", help="Path to the JSON results file to re-evaluate.")
    args = parser.parse_args()
    
    reevaluate_pfs(args.path)