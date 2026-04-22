import json
import yaml
import os
import re
from typing import List
from src.api.thinking_machine import ThinkingMachineClient
from src.models.schemas import CommonGroundModel

def extract_cgm_from_background(api_client: ThinkingMachineClient, state_diff_log: List[str], existing_cgm_json: str = None) -> str:
    """
    Layer 1: Passive Observation. Compiles the initial CGM.
    """
    # Load prompt
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'layer1_prompts.yaml')
    with open(prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        
    schema_str = json.dumps(CommonGroundModel.model_json_schema(), indent=2)
    system_prompt = prompts['system_prompt'] + f"\n\nJSON SCHEMA YOU MUST FOLLOW:\n{schema_str}"
    
    # Structure the message
    if existing_cgm_json:
        user_message = (
            "You are provided with an EXISTING CGM and a NEW observation log. Merge the new semantic rules into the existing CGM. Output the completely updated CGM.\n\n"
            f"EXISTING CGM:\n{existing_cgm_json}\n\n"
            f"NEW OBSERVATION LOG:\n{json.dumps(state_diff_log, indent=2)}\n"
        )
    else:
        user_message = f"Here is the human's background behavior log:\n{json.dumps(state_diff_log, indent=2)}\nGenerate the structured CGM JSON."
    
    # Query the LLM
    response = api_client.query([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], temperature=0.0)

    print(f"\n[DEBUG] Raw Layer 1 LLM Response:\n{response}\n")
    
    # Extract JSON out of response
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        response = match.group(0)
        
    return response
