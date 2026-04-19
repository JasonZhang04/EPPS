import json
from src.models.schemas import CommonGroundModel
from .layer1_extractor import extract_cgm_from_background
from .layer2_corrector import apply_human_correction
from .execution_planner import synthesize_execution_program
from src.api.thinking_machine import ThinkingMachineClient

class EPPSAgent:
    def __init__(self, user_id: str, api_client: ThinkingMachineClient):
        self.user_id = user_id
        self.api_client = api_client
        self.cgm_state: CommonGroundModel = None

    def observe_background(self, state_diff_log: list[str]):
        """Layer 1: Passive Observation. Compiles the initial CGM."""
        print(f"[{self.user_id}] Layer 1: Processing {len(state_diff_log)} background observations...")
        raw_cgm_json = extract_cgm_from_background(self.api_client, state_diff_log)
        try:
            self.cgm_state = CommonGroundModel(**json.loads(raw_cgm_json))
        except Exception as e:
            print(f"[{self.user_id}] Error parsing CGM JSON from Layer 1: {e}")
            self.cgm_state = CommonGroundModel(user_id=self.user_id, category_mappings={})

    def receive_feedback(self, correction_diff_log: list[str]):
        """Layer 2: Implicit Correction. Updates the CGM based on human overriding actions."""
        if not self.cgm_state:
            raise ValueError("Cannot apply Layer 2 feedback without an existing Layer 1 CGM.")
        print(f"[{self.user_id}] Layer 2: Applying human correction log...")
        updated_cgm_json = apply_human_correction(self.api_client, self.cgm_state.model_dump_json(), correction_diff_log)
        
        try:
            new_cgm_data = json.loads(updated_cgm_json)
            # Apply Bayesian momentum decay tracking logic here
            alpha = 0.8
            if self.cgm_state:
                for cat, rule in new_cgm_data.get('category_mappings', {}).items():
                    if cat in self.cgm_state.category_mappings:
                        old_conf = self.cgm_state.category_mappings[cat].confidence
                        # Simplistic decay representation; in a real implementation, 
                        # the logical indicator function calculates if the new correction matched.
                        new_conf = (alpha * old_conf) + ((1 - alpha) * rule.get('confidence', 1.0))
                        rule['confidence'] = new_conf
                        
            self.cgm_state = CommonGroundModel(**new_cgm_data)
        except Exception as e:
            print(f"[{self.user_id}] Error parsing updated CGM JSON from Layer 2: {e}")

    def plan_execution(self, instruction: str, novel_items: list[str]) -> dict[str, str]:
        """Queries the CGM constraint solver to route novel items."""
        if not self.cgm_state:
            raise ValueError("Agent possesses no Common Ground Model to execute pragmatic commands.")
        
        print(f"[{self.user_id}] Planning execution for instruction: '{instruction}'")
        execution_mapping = synthesize_execution_program(
            self.api_client, 
            instruction, 
            novel_items, 
            self.cgm_state.model_dump_json()
        )
        try:
            return json.loads(execution_mapping)
        except Exception as e:
            print(f"[{self.user_id}] Error parsing execution mapping JSON: {e}")
            return {}
