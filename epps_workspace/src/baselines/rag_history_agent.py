import json
import yaml
import os
from typing import List, Dict
from src.api.thinking_machine import ThinkingMachineClient

class RagHistoryAgent:
    def __init__(self, api_client: ThinkingMachineClient):
        self.api_client = api_client
        
        prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'baseline_prompts.yaml')
        with open(prompt_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

    def predict(self, instruction: str, novel_items: List[str], history_log: List[str]) -> Dict[str, str]:
        history_text = "\n".join(history_log)
        system_prompt = self.prompts['rag_history'].format(
            history_log=history_text,
            instruction=instruction,
            novel_items=novel_items
        )
        
        response = self.api_client.query([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Execute the task."}
        ], temperature=0.0)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].strip()
            return json.loads(response)
        except Exception:
            return {}
