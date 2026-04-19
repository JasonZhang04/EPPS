import sys
import os
from src.api.thinking_machine import ThinkingMachineClient

PROMPT_TEMPLATE = """
You are generating a household activity script for the VirtualHome simulation engine.

ENVIRONMENT:
You have the following character: <character> (5)
You have the following receptacles: <fridge> (10), <kitchen_table> (11), <sink> (12), <desk> (13), <bookshelf> (14), <closet> (15), <sofa> (16), <bathroom_cabinet> (17).
You must tidy the following items currently ON the kitchen_table: <laptop> (24), <textbook> (28), <jacket> (31), <apple> (20), <water_glass> (34), <keys> (35).

PERSONA:
{persona_description}

INSTRUCTIONS:
1. Write a script to tidy the items according to the PERSONA.
2. You must inject exactly ONE "Noise" action (e.g., picking up an item and dropping it on the sofa or floor, or picking it up and putting it right back).
3. You must use ONLY the following actions: [walk], [grab], [putin], [putback], [open], [close].
4. Your output must be strictly formatted line-by-line as VirtualHome DSL. Do not output markdown, explanations, or code blocks.

SYNTAX RULES:
- To move: <char0> [walk] <item> (id)
- To pick up: <char0> [grab] <item> (id)
- To put ON a surface: <char0> [putback] <item> (id) <receptacle> (id)
- To put INSIDE (must open first): 
  <char0> [open] <receptacle> (id)
  <char0> [putin] <item> (id) <receptacle> (id)
  <char0> [close] <receptacle> (id)
"""

def request_vh_script(api_client: ThinkingMachineClient, persona_description: str) -> list[str]:
    """
    Calls the LLM to generate a VirtualHome DSL script.
    """
    prompt = PROMPT_TEMPLATE.format(persona_description=persona_description)
    
    response = api_client.query([
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Generate the script now. Output only raw instructions."}
    ], temperature=0.7)

    # Clean the output into a list of lines, stripping any stray markdown
    lines = []
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith("<char0>") or line.startswith("["):
            # Some LLMs forget <char0>
            if not line.startswith("<char0>"):
                line = f"<char0> {line}"
            lines.append(line)
            
    return lines
