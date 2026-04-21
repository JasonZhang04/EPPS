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
        pred_dest = predicted.get(item, "").strip().lower()
        true_dest = ground_truth.get(item, "").strip().lower()
        
        if pred_dest and pred_dest == true_dest:
            correct_count += 1
            
    return (correct_count / len(novel_items)) * 100.0

def generate_conflict_resolution_matrix(results_path: str):
    # Stub for computing the conflict resolution metrics
    pass