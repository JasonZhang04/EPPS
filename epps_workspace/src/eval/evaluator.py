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

def run_evaluation(dataset_path: str = "eval_dataset.json", persona_filter: str = None, max_turns: int = None):
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
    
    # ==========================================
    # 1. PROPERLY LOAD EXISTING RESULTS FIRST
    # ==========================================
    os.makedirs("data", exist_ok=True)
    results_path = "data/eval_results.json"
    
    # Initialize the results container
    results = {
        "ZeroShot": [],
        "RagHistory": [],
        "NaiveSummary": [],
        "EPPS": []
    }
    
    if os.path.exists(results_path):
        print(f"Found existing results at {results_path}. Loading to resume...")
        try:
            with open(results_path, "r") as f:
                existing_data = json.load(f)
                # Populate our results dict with the existing data
                for key in results.keys():
                    results[key] = existing_data.get(key, [])
        except json.JSONDecodeError:
            print("Existing eval_results.json is corrupted. Starting fresh.")

    # Helper function to check if a turn is already done
    def get_existing_turn(agent_key, persona_name, turn_num):
        for entry in results[agent_key]:
            if entry.get("persona") == persona_name and entry.get("turn") == turn_num:
                return entry
        return None

    # ==========================================
    # 2. GROUP THE FLAT DATASET BY PERSONA
    # ==========================================
    tasks_by_persona = {}
    for task in dataset:
        p = task['persona']
        if persona_filter and p != persona_filter:
            continue
        if p not in tasks_by_persona:
            tasks_by_persona[p] = []
        tasks_by_persona[p].append(task)

    if max_turns:
        tasks_by_persona = {p: turns[:max_turns] for p, turns in tasks_by_persona.items()}
        
    # ==========================================
    # 3. RUN MULTI-TURN LIFELONG LEARNING
    # ==========================================
    for persona, turns in tasks_by_persona.items():
        print(f"\n==================================================")
        print(f"Starting Lifelong Learning Simulation for: {persona}")
        print(f"==================================================")
        
        # --- NEW: FAST-FORWARD CHECK ---
        is_fully_completed = True
        for agent_key in ["ZeroShot", "RagHistory", "NaiveSummary", "EPPS"]:
            completed_turns = [r for r in results[agent_key] if r.get("persona") == persona]
            if len(completed_turns) < len(turns):
                is_fully_completed = False
                break
                
        if is_fully_completed:
            print(f"✅ {persona} is fully evaluated ({len(turns)}/{len(turns)} turns). Skipping to next persona.")
            continue
        # -------------------------------
        
        # INITIALIZE AGENTS ONLY ONCE PER PERSONA
        epps_agent = EPPSAgent(user_id=f"{persona}_user", api_client=api_client)
        rag_history = RagHistoryAgent(api_client)
        naive_summary = NaiveSummaryAgent(api_client)
        zero_shot = ZeroShotAgent(api_client)

        for turn_index, turn_data in enumerate(turns):
            current_turn = turn_index + 1
            print(f"\n--- {persona} | Turn {current_turn}/{len(turns)} ---")
            
            history_log = turn_data['history_log']
            correction_log = turn_data['human_correction_log']
            novel_items = turn_data['novel_items']
            ground_truth = turn_data['ground_truth_destinations']
            chore_type = turn_data.get('chore_type', '')
            context = turn_data.get('context', 'Regular tidying')
            instruction = f"{context}. Tidy up the room according to my {persona} habits."

            try:
                # --- A. UPDATE MEMORIES (LAYER 1) ---
                # We MUST do this even if skipping prediction, so agents don't lose memory for future turns.
                prev_correction = turn_data.get('_prev_correction_log', [])
                combined_history = history_log + prev_correction

                epps_agent.observe_background(combined_history)
                rag_history.update_memory(combined_history)
                naive_summary.update_memory(combined_history)

                # --- B. CHECK EXISTING RESULTS ---
                ext_zs = get_existing_turn("ZeroShot", persona, current_turn)
                ext_rag = get_existing_turn("RagHistory", persona, current_turn)
                ext_ns = get_existing_turn("NaiveSummary", persona, current_turn)
                ext_epps = get_existing_turn("EPPS", persona, current_turn)

                # --- C. PREDICT & RECORD (ONLY IF MISSING) ---
                made_new_prediction = False

                if ext_zs:
                    print(f"[ZeroShot] {persona} Turn {current_turn} exists. Skipping predict.")
                else:
                    pred = zero_shot.predict(instruction, novel_items, combined_history)
                    results["ZeroShot"].append({
                        "persona": persona, "turn": current_turn, "chore_type": chore_type,
                        "prediction": pred, "ground_truth": ground_truth,
                        "pfs": calculate_pfs(pred, ground_truth, novel_items),
                        "pfs_relaxed": calculate_pfs(pred, ground_truth, novel_items, use_synonyms=True)
                    })
                    made_new_prediction = True

                if ext_rag:
                    print(f"[RagHistory] {persona} Turn {current_turn} exists. Skipping predict.")
                else:
                    pred = rag_history.predict(instruction, novel_items)
                    results["RagHistory"].append({
                        "persona": persona, "turn": current_turn, "chore_type": chore_type,
                        "prediction": pred, "ground_truth": ground_truth,
                        "pfs": calculate_pfs(pred, ground_truth, novel_items),
                        "pfs_relaxed": calculate_pfs(pred, ground_truth, novel_items, use_synonyms=True)
                    })
                    made_new_prediction = True

                if ext_ns:
                    print(f"[NaiveSummary] {persona} Turn {current_turn} exists. Skipping predict.")
                else:
                    pred = naive_summary.predict(instruction, novel_items)
                    results["NaiveSummary"].append({
                        "persona": persona, "turn": current_turn, "chore_type": chore_type,
                        "prediction": pred, "ground_truth": ground_truth,
                        "pfs": calculate_pfs(pred, ground_truth, novel_items),
                        "pfs_relaxed": calculate_pfs(pred, ground_truth, novel_items, use_synonyms=True)
                    })
                    made_new_prediction = True

                if ext_epps:
                    print(f"[EPPS] {persona} Turn {current_turn} exists. Skipping predict.")
                else:
                    pred = epps_agent.plan_execution(instruction, novel_items)
                    results["EPPS"].append({
                        "persona": persona, "turn": current_turn, "chore_type": chore_type,
                        "prediction": pred, "ground_truth": ground_truth,
                        "pfs": calculate_pfs(pred, ground_truth, novel_items),
                        "pfs_relaxed": calculate_pfs(pred, ground_truth, novel_items, use_synonyms=True),
                        "cgm_snapshot": epps_agent.cgm_state.model_dump() if epps_agent.cgm_state else {}
                    })
                    made_new_prediction = True

                # --- D. SAVE PROGRESS ---
                # Only write to disk if we actually generated new data this loop
                if made_new_prediction:
                    with open(results_path, "w") as f:
                        json.dump(results, f, indent=4)

                # --- E. IMPLICIT FEEDBACK (LAYER 2) ---
                # We MUST do this so EPPS state updates for the next turn!
                epps_agent.receive_feedback(correction_log)
                if turn_index + 1 < len(turns):
                    turns[turn_index + 1]['_prev_correction_log'] = correction_log

            except Exception as e:
                print(f"Turn {current_turn} failed due to: {e}")
                traceback.print_exc()
                break # Break out of the loop for this persona if an error occurs

    print("\nEvaluation complete. Results saved to data/eval_results.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", type=str, default=None, help="Filter to a single persona (e.g. Minimalist)")
    parser.add_argument("--max-turns", type=int, default=None, help="Limit number of turns per persona")
    parser.add_argument("--dataset", type=str, default="data/eval_dataset.json")
    args = parser.parse_args()
    run_evaluation(args.dataset, persona_filter=args.persona, max_turns=args.max_turns)