import json
import os
import time

from src.api.thinking_machine import ThinkingMachineClient
from src.data_gen.persona_definitions import PERSONAS, GROUND_TRUTH_EVAL, CORRECTION_SCENARIOS
from src.data_gen.vh_script_writer import request_vh_script
from src.data_gen.physics_validator import validate_and_extract

def compile_dataset(api_client: ThinkingMachineClient, output_path: str = "data/eval_dataset.json"):
    print("Starting Hybrid Synthesis Data Generation (Rejection Sampling Loop)...")
    dataset = []
    
    # 10 tasks per persona = 30 tasks total
    tasks_per_persona = 10
    max_retries = 10
    
    for persona_name, persona_data in PERSONAS.items():
        print(f"\n--- Generating scripts for {persona_name} ---")
        
        successful_tasks = 0
        while successful_tasks < tasks_per_persona:
            attempts = 0
            success = False
            
            while not success and attempts < max_retries:
                attempts += 1
                print(f"[{persona_name} | Task {successful_tasks+1}] Attempt {attempts}/{max_retries}...")
                
                # 1. Ask LLM to generate script
                script_lines = request_vh_script(api_client, persona_data['description'])
                
                # 2. Pass to physics validator
                validation_result = validate_and_extract(script_lines)
                
                if validation_result['status'] == 'success':
                    diffs = validation_result['diffs']
                    print(f"  -> SUCCESS! Generated {len(diffs)} topological state diffs.")

                    correction_log = CORRECTION_SCENARIOS[persona_name]
                    novel_items = list(GROUND_TRUTH_EVAL[persona_name].keys())
                    ground_truth = GROUND_TRUTH_EVAL[persona_name]

                    task_entry = {
                        "persona": persona_name,
                        "history_log": diffs,
                        "human_correction_log": correction_log,
                        "novel_items": novel_items,
                        "ground_truth_destinations": ground_truth,
                        "raw_script": script_lines
                    }
                    dataset.append(task_entry)
                    successful_tasks += 1
                    success = True
                else:
                    error_msg = validation_result['error']
                    print(f"  -> REJECTED (Physics Violation): {error_msg}")
                    # In a real setup, we might pass the error back to the LLM for self-correction
                    time.sleep(1) 
                    
            if not success:
                print(f"WARNING: Max retries reached for {persona_name} task {successful_tasks+1}. Skipping.")
                successful_tasks += 1 # Force skip
                
    # Save the dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=4)
        
    print(f"\nHybrid Synthesis Complete! Dataset saved to {output_path}")

if __name__ == "__main__":
    client = ThinkingMachineClient()
    compile_dataset(client)
