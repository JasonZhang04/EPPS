import json
import os
import traceback
from typing import Dict, Any

from src.api.thinking_machine import ThinkingMachineClient
from src.core_epps.epps_agent import EPPSAgent
from src.baselines.zero_shot_agent import ZeroShotAgent
from src.baselines.rag_history_agent import RagHistoryAgent
from src.baselines.naive_summary_agent import NaiveSummaryAgent
from src.eval.metrics import calculate_pfs

def run_evaluation(dataset_path: str = "data/eval_dataset.json"):
    print(f"Loading dataset from {dataset_path}...")
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return
        
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    api_client = ThinkingMachineClient()
    
    results = {
        "ZeroShot": [],
        "RagHistory": [],
        "NaiveSummary": [],
        "EPPS": []
    }
    
    zero_shot = ZeroShotAgent(api_client)
    rag_history = RagHistoryAgent(api_client)
    naive_summary = NaiveSummaryAgent(api_client)

    for i, task in enumerate(dataset):
        persona = task['persona']
        history_log = task['history_log']
        correction_log = task['human_correction_log']
        novel_items = task['novel_items']
        ground_truth = task['ground_truth_destinations']
        
        instruction = f"Tidy up the room according to my {persona} habits."
        
        print(f"\n--- Evaluating Task {i+1}/{len(dataset)} | Persona: {persona} ---")
        
        try:
            # Baseline 1
            zs_pred = zero_shot.predict(instruction, novel_items, history_log)
            results["ZeroShot"].append({"persona": persona, "pfs": calculate_pfs(zs_pred, ground_truth, novel_items)})
            
            # Baseline 2
            rag_pred = rag_history.predict(instruction, novel_items, history_log)
            results["RagHistory"].append({"persona": persona, "pfs": calculate_pfs(rag_pred, ground_truth, novel_items)})
            
            # Baseline 3
            ns_pred = naive_summary.predict(instruction, novel_items, history_log)
            results["NaiveSummary"].append({"persona": persona, "pfs": calculate_pfs(ns_pred, ground_truth, novel_items)})
            
            # EPPS
            epps_agent = EPPSAgent(user_id=f"user_{i}", api_client=api_client)
            epps_agent.observe_background(history_log)
            epps_agent.receive_feedback(correction_log)
            epps_pred = epps_agent.plan_execution(instruction, novel_items)
            results["EPPS"].append({"persona": persona, "pfs": calculate_pfs(epps_pred, ground_truth, novel_items)})

        except Exception as e:
            print(f"Task {i+1} failed due to: {e}")
            traceback.print_exc()

    # Save results
    os.makedirs("data", exist_ok=True)
    with open("data/eval_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("Evaluation complete. Results saved to data/eval_results.json")

if __name__ == "__main__":
    run_evaluation()
