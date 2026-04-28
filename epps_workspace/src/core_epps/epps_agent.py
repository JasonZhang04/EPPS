import json
from src.models.schemas import CommonGroundModel, ItemOverride, RuleSource
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
        
        existing_cgm_json = self.cgm_state.model_dump_json() if self.cgm_state else None
        raw_cgm_json = extract_cgm_from_background(self.api_client, state_diff_log, existing_cgm_json)
        
        try:
            self.cgm_state = CommonGroundModel(**json.loads(raw_cgm_json))
        except Exception as e:
            print(f"[{self.user_id}] Error parsing CGM JSON from Layer 1: {e}")
            if not self.cgm_state:
                self.cgm_state = CommonGroundModel(user_id=self.user_id, category_mappings={})
            # If self.cgm_state already exists, retain previous state

    def receive_feedback(self, correction_diff_log: list[str]):
        """Layer 2: Implicit Correction. Updates the CGM based on human overriding actions."""
        if not self.cgm_state:
            raise ValueError("Cannot apply Layer 2 feedback without an existing Layer 1 CGM.")
        print(f"[{self.user_id}] Layer 2: Applying human correction log...")
        delta_json = apply_human_correction(self.api_client, correction_diff_log)
        
        try:
            delta = json.loads(delta_json)
            item = delta.get("item_name")
            dest = delta.get("new_destination")
            
            if item in self.cgm_state.item_overrides:
                old_conf = self.cgm_state.item_overrides[item].confidence
                # Each human correction is strong positive evidence: +0.2 per confirmation,
                # capped at 0.95 to avoid over-certainty. After 4 corrections: 0.3→0.5→0.7→0.9→0.95.
                new_conf = min(old_conf + 0.2, 0.95)
                self.cgm_state.item_overrides[item].confidence = new_conf
                self.cgm_state.item_overrides[item].destination = dest
            else:
                # Create new override with heavily discounted initial confidence
                self.cgm_state.item_overrides[item] = ItemOverride(
                    destination=dest, confidence=0.3, source=RuleSource(layer="L2_correction")
                )
        except Exception as e:
            print(f"[{self.user_id}] Error parsing delta JSON from Layer 2: {e}")

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
