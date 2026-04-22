import json
import os
import traceback
from typing import Dict, Any

from src.api.thinking_machine import ThinkingMachineClient
from src.core_epps.epps_agent import EPPSAgent
from src.baselines.zero_shot_agent import ZeroShotAgent
from src.baselines.rag_history_agent import RagHistoryAgent
from src.baselines.naive_summary_agent import NaiveSummaryAgent
from metrics import calculate_pfs

def run_evaluation(dataset_path: str = "eval_dataset.json"):
    # Fallback to data folder if not in root
    if not os.path.exists(dataset_path):
        dataset_path = "data/eval_dataset.json"
        
    print(f"Loading dataset from {dataset_path}...")
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Please check your path.")
        return
        
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    api_client = ThinkingMachineClient()
    
    # 1. GROUP THE FLAT DATASET BY PERSONA (For Lifelong Learning)
    tasks_by_persona = {}
    for task in dataset:
        p = task['persona']
        if p not in tasks_by_persona:
            tasks_by_persona[p] = []
        tasks_by_persona[p].append(task)
        
    # We will log EVERYTHING here for qualitative debugging
    results = {
        "ZeroShot": [],
        "RagHistory": [],
        "NaiveSummary": [],
        "EPPS": []
    }
    
    # 2. RUN MULTI-TURN LIFELONG LEARNING PER PERSONA
    for persona, turns in tasks_by_persona.items():
        print(f"\n==================================================")
        print(f"Starting Lifelong Learning Simulation for: {persona}")
        print(f"==================================================")
        
        # INITIALIZE AGENTS ONLY ONCE PER PERSONA (This preserves memory!)
        epps_agent = EPPSAgent(user_id=f"{persona}_user", api_client=api_client)
        rag_history = RagHistoryAgent(api_client)
        naive_summary = NaiveSummaryAgent(api_client)
        zero_shot = ZeroShotAgent(api_client) # Zero-shot has no memory anyway

        # 3. ITERATE THROUGH THE TASKS AS CHRONOLOGICAL "TURNS"
        for turn_index, turn_data in enumerate(turns):
            print(f"\n--- {persona} | Turn {turn_index + 1}/{len(turns)} ---")
            
            history_log = turn_data['history_log']
            correction_log = turn_data['human_correction_log']
            novel_items = turn_data['novel_items']
            ground_truth = turn_data['ground_truth_destinations']
            instruction = f"Tidy up the room according to my {persona} habits."

            try:
                # --- A. UPDATE MEMORIES (LAYER 1) ---
                epps_agent.observe_background(history_log)
                rag_history.update_memory(history_log)
                naive_summary.update_memory(history_log)

                # --- B. PLAN EXECUTION ---
                zs_pred = zero_shot.predict(instruction, novel_items, history_log)
                rag_pred = rag_history.predict(instruction, novel_items)
                ns_pred = naive_summary.predict(instruction, novel_items)
                epps_pred = epps_agent.plan_execution(instruction, novel_items)

                # --- C. SCORE AND RECORD (FORENSIC LOGGING) ---
                results["ZeroShot"].append({
                    "persona": persona, 
                    "turn": turn_index + 1, 
                    "prediction": zs_pred, 
                    "ground_truth": ground_truth,
                    "pfs": calculate_pfs(zs_pred, ground_truth, novel_items)
                })
                results["RagHistory"].append({
                    "persona": persona, 
                    "turn": turn_index + 1, 
                    "prediction": rag_pred, 
                    "ground_truth": ground_truth,
                    "pfs": calculate_pfs(rag_pred, ground_truth, novel_items)
                })
                results["NaiveSummary"].append({
                    "persona": persona, 
                    "turn": turn_index + 1, 
                    "prediction": ns_pred, 
                    "ground_truth": ground_truth,
                    "pfs": calculate_pfs(ns_pred, ground_truth, novel_items)
                })
                results["EPPS"].append({
                    "persona": persona, 
                    "turn": turn_index + 1, 
                    "prediction": epps_pred, 
                    "ground_truth": ground_truth,
                    "pfs": calculate_pfs(epps_pred, ground_truth, novel_items),
                    # Log the exact snapshot of the brain for debugging!
                    "cgm_snapshot": epps_agent.cgm_state.model_dump() if epps_agent.cgm_state else {}
                })

                # --- D. IMPLICIT FEEDBACK (LAYER 2) ---
                # Apply the correction AFTER execution to prepare the agent for the NEXT turn
                epps_agent.receive_feedback(correction_log)

            except Exception as e:
                print(f"Turn {turn_index + 1} failed due to: {e}")
                traceback.print_exc()

    # Save results
    os.makedirs("data", exist_ok=True)
    with open("data/eval_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("\nEvaluation complete. Results saved to data/eval_results.json")

if __name__ == "__main__":
    # If the file is in your root directory, it will find it. If it's in data/, it will fall back to it.
    run_evaluation("eval_dataset.json")