import re
from typing import Dict, List

def calculate_pfs(predicted: Dict[str, str], ground_truth: Dict[str, str], novel_items: List[str]) -> float:
    """
    Computes Pragmatic Faithfulness Score (PFS)
    PFS = (1 / |N|) * Sum(pred == true) * 100
    """
    if not novel_items:
        return 0.0
        
    correct_count = 0
    for item in novel_items:
        # Safely get the strings and convert to lowercase
        pred_dest = predicted.get(item, "").strip().lower()
        true_dest = ground_truth.get(item, "").strip().lower()
        
        # 1. Regex Cleanup: Strip common topological prefixes LLMs like to add
        pred_dest_cleaned = re.sub(r'^(on|inside|in|under|next to|near)\s+', '', pred_dest).strip()
        
        # 2. Substring Fallback: Replace underscores to handle 'bathroom_cabinet' vs 'bathroom cabinet'
        true_dest_normalized = true_dest.replace("_", " ")
        pred_dest_normalized = pred_dest_cleaned.replace("_", " ")
        
        # Evaluate: Direct match OR true destination is contained within the prediction
        if pred_dest_cleaned == true_dest or true_dest_normalized in pred_dest_normalized:
            correct_count += 1
            
    return (correct_count / len(novel_items)) * 100.0

def generate_conflict_resolution_matrix(results_path: str):
    # Stub for computing the conflict resolution metrics
    pass