from src.api.thinking_machine import ThinkingMachineClient

PROMPT_TEMPLATE = """
You are generating a household activity script for the VirtualHome simulation engine.

ENVIRONMENT:
You have the following character: <character> (5)

RECEPTACLES — surfaces only (use [putback] to place items ON these, cannot be opened):
  <kitchen_table> (11), <sink> (12), <desk> (13), <bookshelf> (14), <sofa> (16)

RECEPTACLES — openable containers (use [open], [putin], [close] to place items INSIDE these):
  <fridge> (10), <closet> (15), <bathroom_cabinet> (17)

You must tidy the following items currently ON the kitchen_table:
  {items_list}

CONTEXT: {context}

PERSONA:
{persona_description}

INSTRUCTIONS:
1. Write a script to tidy the items according to the PERSONA and CONTEXT.
2. You must inject exactly ONE "Noise" action: pick up one item and place it on a wrong surface (e.g., sofa), then later move it to its correct location.
3. You must use ONLY the following actions: [walk], [grab], [putin], [putback], [open], [close].
4. CRITICAL: Only use [open] and [close] on the three openable containers: fridge (10), closet (15), bathroom_cabinet (17). Never [open] a surface.
5. Your output must be strictly formatted line-by-line as VirtualHome DSL. Do not output markdown, explanations, or code blocks.

SYNTAX RULES:
The character must WALK to an object before interacting with it.

- Pick up item from table: <char0> [walk] <item_name> (item_id)
                           <char0> [grab] <item_name> (item_id)

- Place ON a surface:      <char0> [walk] <surface_name> (surface_id)
                           <char0> [putback] <item_name> (item_id) <surface_name> (surface_id)

- Pick up item from surface (e.g. sofa): walk to the ITEM, not the surface
                           <char0> [walk] <item_name> (item_id)
                           <char0> [grab] <item_name> (item_id)
                           NOTE: NEVER write [grab] <sofa> or [grab] <desk>. Always grab the ITEM by name.

- Place INSIDE container:  <char0> [walk] <container_name> (container_id)
                           <char0> [open] <container_name> (container_id)
                           <char0> [putin] <item_name> (item_id) <container_name> (container_id)
                           <char0> [close] <container_name> (container_id)
                           NOTE: [putin] requires [open] immediately before it in the same location. Never skip [open].
"""

def request_vh_script(
    api_client: ThinkingMachineClient,
    persona_description: str,
    training_items: list = None,
    context: str = "Regular evening tidying",
) -> list[str]:
    """
    Calls the LLM to generate a VirtualHome DSL script.

    Args:
        training_items: List of (item_name, item_id) tuples. Defaults to the original 6-item set.
        context: Situational context string added to the prompt for human realism.
    """
    if training_items is None:
        training_items = [
            ("laptop", 24), ("textbook", 28), ("jacket", 31),
            ("apple", 20), ("water_glass", 34), ("keys", 35),
        ]

    items_list = ", ".join(f"<{name}> ({item_id})" for name, item_id in training_items)

    prompt = PROMPT_TEMPLATE.format(
        items_list=items_list,
        context=context,
        persona_description=persona_description,
    )

    # /no_think disables Qwen3's chain-of-thought, which otherwise consumes the
    # entire token budget before writing a single script line.
    response = api_client.query([
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Generate the script now. Output only raw DSL instructions. /no_think"},
    ], temperature=0.7)

    lines = []
    for line in response.split("\n"):
        line = line.strip()
        line = line.replace("<|im_end|>", "").strip()
        if not line:
            continue
        if line.startswith("<char0>") or line.startswith("["):
            if not line.startswith("<char0>"):
                line = f"<char0> {line}"
            lines.append(line)

    return lines
