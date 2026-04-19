"""
=============================================================================
Project: Embodied Pragmatic Program Synthesis (EPPS)
Experiment 1A: Oracle State Diffing (Step-by-Step Debugging Version)
=============================================================================
"""

import copy
from virtualhome.simulation.evolving_graph.environment import EnvironmentGraph
from virtualhome.simulation.evolving_graph.execution import ScriptExecutor, Relation
from virtualhome.simulation.evolving_graph.scripts import Script, ScriptLine, Action, ScriptObject
import virtualhome.simulation.evolving_graph.utils as utils

def get_item_location_from_dict(state_dict, item_name):
    """
    精准解析版：过滤掉宏观的房间(Rooms)，只抓取具体的家具/电器表面或内部。
    """
    nodes = state_dict.get('nodes', [])
    edges = state_dict.get('edges', [])
    
    item_node = next((n for n in nodes if n.get('class_name') == item_name), None)
    if not item_node:
        return "UNKNOWN", "UNKNOWN"
        
    item_id = item_node['id']
    
    for edge in edges:
        if edge.get('from_id') == item_id:
            rel_type = str(edge.get('relation_type', '')).upper() 
            
            if 'ON' in rel_type or 'INSIDE' in rel_type:
                target_node = next((n for n in nodes if n.get('id') == edge.get('to_id')), None)
                if target_node:
                    # [关键修复] 如果目标节点是房间(kitchen/Rooms)，则跳过，继续寻找具体的家具
                    if target_node.get('category') == 'Rooms' or target_node.get('class_name') == 'kitchen':
                        continue
                        
                    clean_rel = 'INSIDE' if 'INSIDE' in rel_type else 'ON'
                    return clean_rel, target_node.get('class_name', 'UNKNOWN')
                    
    return "UNKNOWN", "UNKNOWN"

def run_experiment_debug():
    print("=== EPPS Experiment 1A: Step-by-Step Debugging ===")
    
    graph_dict = {
        'nodes': [
            {'id': 1, 'class_name': 'kitchen', 'category': 'Rooms', 'properties': [], 'states': []},
            {'id': 2, 'class_name': 'character', 'category': '', 'properties': [], 'states': []},
            {'id': 3, 'class_name': 'fridge', 'category': 'Appliances', 'properties': ['CAN_OPEN'], 'states': ['CLOSED']},
            {'id': 4, 'class_name': 'kitchen_table', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            {'id': 5, 'class_name': 'bookshelf', 'category': 'Furniture', 'properties': ['SURFACES'], 'states': []},
            
            {'id': 6, 'class_name': 'apple', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 7, 'class_name': 'salmon', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
            {'id': 8, 'class_name': 'book', 'category': 'Items', 'properties': ['GRABBABLE'], 'states': []},
        ],
        'edges': [
            {'from_id': 2, 'to_id': 1, 'relation_type': 'INSIDE'},
            {'from_id': 3, 'to_id': 1, 'relation_type': 'INSIDE'},
            {'from_id': 4, 'to_id': 1, 'relation_type': 'INSIDE'},
            {'from_id': 5, 'to_id': 1, 'relation_type': 'INSIDE'},
            
            {'from_id': 6, 'to_id': 1, 'relation_type': 'INSIDE'},
            {'from_id': 7, 'to_id': 1, 'relation_type': 'INSIDE'},
            {'from_id': 8, 'to_id': 1, 'relation_type': 'INSIDE'},
            
            {'from_id': 6, 'to_id': 4, 'relation_type': 'ON'},
            {'from_id': 7, 'to_id': 4, 'relation_type': 'ON'},
            {'from_id': 8, 'to_id': 4, 'relation_type': 'ON'},
        ]
    }

    name_equivalence = utils.load_name_equivalence()
    current_graph = EnvironmentGraph(copy.deepcopy(graph_dict))

    script_lines = [
        ScriptLine(Action.WALK, [ScriptObject('apple', 6)], 0),
        ScriptLine(Action.GRAB, [ScriptObject('apple', 6)], 0),
        ScriptLine(Action.WALK, [ScriptObject('fridge', 3)], 0),
        ScriptLine(Action.OPEN, [ScriptObject('fridge', 3)], 0),
        ScriptLine(Action.PUTIN, [ScriptObject('apple', 6), ScriptObject('fridge', 3)], 0),
        
        ScriptLine(Action.WALK, [ScriptObject('salmon', 7)], 0),
        ScriptLine(Action.GRAB, [ScriptObject('salmon', 7)], 0),
        ScriptLine(Action.WALK, [ScriptObject('fridge', 3)], 0),
        ScriptLine(Action.PUTIN, [ScriptObject('salmon', 7), ScriptObject('fridge', 3)], 0),
        ScriptLine(Action.CLOSE, [ScriptObject('fridge', 3)], 0),
        
        ScriptLine(Action.WALK, [ScriptObject('book', 8)], 0),
        ScriptLine(Action.GRAB, [ScriptObject('book', 8)], 0),
        ScriptLine(Action.WALK, [ScriptObject('bookshelf', 5)], 0),
        ScriptLine(Action.PUTBACK, [ScriptObject('book', 8), ScriptObject('bookshelf', 5)], 0),
    ]

    print("\n[Debug] 开始逐帧执行与监控...")
    
    is_success = True
    final_raw_dict = None  # 准备存放最后一个成功的纯字典
    
    for i, line in enumerate(script_lines):
        print(f"\n--- 步骤 {i+1} ---")
        print(f"尝试执行: {line}")
        
        executor = ScriptExecutor(current_graph, name_equivalence)
        single_action_script = Script([line])
        
        success, message, state_list = executor.execute(single_action_script)
        
        if not success:
            print(f">>> [失败] 动作在步骤 {i+1} 崩溃！")
            print(f">>> 引擎报错: {message}")
            is_success = False
            break
        else:
            print(">>> 成功。")
            raw_state = state_list[-1]
            final_raw_dict = raw_state  # 记录纯字典
            
            if isinstance(raw_state, dict):
                current_graph = EnvironmentGraph(raw_state)
            else:
                current_graph = raw_state

    if is_success and final_raw_dict is not None:
        print("\n" + "="*60)
        print("[恭喜] 动作序列全部执行成功！提取 State Diff：")
        items_to_track = ['apple', 'salmon', 'book']
        
        for item in items_to_track:
            # 用纯字典函数直接比对初始 graph_dict 和 最终的 final_raw_dict
            init_rel, init_loc = get_item_location_from_dict(graph_dict, item)
            final_rel, final_loc = get_item_location_from_dict(final_raw_dict, item)
            
            if init_loc != final_loc or init_rel != final_rel:
                print(f"[{item}] 从 ({init_rel} {init_loc}) 移动到了 ({final_rel} {final_loc})")
        print("="*60)
        print("你可以把上面的 State Diff 喂给大模型进行意图推理了！")

if __name__ == '__main__':
    run_experiment_debug()