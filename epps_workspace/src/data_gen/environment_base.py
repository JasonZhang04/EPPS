import copy

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

    # 2. Check for any type of HOLDS relation (RH or LH)
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

def extract_diffs(base_graph_dict, final_raw_dict):
    """
    Extracts topological state diffs for items that moved.
    """
    diffs = []
    # Relevant entities for this experimental scope:
    all_entities = ['character', 'apple', 'milk', 'salmon', 'cheese', 'laptop', 'tablet', 'charger', 'headphones',
                    'textbook', 'notebook', 'pen', 'jacket', 'shoes', 'toothpaste', 
                    'water_glass', 'keys', 'tv_remote', 'mail', 'sunglasses']
    
    for entity in all_entities:
        init_rel, init_loc = get_location(base_graph_dict, entity)
        final_rel, final_loc = get_location(final_raw_dict, entity)
        
        if init_loc != final_loc or init_rel != final_rel:
            diffs.append(f"[MOVED] {entity} : ({init_rel} {init_loc}) -> ({final_rel} {final_loc})")
            
    return diffs

# Static Base Dictionary for the Scenario
BASE_GRAPH_DICT = {
    'nodes': [
        {'id': 1, 'class_name': 'kitchen', 'category': 'Rooms', 'properties': [], 'states': []},
        {'id': 2, 'class_name': 'bedroom', 'category': 'Rooms', 'properties': [], 'states': []},
        {'id': 3, 'class_name': 'living_room', 'category': 'Rooms', 'properties': [], 'states': []},
        {'id': 4, 'class_name': 'bathroom', 'category': 'Rooms', 'properties': [], 'states': []},
        {'id': 5, 'class_name': 'character', 'category': '', 'properties': [], 'states': []},
        
        {'id': 10, 'class_name': 'fridge', 'category': 'Appliances', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
        {'id': 11, 'class_name': 'kitchen_table', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
        {'id': 12, 'class_name': 'sink', 'category': 'Appliances', 'properties': ['SURFACES'], 'states': []},
        {'id': 13, 'class_name': 'desk', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
        {'id': 14, 'class_name': 'bookshelf', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
        {'id': 15, 'class_name': 'closet', 'category': 'Furniture', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
        {'id': 16, 'class_name': 'sofa', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
        {'id': 17, 'class_name': 'bathroom_cabinet', 'category': 'Furniture', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
        
        {'id': 20, 'class_name': 'apple', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 21, 'class_name': 'milk', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 22, 'class_name': 'salmon', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 23, 'class_name': 'cheese', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 24, 'class_name': 'laptop', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 25, 'class_name': 'tablet', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 26, 'class_name': 'charger', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 27, 'class_name': 'headphones', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 28, 'class_name': 'textbook', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 29, 'class_name': 'notebook', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 30, 'class_name': 'pen', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 31, 'class_name': 'jacket', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 32, 'class_name': 'shoes', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 33, 'class_name': 'toothpaste', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 34, 'class_name': 'water_glass', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 35, 'class_name': 'keys', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 36, 'class_name': 'tv_remote', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 37, 'class_name': 'mail', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        {'id': 38, 'class_name': 'sunglasses', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
    ],
    'edges': [
        {'from_id': 5, 'to_id': 1, 'relation_type': 'INSIDE'}, 
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

# Dump all 19 items ON the kitchen_table to establish the starting state
for item_id in range(20, 39):
    BASE_GRAPH_DICT['edges'].append({'from_id': item_id, 'to_id': 1, 'relation_type': 'INSIDE'})
    BASE_GRAPH_DICT['edges'].append({'from_id': item_id, 'to_id': 11, 'relation_type': 'ON'})

def get_base_graph():
    return copy.deepcopy(BASE_GRAPH_DICT)
