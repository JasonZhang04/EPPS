from pydantic import BaseModel, Field
from typing import Dict, List

class RuleSource(BaseModel):
    layer: str = Field(description="Origin of the rule: 'L1_passive' or 'L2_correction'")
    observation_count: int = Field(default=1, description="Number of times this rule was observed")

class CategoryRule(BaseModel):
    destination: str = Field(description="The target receptacle for this semantic category")
    confidence: float = Field(ge=0.0, le=1.0, description="Probability that this rule is stable")
    source: RuleSource
    member_examples: List[str] = Field(default_factory=list, description="Examples of items seen that formed this rule")

class ItemOverride(BaseModel):
    destination: str = Field(description="The destination for this specific item, overriding its category")
    confidence: float = Field(ge=0.0, le=1.0)
    source: RuleSource

class CommonGroundModel(BaseModel):
    user_id: str
    category_mappings: Dict[str, CategoryRule] = Field(
        description="Maps abstract latent concepts (e.g., 'electronics', 'perishable_food') to destinations."
    )
    item_overrides: Dict[str, ItemOverride] = Field(
        default_factory=dict,
        description="Specific items that break their semantic category rules."
    )
    global_noise_items: List[str] = Field(
        default_factory=list,
        description="Items identified as transient noise (e.g., keys, water glasses) to be ignored in planning."
    )

class CorrectionDelta(BaseModel):
    item_name: str = Field(description="The item the human moved")
    new_destination: str = Field(description="Where the human placed it")
