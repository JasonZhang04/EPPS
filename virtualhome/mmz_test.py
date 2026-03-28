from virtualhome.simulation.unity_simulator.comm_unity import UnityCommunication

port = "8080"
comm = UnityCommunication(port=port, timeout_wait=120)

try:
    env_id = 0
    res = comm.reset(env_id)
    comm.add_character('Chars/Female1')

    s, g = comm.environment_graph()
    print("Environment loaded, nodes:", len(g['nodes']))

    salmon_id = [node['id'] for node in g['nodes'] if node['class_name'] == 'salmon'][0]
    microwave_id = [node['id'] for node in g['nodes'] if node['class_name'] == 'microwave'][0]
    print(f"salmon id={salmon_id}, microwave id={microwave_id}")

    script = [
        '<char0> [walk] <salmon> ({})'.format(salmon_id),
        '<char0> [grab] <salmon> ({})'.format(salmon_id),
        '<char0> [open] <microwave> ({})'.format(microwave_id),
        '<char0> [putin] <salmon> ({}) <microwave> ({})'.format(salmon_id, microwave_id),
        '<char0> [close] <microwave> ({})'.format(microwave_id)
    ]

    success, message = comm.render_script(
        script,
        recording=True,
        frame_rate=10,
        output_folder='output_video',
        file_name_prefix='salmon_microwave',
        find_solution=True,
    )
    print(f"Success: {success}")
    print(f"Message: {message}")

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    comm.close()
    print("Done")