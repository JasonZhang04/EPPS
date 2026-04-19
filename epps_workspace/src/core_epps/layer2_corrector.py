import json
import yaml
import os
from typing import List
from src.api.thinking_machine import ThinkingMachineClient

def apply_human_correction(api_client: ThinkingMachineClient, current_cgm_json: str, correction_diff_log: List[str]) -> str:
    """
    Layer 2: Implicit Correction. Updates the CGM based on human overriding actions.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'layer2_prompts.yaml')
    with open(prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        
    system_prompt = prompts['system_prompt']
    
    user_message = (
        f"CURRENT CGM:\n{current_cgm_json}\n\n"
        f"HUMAN CORRECTION LOG:\n{json.dumps(correction_diff_log, indent=2)}\n\n"
        f"Please output the fully updated CGM JSON."
    )
    
    response = api_client.query([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], temperature=0.0)
    
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response:
        response = response.split("```")[1].strip()
        
    return response
