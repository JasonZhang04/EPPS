import copy
import sys
import os

# Add the parent directory to sys.path so 'virtualhome' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

try:
    from virtualhome.simulation.evolving_graph.environment import EnvironmentGraph
    from virtualhome.simulation.evolving_graph.execution import ScriptExecutor
    from virtualhome.simulation.evolving_graph.scripts import Script
    import virtualhome.simulation.evolving_graph.utils as utils
except ImportError as e:
    print(f"Warning: VirtualHome library could not be imported: {e}")

from src.data_gen.environment_base import get_base_graph, extract_diffs

def validate_and_extract(generated_script_lines: list[str]) -> dict:
    """
    Executes the LLM-generated script in the VH engine. 
    Returns the topological state diffs if successful.
    """
    base_graph_dict = get_base_graph()
    
    try:
        current_graph = EnvironmentGraph(copy.deepcopy(base_graph_dict))
        name_equivalence = utils.load_name_equivalence()
        executor = ScriptExecutor(current_graph, name_equivalence)
        
        # Attempt to execute the LLM's script
        script = Script(generated_script_lines)
        success, message, state_list = executor.execute(script)
        
        if not success:
            return {"status": "failed", "error": message}
            
        final_state = state_list[-1]
        final_state_dict = final_state.to_dict() if not isinstance(final_state, dict) else final_state
        
        # Run the diff logic
        state_diffs = extract_diffs(base_graph_dict, final_state_dict)
        
        return {"status": "success", "diffs": state_diffs}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
