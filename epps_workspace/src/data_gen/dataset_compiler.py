import json
import os
import time

from src.api.thinking_machine import ThinkingMachineClient
from src.data_gen.persona_definitions import (
    PERSONAS,
    NOVEL_ITEM_GROUND_TRUTHS,
    CHORE_CORRECTIONS,
    CHORE_SCHEDULE,
)
from src.data_gen.vh_script_writer import request_vh_script
from src.data_gen.physics_validator import validate_and_extract


def compile_dataset(
    api_client: ThinkingMachineClient,
    output_path: str = "data/eval_dataset.json",
    max_retries: int = 10,
):
    """
    Generates a multi-turn, persona-diverse dataset for EPPS evaluation.

    Key design properties vs. v1:
    - "Day in the Life" structure: each turn is a thematically coherent chore
      session (Morning Routine, Grocery Put-Away, Office Setup, …) so the
      history logs accumulate within-category evidence the CGM can exploit.
    - Novel items are correlated with chore type: when the agent observes an
      Office Setup session, it is tested on office-adjacent novel items
      (sticky_notes, power_bank, book_novel), so category-level CGM rules
      directly improve performance.
    - Corrections are chore-type-specific: the human correction always refers
      to an item from that session, giving targeted per-category feedback.
    - 20 turns × 5 personas = 100 tasks (up from 30).
    - 8 chore types with 2-3 repetitions each, so the agent observes each
      semantic category multiple times and can build confident CGM rules.
    """
    print("Starting Day-in-the-Life Multi-Turn Dataset Generation...")
    dataset = []

    turns_per_persona = len(CHORE_SCHEDULE)  # 20

    for persona_name, persona_data in PERSONAS.items():
        print(f"\n{'='*60}")
        print(f"Generating {turns_per_persona} turns for: {persona_name}")
        print(f"{'='*60}")

        novel_gt = NOVEL_ITEM_GROUND_TRUTHS[persona_name]
        persona_corrections = CHORE_CORRECTIONS[persona_name]

        for turn_idx, chore in enumerate(CHORE_SCHEDULE):
            turn_num = turn_idx + 1
            chore_type = chore["chore_type"]
            context = chore["context"]
            training_items = chore["training_items"]
            novel_items = chore["novel_items"]

            # Ground truth for exactly the novel items in this turn
            turn_ground_truth = {item: novel_gt[item] for item in novel_items}

            # Correction relevant to this chore type
            correction = persona_corrections[chore_type]

            success = False
            attempts = 0
            while not success and attempts < max_retries:
                attempts += 1
                print(
                    f"  [{persona_name} | Turn {turn_num} | {chore_type}] "
                    f"Attempt {attempts}/{max_retries}..."
                )

                script_lines = request_vh_script(
                    api_client,
                    persona_data["description"],
                    training_items=training_items,
                    context=context,
                )
                result = validate_and_extract(script_lines)

                if result["status"] == "success":
                    diffs = result["diffs"]
                    print(f"    -> SUCCESS: {len(diffs)} state diffs.")

                    task_entry = {
                        "persona": persona_name,
                        "turn": turn_num,
                        "chore_type": chore_type,
                        "context": context,
                        "training_items": [name for name, _ in training_items],
                        "history_log": diffs,
                        "human_correction_log": correction,
                        "novel_items": novel_items,
                        "ground_truth_destinations": turn_ground_truth,
                        "raw_script": script_lines,
                    }
                    dataset.append(task_entry)
                    success = True
                else:
                    print(f"    -> REJECTED: {result['error']}")
                    time.sleep(1)

            if not success:
                print(
                    f"WARNING: Max retries reached for {persona_name} "
                    f"turn {turn_num} ({chore_type}). Skipping."
                )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=4)

    print(
        f"\nDataset saved to {output_path} "
        f"({len(dataset)} tasks, {len(PERSONAS)} personas × {turns_per_persona} turns)"
    )


if __name__ == "__main__":
    client = ThinkingMachineClient()
    compile_dataset(client)
