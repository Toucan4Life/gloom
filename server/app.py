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

    (s,solve_reach,solve_sight,scenario_id,start_location)=unpack_scenario(request.data)
    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True
    s.prepare_map()

    raw_actions, aoes, destinations, focuses, sightlines, debug_lines = s.calculate_monster_move()

    if IsDebugEnv:
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

    solution: dict[str,
                   list[list[tuple[int, int]]] |
                   int | 
                   list[dict[str,
                            int |
                            list[int] |
                            list[tuple[tuple[float, float], tuple[tuple[float, float]]]]]]] = {
        'scenario_id': scenario_id,
        'actions': actions,
    }
    moves = list((raw_action[0] for raw_action in raw_actions))
    if solve_reach :
        solution['reach'] = s.solve_reaches(moves)
    if solve_sight :
        solution['sight'] = s.solve_sights(moves)

    # if IsDebugEnv:
    #   print(solution)
    return jsonify(solution)

def unpack_scenario(data: bytes) -> tuple['Scenario', bool, bool,int,int]:
    
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    packed_scenario = json.loads(data)
    map_width = packed_scenario['width']
    map_height = packed_scenario['height']
    solve_view = packed_scenario['solve_view']
    s = Scenario(map_width, map_height, 7, 7)
    s.action_move = int(packed_scenario['move'])
    s.action_range = int(packed_scenario['range'])
    s.action_target = int(packed_scenario['target'])
    s.jumping = int(packed_scenario['flying']) == 1
    s.flying = int(packed_scenario['flying']) == 2
    s.muddled = int(packed_scenario['muddled']) == 1

    s.set_rules(int(packed_scenario.get('game_rules', '0')))

    s.debug_toggle = bool(packed_scenario.get('debug_toggle', '0'))

    def add_elements(grid:list[str], key:str, content:str):
        for _ in packed_scenario['map'][key]:
            grid[_] = content

    add_elements(s.contents, 'walls', 'X')
    add_elements(s.contents, 'obstacles', 'O')
    add_elements(s.contents, 'traps', 'T')
    add_elements(s.contents, 'hazardous', 'H')
    add_elements(s.contents, 'difficult', 'D')
    add_elements(s.figures, 'characters', 'C')
    add_elements(s.figures, 'monsters', 'M')

    active_figure_location = packed_scenario['active_figure']
    switch_factions = s.figures[active_figure_location] == 'C'
    s.figures[active_figure_location] = 'A'

    if switch_factions:
        for _ in range(s.map.map_size):
            if s.figures[_] == 'C':
                s.figures[_] = 'M'
            elif s.figures[_] == 'M':
                s.figures[_] = 'C'

    for _ in packed_scenario['aoe']:
        if _ != s.aoe_center or s.action_range > 0:
            s.aoe[_] = True

    remap = {
        1: 0,
        0: 1,
        2: 5,
    }
    for _ in packed_scenario['map']['thin_walls']:
        ss = remap[_[1]]
        s.walls[_[0]][ss] = True

    if switch_factions:
        victims = packed_scenario['map']['monsters']
    else:
        victims = packed_scenario['map']['characters']

    for i, j in zip(packed_scenario['map']['initiatives'], victims):
        s.initiatives[j] = int(i)
    return (s,solve_view > 0,solve_view > 0,packed_scenario['scenario_id'],active_figure_location)

@app.route('/views', methods=['PUT'])
def views():

    (s,solve_reach,solve_sight,scenario_id,viewpoints)=unpack_scenario_forviews(request.data)

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True
    
    s.prepare_map()
    solution: dict[str,
                   list[list[tuple[int, int]]] |
                   int] = {
        'scenario_id': scenario_id,
    }

    if solve_reach :
        solution['reach'] = s.solve_reaches(viewpoints)
    if solve_sight :
        solution['sight'] = s.solve_sights(viewpoints)

    # if IsDebugEnv:
        # print solution
    return jsonify(solution)

def unpack_scenario_forviews(data: bytes) ->  tuple['Scenario', bool, bool,int,list[int]]:
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    packed_scenario = json.loads(data)
    s = Scenario(packed_scenario['width'], packed_scenario['height'], 7, 7)
    s.action_range = int(packed_scenario['range'])
    s.action_target = int(packed_scenario['target'])
    solve_view = packed_scenario['solve_view']
    s.set_rules(int(packed_scenario.get('game_rules', '0')))

    def add_elements(grid:list[str], key:str, content:str):
        for _ in packed_scenario['map'][key]:
            grid[_] = content

    add_elements(s.contents, 'walls', 'X')

    remap = {
        1: 0,
        0: 1,
        2: 5,
    }
    for _ in packed_scenario['map']['thin_walls']:
        ss = remap[_[1]]
        s.walls[_[0]][ss] = True

    return (s,solve_view > 0,solve_view > 0,packed_scenario['scenario_id'], packed_scenario['viewpoints'])