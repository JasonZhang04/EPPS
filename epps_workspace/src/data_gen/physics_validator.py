import copy
import re
import sys
import os

# Point directly at the simulation/ subdirectory to bypass two broken __init__.py files:
#   virtualhome/__init__.py — hardcoded Windows path + Unity visual renderer
#   simulation/__init__.py  — imports unity_simulator (cv2, PIL, etc. not needed here)
# We only use the text-based evolving_graph; none of those visual deps apply.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'virtualhome', 'virtualhome', 'simulation')))

VH_AVAILABLE = False
try:
    from evolving_graph.environment import EnvironmentGraph
    from evolving_graph.execution import ScriptExecutor
    from evolving_graph.scripts import Script, parse_script_line, ScriptParseException
    import evolving_graph.utils as utils
    VH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: VirtualHome library could not be imported: {e}")

from src.data_gen.environment_base import get_base_graph, extract_diffs


def _parse_dsl_lines(raw_lines: list[str]):
    """
    Converts LLM DSL strings to ScriptLine objects.
    Strips the optional <charN> prefix that LLMs tend to emit before delegating
    to VirtualHome's own parse_script_line, which expects '[action] <item> (id)'.
    Returns (script_lines, error_string) — error_string is None on success.
    """
    script_lines = []
    for i, line in enumerate(raw_lines):
        line = line.strip()
        if not line or '[' not in line:
            continue
        # Strip optional "<char0> " prefix
        line = re.sub(r'^<char\d+>\s*', '', line)
        try:
            script_lines.append(parse_script_line(line, i + 1))
        except ScriptParseException as e:
            return None, f"Parse error on line {i+1} '{line}': {e}"
    return script_lines, None


def validate_and_extract(generated_script_lines: list[str]) -> dict:
    """
    Parses and executes the LLM-generated script through the VirtualHome physics engine.
    Runs line-by-line (updating the graph between steps) to mirror how the working
    experiment code operates. Returns topological state diffs on success.
    """
    if not VH_AVAILABLE:
        return {"status": "failed", "error": "VirtualHome library not available"}

    base_graph_dict = get_base_graph()

    try:
        script_lines, parse_error = _parse_dsl_lines(generated_script_lines)
        if parse_error:
            return {"status": "failed", "error": parse_error}
        if not script_lines:
            return {"status": "failed", "error": "No valid script lines parsed from LLM output"}

        name_equivalence = utils.load_name_equivalence()
        current_graph = EnvironmentGraph(copy.deepcopy(base_graph_dict))
        final_state_dict = None

        for i, script_line in enumerate(script_lines):
            executor = ScriptExecutor(current_graph, name_equivalence)
            success, _, state_list = executor.execute(Script([script_line]))

            if not success:
                return {"status": "failed", "error": f"Physics violation at step {i+1}: {script_line}"}

            raw_state = state_list[-1]
            if isinstance(raw_state, dict):
                final_state_dict = raw_state
                current_graph = EnvironmentGraph(raw_state)
            else:
                final_state_dict = raw_state.to_dict()
                current_graph = raw_state

        if final_state_dict is None:
            return {"status": "failed", "error": "Script produced no state"}

        return {"status": "success", "diffs": extract_diffs(base_graph_dict, final_state_dict)}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
