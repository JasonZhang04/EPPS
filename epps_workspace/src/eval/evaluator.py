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
    
    # 1. GROUP THE FLAT DATASET BY PERSONA (For Lifelong Learning)
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
            chore_type = turn_data.get('chore_type', '')
            context = turn_data.get('context', 'Regular tidying')
            instruction = f"{context}. Tidy up the room according to my {persona} habits."

            try:
                # --- A. UPDATE MEMORIES (LAYER 1) ---
                # All memory agents see the same information: both the background
                # history log AND the human correction from the previous turn.
                # EPPS processes the correction via structured Layer 2; baselines
                # receive it as additional raw history so information is symmetric.
                # This ensures EPPS's advantage comes from its structured CGM
                # representation, not from having access to more data.
                prev_correction = turn_data.get('_prev_correction_log', [])
                combined_history = history_log + prev_correction

                epps_agent.observe_background(combined_history)
                rag_history.update_memory(combined_history)
                naive_summary.update_memory(combined_history)

                # --- B. PLAN EXECUTION ---
                zs_pred = zero_shot.predict(instruction, novel_items, combined_history)
                rag_pred = rag_history.predict(instruction, novel_items)
                ns_pred = naive_summary.predict(instruction, novel_items)
                epps_pred = epps_agent.plan_execution(instruction, novel_items)

                # --- C. SCORE AND RECORD (FORENSIC LOGGING) ---
                def _record(pred, agent_key, extra=None):
                    entry = {
                        "persona": persona,
                        "turn": turn_index + 1,
                        "chore_type": chore_type,
                        "prediction": pred,
                        "ground_truth": ground_truth,
                        "pfs": calculate_pfs(pred, ground_truth, novel_items),
                        "pfs_relaxed": calculate_pfs(pred, ground_truth, novel_items, use_synonyms=True),
                    }
                    if extra:
                        entry.update(extra)
                    results[agent_key].append(entry)

                _record(zs_pred, "ZeroShot")
                _record(rag_pred, "RagHistory")
                _record(ns_pred, "NaiveSummary")
                _record(
                    epps_pred, "EPPS",
                    extra={"cgm_snapshot": epps_agent.cgm_state.model_dump() if epps_agent.cgm_state else {}}
                )

                # --- D. IMPLICIT FEEDBACK (LAYER 2) ---
                # Apply correction AFTER scoring so it only influences the NEXT turn.
                epps_agent.receive_feedback(correction_log)
                # Tag the correction so the next turn can share it with baselines.
                if turn_index + 1 < len(turns):
                    turns[turn_index + 1]['_prev_correction_log'] = correction_log

            except Exception as e:
                print(f"Turn {turn_index + 1} failed due to: {e}")
                traceback.print_exc()

    # Merge with existing results (so personas accumulate across runs)
    os.makedirs("data", exist_ok=True)
    results_path = "data/eval_results.json"
    if os.path.exists(results_path):
        with open(results_path) as f:
            existing = json.load(f)
        for agent_key, entries in existing.items():
            if agent_key in results:
                results[agent_key] = entries + results[agent_key]
            else:
                results[agent_key] = entries
    with open(results_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print("\nEvaluation complete. Results saved to data/eval_results.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", type=str, default=None, help="Filter to a single persona (e.g. Minimalist)")
    parser.add_argument("--max-turns", type=int, default=None, help="Limit number of turns per persona")
    parser.add_argument("--dataset", type=str, default="eval_dataset.json")
    args = parser.parse_args()
    run_evaluation(args.dataset, persona_filter=args.persona, max_turns=args.max_turns)