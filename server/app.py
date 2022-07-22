import time
import os
import json
from solver.solver import Scenario
from flask import Flask, jsonify, request, render_template

app = Flask(__name__, static_folder='../static/dist',
            template_folder='../static')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Configuration
IsDebugEnv = os.environ.get('FLASK_ENV') == "development"

title = 'Gloomhaven Monster Mover'
version_major = 2
version_minor = 7
version_build = 1
version = str(version_major) + '.' + \
    str(version_minor) + '.' + str(version_build)
client_local_storage_version_major = 1
client_local_storage_version_minor = 3
client_local_storage_version_build = 0
client_local_storage_version = str(client_local_storage_version_major) + '.' + str(
    client_local_storage_version_minor) + '.' + str(client_local_storage_version_build)

# Routes
@app.route('/isAlive')
def isAlive():
    return jsonify("ok")

@app.route('/')
def root():
    return templates('index.html')


@app.route('/los')
def los()->str:
    return templates('index.html', params={
        'los_mode': True,
    })


@app.route('/templates/<filename>')
def templates(filename:str, params:dict[str,bool]={})->str:
    template_version = version
    if IsDebugEnv:
        template_version += '.' + str(time.time())

    return render_template(
        filename,
        debug_server=IsDebugEnv,
        title=title,
        version=template_version,
        client_local_storage_version=client_local_storage_version,
        client_local_storage_version_major=client_local_storage_version_major,
        client_local_storage_version_minor=client_local_storage_version_minor,
        client_local_storage_version_build=client_local_storage_version_build,
        **params
    )


@app.route('/solve', methods=['PUT'])
def solve():
    packed_scenario = json.loads(request.data)
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    map_width = packed_scenario['width']
    map_height = packed_scenario['height']

    s = Scenario(map_width, map_height, 7, 7)

    s.unpack_scenario(packed_scenario)

    raw_actions, aoes, destinations, focuses, sightlines, debug_lines = s.calculate_monster_move()

    if IsDebugEnv:
        start_location = s.figures.index('A')
        print(f'{len(raw_actions)} option(s):')
        for raw_action in raw_actions:
            if raw_action[0] == start_location:
                out = '- no movement'
            else:
                out = f'- move to {raw_action[0]}'
            if raw_action[1:]:                
                for attack in raw_action[1:]:
                    out += f', attack {attack}'
            print(out)

    actions = [
        {
            'move': raw_action[0],
            'attacks': list(raw_action[1:]),
            'aoe': list(aoes[raw_action]),
            'destinations': list(destinations[raw_action]),
            'focuses': list(focuses[raw_action]),
            'sightlines': list(sightlines[raw_action]),
        }
        for raw_action in raw_actions
    ]

    if IsDebugEnv:
        for _, raw_action in enumerate(raw_actions):
            actions[_]['debug_lines'] = list(debug_lines[raw_action])  

    solution = {
        'scenario_id': packed_scenario['scenario_id'],
        'actions': actions,
    }
    moves = list((raw_action[0] for raw_action in raw_actions))
    solve_view = packed_scenario['solve_view']
    if solve_view > 0:
        solution['reach'] = s.solve_reaches(moves)
    if solve_view > 1:
        solution['sight'] = s.solve_sights(moves)

    # if IsDebugEnv:
    #   print(solution)
    return jsonify(solution)


@app.route('/views', methods=['PUT'])
def views():
    packed_scenario = json.loads(request.data)
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    map_width = packed_scenario['width']
    map_height = packed_scenario['height']
    viewpoints = packed_scenario['viewpoints']
    

    s = Scenario(map_width, map_height, 7, 7)
    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True
    s.unpack_scenario_forviews(packed_scenario)

    solution = {
        'scenario_id': packed_scenario['scenario_id'],
    }
    solve_view = packed_scenario['solve_view']
    if solve_view > 0:
        solution['reach'] = s.solve_reaches(viewpoints)
    if solve_view > 1:
        solution['sight'] = s.solve_sights(viewpoints)

    # if IsDebugEnv:
        # print solution
    return jsonify(solution)