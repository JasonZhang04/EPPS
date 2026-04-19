import time
import subprocess
import traceback
from virtualhome.simulation.unity_simulator.comm_unity import UnityCommunication

# 1. Auto-Start the Unity Executable
exec_path = r"D:\Users\lenovo\Desktop\EPPS\virtualhome\virtualhome\simulation\unity_simulator\windows_exec.v2.3.0\VirtualHome.exe"
print(f"[Setup] Starting Unity Executable at {exec_path}...")
unity_process = subprocess.Popen([exec_path, "-batchmode"]) 
time.sleep(10) # Give Unity 10 seconds to spin up the server

port = "8080"
comm = UnityCommunication(port=port, timeout_wait=120)

try:
    print("[Setup] Connecting to Environment...")
    env_id = 0 # Standard apartment
    comm.reset(env_id)
    comm.add_character('Chars/Female1')
    
    # 2. Add a Fixed Camera for a consistent third-person view
    # This places a camera high up in the kitchen corner looking down
    comm.add_camera(position=[-2.0, 2.5, 0.0], rotation=[30, 90, 0])

    # 3. Get Environment Node IDs dynamically
    s, g = comm.environment_graph()
    
    def get_id(class_name):
        nodes = [n['id'] for n in g['nodes'] if n['class_name'] == class_name]
        return nodes[0] if nodes else None

    # Find the items that actually exist in Unity Scene 0
    fridge = get_id('fridge')
    apple = get_id('apple')
    pie = get_id('pie') # Using pie instead of salmon if salmon isn't in scene 0
    sink = get_id('sink')
    waterglass = get_id('waterglass')
    cellphone = get_id('cellphone')
    sofa = get_id('sofa')

    print("[Simulation] Generating Noisy 3D Unpacking Routine...")
    
    # Translate our EPPS logic to VirtualHome String Commands
    script = [
        # Signal: Groceries to Fridge
        f'<char0> [walk] <apple> ({apple})',
        f'<char0> [grab] <apple> ({apple})',
        f'<char0> [walk] <fridge> ({fridge})',
        f'<char0> [open] <fridge> ({fridge})',
        f'<char0> [putin] <apple> ({apple}) <fridge> ({fridge})',
        
        f'<char0> [walk] <pie> ({pie})',
        f'<char0> [grab] <pie> ({pie})',
        f'<char0> [walk] <fridge> ({fridge})',
        f'<char0> [putin] <pie> ({pie}) <fridge> ({fridge})',
        f'<char0> [close] <fridge> ({fridge})',
        
        # Noise: Move waterglass to sink
        f'<char0> [walk] <waterglass> ({waterglass})',
        f'<char0> [grab] <waterglass> ({waterglass})',
        f'<char0> [walk] <sink> ({sink})',
        f'<char0> [putback] <waterglass> ({waterglass}) <sink> ({sink})',
        
        # Transient: Grab phone, walk to sofa (Held Item)
        f'<char0> [walk] <cellphone> ({cellphone})',
        f'<char0> [grab] <cellphone> ({cellphone})',
        f'<char0> [walk] <sofa> ({sofa})'
    ]

    # 4. Render the Script to Images
    success, message = comm.render_script(
        script,
        recording=True,
        frame_rate=5, # 5 FPS is plenty for a VLM, keeps data size low
        camera_mode=["FIRST_PERSON", "FIXED"], # Captures both views
        output_folder='epps_video_output',
        file_name_prefix='unpacking_noisy',
        find_solution=True,
    )
    print(f"Render Success: {success}")

except Exception as e:
    traceback.print_exc()
finally:
    comm.close()
    unity_process.terminate() # Kill the background Unity process
    print("Simulation Closed.")