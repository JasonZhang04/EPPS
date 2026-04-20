import json
import yaml
import os
from typing import List, Dict
from src.api.thinking_machine import ThinkingMachineClient

class NaiveSummaryAgent:
    def __init__(self, api_client: ThinkingMachineClient):
        self.api_client = api_client
        self.current_summary: str = "No history yet."
        
        prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'baseline_prompts.yaml')
        with open(prompt_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

    def update_memory(self, history_log: List[str]):
        if not history_log:
            return
            
        system_prompt = (
            "Read this new history log and update your existing running summary of the user's habits.\n"
            f"Previous Summary: {self.current_summary}"
        )
        history_text = "\n".join(history_log)
        
        response = self.api_client.query([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"New history log:\n{history_text}\nGenerate the updated summary."}
        ], temperature=0.0)
        
        self.current_summary = response.strip()

    def predict(self, instruction: str, novel_items: List[str], history_log: List[str] = None) -> Dict[str, str]:
        # Step 2: Use summary to plan (Step 1 is now handled by update_memory)
        step2_prompt = self.prompts['naive_summary_step2'].format(
            instruction=instruction,
            novel_items=novel_items,
            plain_text_summary=self.current_summary
        )
        
        response = self.api_client.query([
            {"role": "system", "content": step2_prompt},
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
