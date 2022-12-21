import time
import os
import collections
import json
from solver.monster import Monster
from solver.solver import GloomhavenMap, Rule, Solver
from flask import Flask, jsonify, request, render_template

app = Flask(__name__, static_folder='../static/dist',
            template_folder='../static')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Configuration
IsDebugEnv = os.environ.get('FLASK_DEBUG') == "1"

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

def map_solution(info: list[tuple[int,int,list[int],tuple[int] | tuple[()],list[int],set[tuple[tuple[float, float], tuple[float, float]]]]])->list[tuple[int, list[int], list[int], set[int], set[tuple[tuple[float, float], tuple[float, float]]], set[int], set[int]]]:
        debug_lines:set[int] = set()
        if info[0][1] ==-1:
            return list({((info[0][0],)):(info[0][0],[],[],set(),set(),set(),set())}.values())
        focusdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        destdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)        
        aoedict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        for iinf in info:
            for act in iinf[2]:
                destdict[(act,)+iinf[3]].update({iinf[0]})
                focusdict[(act,)+iinf[3]].update({iinf[1]})
                aoedict[(act,)+iinf[3]].add(frozenset(iinf[4]))
   
        solution = list({((act,)+iinf[3]):
            (act,
            list(iinf[3]),
            aoedict[(act,)+iinf[3]],
            destdict[(act,)+iinf[3]],
            iinf[5],
            debug_lines,
            focusdict[(act,)+iinf[3]])
            for iinf in info for act in iinf[2]}.values())
            
        return solution


@app.route('/solve', methods=['PUT'])
def solve():

    (s,solve_reach,solve_sight,scenario_id,start_location)=unpack_scenario(request.data)
    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    raw_actions= map_solution(s.calculate_monster_move())


    actions = [
        {
            'move': raw_action[0],
            'attacks': list(raw_action[1]),
            'aoe': list(list(raw_action[2])[0]),
            'destinations': list(raw_action[6]),
            'focuses': list(raw_action[3]),
            'sightlines': list(raw_action[4]),
        }
        for raw_action in raw_actions
    ]

    if IsDebugEnv:
        for _, raw_action in enumerate(raw_actions):
            actions[_]['debug_lines'] = list(raw_action[5])

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

def unpack_scenario(data: bytes) -> tuple['Solver', bool, bool,int,int]:
    
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    packed_scenario = json.loads(data)
    map_width = packed_scenario['width']
    map_height = packed_scenario['height']
    solve_view = packed_scenario['solve_view']

    aoe=[False]*49
    action_move = int(packed_scenario['move'])
    action_range = int(packed_scenario['range'])
    action_target = int(packed_scenario['target'])
    jumping = int(packed_scenario['flying']) == 1
    flying = int(packed_scenario['flying']) == 2
    muddled = int(packed_scenario['muddled']) == 1

    for _ in packed_scenario['aoe']:
        if _ != (7*7 - 1) // 2 or action_range > 0:
            aoe[_] = True

    monster = Monster(action_move,action_range,action_target,flying,jumping,muddled,aoe)
    rule = int(packed_scenario.get('game_rules', '0'))




    figures:list[str] = [' '] * packed_scenario['width']*packed_scenario['height']
    initiatives:list[int] = [0] *packed_scenario['width']*packed_scenario['height']
    contents:list[str] = [' '] * packed_scenario['width']*packed_scenario['height']
    def add_elements(grid:list[str], key:str, content:str):
        for _ in packed_scenario['map'][key]:
            grid[_] = content

    add_elements(contents, 'walls', 'X')
    add_elements(contents, 'obstacles', 'O')
    add_elements(contents, 'traps', 'T')
    add_elements(contents, 'hazardous', 'H')
    add_elements(contents, 'difficult', 'D')
    add_elements(figures, 'characters', 'C')
    add_elements(figures, 'monsters', 'M')

    active_figure_location = packed_scenario['active_figure']
    switch_factions = figures[active_figure_location] == 'C'
    figures[active_figure_location] = 'A'

    if switch_factions:
        for _ in range(packed_scenario['width']*packed_scenario['height']):
            if figures[_] == 'C':
                figures[_] = 'M'
            elif figures[_] == 'M':
                figures[_] = 'C'


    remap = {
        1: 0,
        0: 1,
        2: 5,
    }

    walls:list[list[bool]] = [[False] * 6 for _ in range(packed_scenario['width']*packed_scenario['height'])]
    for _ in packed_scenario['map']['thin_walls']:
        walls[_[0]][remap[_[1]]] = True

    if switch_factions:
        victims = packed_scenario['map']['monsters']
    else:
        victims = packed_scenario['map']['characters']

    for i, j in zip(packed_scenario['map']['initiatives'], victims):
        initiatives[j] = int(i)

    gmap = GloomhavenMap(packed_scenario['width'], packed_scenario['height'], monster,figures,contents, initiatives,walls,  Rule(rule)) 
    s = Solver(Rule(rule),gmap)
    s.debug_toggle = bool(packed_scenario.get('debug_toggle', '0'))
    return (s,solve_view > 0,solve_view > 0,packed_scenario['scenario_id'],active_figure_location)

@app.route('/views', methods=['PUT'])
def views():

    (s,solve_reach,solve_sight,scenario_id,viewpoints)=unpack_scenario_forviews(request.data)

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

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

def unpack_scenario_forviews(data: bytes) ->  tuple['Solver', bool, bool,int,list[int]]:
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    packed_scenario = json.loads(data)
    action_rang = int(packed_scenario['range'])
    action_targe = int(packed_scenario['target'])
    monster = Monster(action_range=action_rang, action_target=action_targe)
    rule = int(packed_scenario.get('game_rules', '0'))

   

    solve_view = packed_scenario['solve_view']

    contents = ['X' if i in packed_scenario['map']['walls'] else ' ' for i in range(packed_scenario['width']*packed_scenario['height'])]

    remap = {
        1: 0,
        0: 1,
        2: 5,
    }

    walls:list[list[bool]] = [[False] * 6 for _ in range(packed_scenario['width']*packed_scenario['height'])]
    for _ in packed_scenario['map']['thin_walls']:
        walls[_[0]][remap[_[1]]] = True
    gmap = GloomhavenMap(packed_scenario['width'], packed_scenario['height'], monster,[],contents, [],walls,  Rule(rule)) 
    s = Solver(Rule(rule),gmap)
    return (s,solve_view > 0,solve_view > 0,packed_scenario['scenario_id'], packed_scenario['viewpoints'])