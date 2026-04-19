"""
=============================================================================
Project: Embodied Pragmatic Program Synthesis (EPPS)
Preliminary Experiment 1: Scaled-Up Layer 1 Extraction (REAL-WORLD NOISE)
Task: "Unpack the bags" (25 Items, Human Avatar Tracking, Interruptions)
=============================================================================
"""

import copy
from virtualhome.simulation.evolving_graph.environment import EnvironmentGraph
from virtualhome.simulation.evolving_graph.execution import ScriptExecutor
from virtualhome.simulation.evolving_graph.scripts import Script, ScriptLine, Action, ScriptObject
import virtualhome.simulation.evolving_graph.utils as utils

def get_location(state_dict, item_name):
    """
    Advanced Graph Parser: Handles specific receptacles, macro-rooms, 
    and human interactions (HOLDS_RH / HOLDS_LH).
    """
    nodes = state_dict.get('nodes', [])
    edges = state_dict.get('edges', [])
    
    target_node = next((n for n in nodes if n.get('class_name') == item_name), None)
    if not target_node: return "UNKNOWN", "UNKNOWN"
    t_id = target_node['id']

    # 1. Track the Human Character's Room
    if item_name == 'character':
        for edge in edges:
            if edge.get('from_id') == t_id and edge.get('relation_type') == 'INSIDE':
                room = next((n for n in nodes if n.get('id') == edge.get('to_id')), None)
                if room and room.get('category') == 'Rooms':
                    return 'INSIDE', room.get('class_name')
        return "UNKNOWN", "UNKNOWN"

    # 2. THE FIX: Check for any type of HOLDS relation (RH or LH)
    for edge in edges:
        if edge.get('to_id') == t_id and 'HOLDS' in str(edge.get('relation_type')).upper():
            return 'HELD_BY', 'character'

    # 3. Standard Receptacle Checking (ON / INSIDE furniture)
    for edge in edges:
        if edge.get('from_id') == t_id:
            rel = str(edge.get('relation_type')).upper()
            if rel in ['ON', 'INSIDE']:
                parent = next((n for n in nodes if n.get('id') == edge.get('to_id')), None)
                if parent:
                    # Skip bounding boxes to get the actual furniture
                    if parent.get('category') == 'Rooms' or parent.get('class_name') in ['kitchen', 'bedroom', 'living_room', 'bathroom']:
                        continue
                    clean_rel = 'INSIDE' if 'INSIDE' in rel else 'ON'
                    return clean_rel, parent.get('class_name')
                    
    # 4. Fallback: Dropped on the floor of a room
    for edge in edges:
        if edge.get('from_id') == t_id and edge.get('relation_type') == 'INSIDE':
            room = next((n for n in nodes if n.get('id') == edge.get('to_id')), None)
            if room: return 'ON_FLOOR_IN', room.get('class_name')

    return "UNKNOWN", "UNKNOWN"

