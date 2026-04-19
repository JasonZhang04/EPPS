import json
import yaml
import os
from typing import List
from src.api.thinking_machine import ThinkingMachineClient

def extract_cgm_from_background(api_client: ThinkingMachineClient, state_diff_log: List[str]) -> str:
    """
    Layer 1: Passive Observation. Compiles the initial CGM.
    """
    # Load prompt
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'layer1_prompts.yaml')
    with open(prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        
    system_prompt = prompts['system_prompt']
    
    # Structure the message
    user_message = f"Here is the human's background behavior log:\n{json.dumps(state_diff_log, indent=2)}\nGenerate the structured CGM JSON."
    
    # Query the LLM
    # In a real setup, we'd force a JSON schema here via the API if it supports it, or request JSON explicitly.
    response = api_client.query([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ], temperature=0.0)
    
    # Extract JSON out of response if it's wrapped in markdown blocks
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response:
        response = response.split("```")[1].strip()
        
    return response
