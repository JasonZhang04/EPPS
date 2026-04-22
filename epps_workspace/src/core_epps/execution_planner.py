import json
import yaml
import os
import re
from typing import List
from src.api.thinking_machine import ThinkingMachineClient

def synthesize_execution_program(api_client: ThinkingMachineClient, instruction: str, novel_items: List[str], cgm_json: str) -> str:
    """
    Queries the CGM constraint solver to route novel items.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'planner_prompts.yaml')
    with open(prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        
    system_prompt = prompts['system_prompt'].format(
        instruction=instruction,
        novel_items=novel_items
    )
    
    user_message = (
        f"USER CGM:\n{cgm_json}\n\n"
        "Assign the destinations for the novel items based strictly on this CGM.\n"
        "CRITICAL INSTRUCTION: Treat `item_overrides` with absolute priority over `category_mappings`."
    )
    
    response = api_client.query([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], temperature=0.0)
    
    print(f"\n[DEBUG] Raw Planner LLM Response:\n{response}\n")
    
    # Robust Regex JSON extraction fallback
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        response = match.group(0)
    else:
        # Fallback if regex fails to find a dictionary
        response = "{}"
        
    return response