def run_complex_extraction_test():
    print("=== EPPS Preliminary Experiment 1: Complete Real-World Extraction ===")
    
    graph_dict = {
        'nodes': [
            # Rooms & Character
            {'id': 1, 'class_name': 'kitchen', 'category': 'Rooms', 'properties': [], 'states': []},
            {'id': 2, 'class_name': 'bedroom', 'category': 'Rooms', 'properties': [], 'states': []},
            {'id': 3, 'class_name': 'living_room', 'category': 'Rooms', 'properties': [], 'states': []},
            {'id': 4, 'class_name': 'bathroom', 'category': 'Rooms', 'properties': [], 'states': []},
            {'id': 5, 'class_name': 'character', 'category': '', 'properties': [], 'states': []},
            
            # Receptacles
            {'id': 10, 'class_name': 'fridge', 'category': 'Appliances', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
            {'id': 11, 'class_name': 'kitchen_table', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            {'id': 12, 'class_name': 'sink', 'category': 'Appliances', 'properties': ['SURFACES'], 'states': []},
            {'id': 13, 'class_name': 'desk', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            {'id': 14, 'class_name': 'bookshelf', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            {'id': 15, 'class_name': 'closet', 'category': 'Furniture', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
            {'id': 16, 'class_name': 'sofa', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            {'id': 17, 'class_name': 'bathroom_cabinet', 'category': 'Furniture', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
            
            # Target Items (Groceries -> Fridge)
            {'id': 20, 'class_name': 'apple', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 21, 'class_name': 'milk', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 22, 'class_name': 'salmon', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 23, 'class_name': 'cheese', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            
            # Target Items (Electronics -> Desk)
            {'id': 24, 'class_name': 'laptop', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 25, 'class_name': 'tablet', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 26, 'class_name': 'charger', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 27, 'class_name': 'headphones', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            
            # Target Items (Study Materials -> Bookshelf)
            {'id': 28, 'class_name': 'textbook', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 29, 'class_name': 'notebook', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 30, 'class_name': 'pen', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            
            # Target Items (Clothing/Hygiene -> Closet / Bathroom)
            {'id': 31, 'class_name': 'jacket', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 32, 'class_name': 'shoes', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 33, 'class_name': 'toothpaste', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            
            # Distractors (Noise - Intended to stay STATIC on the table)
            {'id': 34, 'class_name': 'water_glass', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 35, 'class_name': 'keys', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 36, 'class_name': 'tv_remote', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 37, 'class_name': 'mail', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 38, 'class_name': 'sunglasses', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        ],
        'edges': [
            {'from_id': 5, 'to_id': 1, 'relation_type': 'INSIDE'}, # Character starts in kitchen
            {'from_id': 10, 'to_id': 1, 'relation_type': 'INSIDE'}, 
            {'from_id': 11, 'to_id': 1, 'relation_type': 'INSIDE'}, 
            {'from_id': 12, 'to_id': 1, 'relation_type': 'INSIDE'}, 
            {'from_id': 13, 'to_id': 2, 'relation_type': 'INSIDE'}, 
            {'from_id': 14, 'to_id': 2, 'relation_type': 'INSIDE'}, 
            {'from_id': 15, 'to_id': 2, 'relation_type': 'INSIDE'}, 
            {'from_id': 16, 'to_id': 3, 'relation_type': 'INSIDE'}, 
            {'from_id': 17, 'to_id': 4, 'relation_type': 'INSIDE'}, 
        ]
    }

    # Dump all 19 items ON the kitchen_table
    for item_id in range(20, 39):
        graph_dict['edges'].append({'from_id': item_id, 'to_id': 1, 'relation_type': 'INSIDE'})
        graph_dict['edges'].append({'from_id': item_id, 'to_id': 11, 'relation_type': 'ON'})

    name_equivalence = utils.load_name_equivalence()
    current_graph = EnvironmentGraph(copy.deepcopy(graph_dict))

    def interact(action, item_name, item_id, target_name=None, target_id=None):
        if target_name:
            return ScriptLine(action, [ScriptObject(item_name, item_id), ScriptObject(target_name, target_id)], 0)
        return ScriptLine(action, [ScriptObject(item_name, item_id)], 0)

    script_lines = [
        # 1. Grab jacket, toss it on sofa temporarily (Multi-step noise)
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'jacket', 31),
        interact(Action.WALK, 'sofa', 16),
        interact(Action.PUTBACK, 'jacket', 31, 'sofa', 16),
        
        # 2. Start sorting groceries (Includes Salmon)
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'milk', 21),
        interact(Action.WALK, 'fridge', 10),
        interact(Action.OPEN, 'fridge', 10),
        interact(Action.PUTIN, 'milk', 21, 'fridge', 10),
        
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'salmon', 22),
        interact(Action.WALK, 'fridge', 10),
        interact(Action.PUTIN, 'salmon', 22, 'fridge', 10),
        
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'apple', 20),
        interact(Action.WALK, 'fridge', 10),
        interact(Action.PUTIN, 'apple', 20, 'fridge', 10),
        interact(Action.CLOSE, 'fridge', 10),
        
        # 3. Random Noise: Pick up mail, put it back
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'mail', 37),
        interact(Action.PUTBACK, 'mail', 37, 'kitchen_table', 11),
        
        # 4. Electronics to Desk
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'laptop', 24),
        interact(Action.WALK, 'desk', 13),
        interact(Action.PUTBACK, 'laptop', 24, 'desk', 13),
        
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'headphones', 27),
        interact(Action.WALK, 'desk', 13),
        interact(Action.PUTBACK, 'headphones', 27, 'desk', 13),
        
        # 5. Distractor task: Move water glass to sink (Noise)
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'water_glass', 34),
        interact(Action.WALK, 'sink', 12),
        interact(Action.PUTBACK, 'water_glass', 34, 'sink', 12),
        
        # 6. Study Materials
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'textbook', 28),
        interact(Action.WALK, 'bookshelf', 14),
        interact(Action.PUTBACK, 'textbook', 28, 'bookshelf', 14),
        
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'pen', 30),
        interact(Action.WALK, 'bookshelf', 14),
        interact(Action.PUTBACK, 'pen', 30, 'bookshelf', 14),
        
        # 7. Resolve the Jacket (Multi-step completion)
        interact(Action.WALK, 'sofa', 16),
        interact(Action.GRAB, 'jacket', 31),
        interact(Action.WALK, 'closet', 15),
        interact(Action.OPEN, 'closet', 15),
        interact(Action.PUTIN, 'jacket', 31, 'closet', 15),
        interact(Action.CLOSE, 'closet', 15),
        
        # 8. Toss keys on sofa (Noise)
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'keys', 35),
        interact(Action.WALK, 'sofa', 16),
        interact(Action.PUTBACK, 'keys', 35, 'sofa', 16),
        
        # 9. Bathroom hygiene
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'toothpaste', 33),
        interact(Action.WALK, 'bathroom_cabinet', 17),
        interact(Action.OPEN, 'bathroom_cabinet', 17),
        interact(Action.PUTIN, 'toothpaste', 33, 'bathroom_cabinet', 17),
        interact(Action.CLOSE, 'bathroom_cabinet', 17),

        # 10. INTERRUPTED TASK: Grab tablet, hold it, walk to living room
        interact(Action.WALK, 'kitchen_table', 11),
        interact(Action.GRAB, 'tablet', 25),
        interact(Action.WALK, 'sofa', 16) # Character walks to living room holding the tablet
    ]

    is_success = True
    final_raw_dict = None  
    for i, line in enumerate(script_lines):
        executor = ScriptExecutor(current_graph, name_equivalence)
        success, message, state_list = executor.execute(Script([line]))
        if not success:
            is_success = False
            break
        raw_state = state_list[-1]
            
        if isinstance(raw_state, dict):
            final_raw_dict = raw_state
            current_graph = EnvironmentGraph(raw_state)
        else:
            final_raw_dict = raw_state.to_dict()
            current_graph = raw_state

    if is_success and final_raw_dict is not None:
        print("\n" + "="*70)
        print("[System State] Extracting Raw Topological Diff...")
        print("-" * 70)
        
        # We track ALL items, plus the human character
        all_entities = ['character', 'apple', 'milk', 'salmon', 'cheese', 'laptop', 'tablet', 'charger', 'headphones',
                        'textbook', 'notebook', 'pen', 'jacket', 'shoes', 'toothpaste', 
                        'water_glass', 'keys', 'tv_remote', 'mail', 'sunglasses']
        
        for entity in all_entities:
            init_rel, init_loc = get_location(graph_dict, entity)
            final_rel, final_loc = get_location(final_raw_dict, entity)
            
            if init_loc != final_loc or init_rel != final_rel:
                print(f"[MOVED]   {entity:<12} : ({init_rel} {init_loc}) -> ({final_rel} {final_loc})")
            else:
                print(f"[STATIC]  {entity:<12} : Remained at ({init_rel} {init_loc})")
                
        print("="*70)

if __name__ == '__main__':
    run_complex_extraction_test()