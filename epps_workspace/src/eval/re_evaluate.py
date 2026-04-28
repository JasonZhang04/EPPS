import json
import os
from metrics import calculate_pfs

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
        
    print("\nRecalculating scores using updated regex metric...")
    
    # Iterate through all baseline and EPPS models in the results
    for model_name, turns in results.items():
        for turn_data in turns:
            prediction = turn_data.get("prediction", {})
            ground_truth = turn_data.get("ground_truth", {})
            
            # The novel items are simply the items listed in the ground truth
            novel_items = list(ground_truth.keys())
            
            # Recalculate using the robust metric
            new_pfs = calculate_pfs(prediction, ground_truth, novel_items)
            
            # Update the score in the dictionary
            turn_data["pfs"] = new_pfs

    # Save the updated results to a new file so you don't lose the original
    output_path = "data/eval_results_recalculated.json"
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"\nRe-evaluation complete! Updated results safely saved to {output_path}")

if __name__ == "__main__":
    # Point this to wherever your generated results live
    reevaluate_pfs("eval_results.json")