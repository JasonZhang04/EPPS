import json
import yaml
import os
import re
from typing import List
from src.api.thinking_machine import ThinkingMachineClient
from src.models.schemas import CorrectionDelta

def apply_human_correction(api_client: ThinkingMachineClient, correction_diff_log: List[str]) -> str:
    """
    Layer 2: Implicit Correction. Updates the CGM based on human overriding actions.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'layer2_prompts.yaml')
    with open(prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        
    schema_str = json.dumps(CorrectionDelta.model_json_schema(), indent=2)
    system_prompt = prompts['system_prompt'] + f"\n\nJSON SCHEMA YOU MUST FOLLOW:\n{schema_str}"
    
    user_message = (
        f"HUMAN CORRECTION LOG:\n{json.dumps(correction_diff_log, indent=2)}\n\n"
        f"Extract the delta using the CorrectionDelta schema. Output ONLY valid JSON."
    )
    
    response = api_client.query([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], temperature=0.0)
    
    last_end = response.rfind('}')
    if last_end != -1:
        depth = 0
        for i in range(last_end, -1, -1):
            if response[i] == '}':
                depth += 1
            elif response[i] == '{':
                depth -= 1
                if depth == 0:
                    response = response[i:last_end + 1]
                    break

    return response
