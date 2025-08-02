import time
import os
import collections
import json
from solver.monster import Monster
from solver.solver import GloomhavenMap, Rule, Solver
from flask import Flask, jsonify, request, render_template
from dataclasses import dataclass
from typing import List
from dacite import from_dict, Config

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
def los() -> str:
    return templates('index.html', params={
        'los_mode': True,
    })


@app.route('/templates/<filename>')
def templates(filename: str, params: dict[str, bool] = {}) -> str:
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


def map_solution(info: list[tuple[int, int, list[int], tuple[int] | tuple[()], list[int], set[tuple[tuple[float, float], tuple[float, float]]]]]) -> list[tuple[int, list[int], list[int], set[int], set[tuple[tuple[float, float], tuple[float, float]]], set[int], set[int]]]:
    debug_lines: set[int] = set()
    if info[0][1] == -1:
        return list({((info[0][0],)): (info[0][0], [], [], set(), set(), set(), set())}.values())
    focusdict: dict[tuple[int] | tuple[int, int],
                    set[int]] = collections.defaultdict(set)
    destdict: dict[tuple[int] | tuple[int, int],
                   set[int]] = collections.defaultdict(set)
    aoedict: dict[tuple[int] | tuple[int, int],
                  set[int]] = collections.defaultdict(set)
    for iinf in info:
        for act in iinf[2]:
            destdict[(act,)+tuple(sorted(iinf[3]))].update({iinf[0]})
            focusdict[(act,)+tuple(sorted(iinf[3]))].update({iinf[1]})
            aoedict[(act,)+tuple(sorted(iinf[3]))].update(iinf[4])

    solution = list({((act,)+tuple(sorted(iinf[3]))):
                     (act,
                      sorted(list(iinf[3])),
                      aoedict[(act,)+tuple(sorted(iinf[3]))],
                      destdict[(act,)+tuple(sorted(iinf[3]))],
                      iinf[5],
                      debug_lines,
                      focusdict[(act,)+tuple(sorted(iinf[3]))])
                     for iinf in info for act in iinf[2]}.values())

    return solution


@app.route('/solve', methods=['PUT'])
def solve():

    (s, solve_reach, solve_sight, scenario_id,
     start_location) = unpack_scenario(request.data)
    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    raw_actions = map_solution(s.calculate_monster_move())

    actions = [
        {
            'move': raw_action[0],
            'attacks': list(raw_action[1]),
            'aoe': list(list(raw_action[2])[0])if len(list(raw_action[2])) > 0 else list(),
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
    if solve_reach:
        solution['reach'] = s.solve_reaches(moves)
    if solve_sight:
        solution['sight'] = s.solve_sights(moves)

    # if IsDebugEnv:
    #   print(solution)
    return jsonify(solution)


def unpack_scenario(data: bytes) -> tuple['Solver', bool, bool, int, int]:
    scenario = from_dict(ScenarioData, json.loads(
        data), Config(cast=[int, str], strict=True))

    # Build AOE, monster, and grids
    aoe = [False] * 49
    for pos in scenario.aoe:
        if pos != 24 or scenario.range > 0:  # center = (7*7 - 1) // 2
            aoe[pos] = True

    monster = Monster(scenario.move, scenario.range, scenario.target,
                      scenario.flying == 2, scenario.flying == 1, scenario.muddled == 1,
                      aoe, scenario.teleport == 1)

    total_cells = scenario.width * scenario.height
    figures = [' '] * total_cells
    contents = [' '] * total_cells
    initiatives = [0] * total_cells

    # Populate all grids using dictionary mapping
    content_map = {'walls': 'X', 'obstacles': 'O', 'traps': 'T','hazardous': 'H', 'difficult': 'D', 'icy': 'I'}
    figure_map = {'characters': 'C', 'monsters': 'M'}

    for attr, char in content_map.items():
        for pos in getattr(scenario.map, attr):
            contents[pos] = char

    for attr, char in figure_map.items():
        for pos in getattr(scenario.map, attr):
            figures[pos] = char

    # Handle active figure and faction switching
    if figures[scenario.active_figure] == 'C':
        figures = ['M' if f == 'C' else 'C' if f == 'M' else f for f in figures]
        victims = scenario.map.monsters
    else:
        figures[scenario.active_figure] = 'A'
        victims = scenario.map.characters

    # Build walls
    walls = [[False] * 6 for _ in range(total_cells)]
    for wall_pos, wall_dir in scenario.map.thin_walls:
        walls[wall_pos][{1: 0, 0: 1, 2: 5}[wall_dir]] = True

    for initiative, victim_pos in zip(scenario.map.initiatives, victims):
        initiatives[victim_pos] = int(initiative)

    # Create solver and return
    rule_obj = Rule(int(scenario.game_rules))
    gmap = GloomhavenMap(scenario.width, scenario.height, monster, figures,
                         contents, initiatives, walls, rule_obj)
    solver = Solver(rule_obj, gmap)
    solver.debug_toggle = scenario.debug_toggle == '0'

    return solver, scenario.solve_view > 0, scenario.solve_view > 0, scenario.scenario_id, scenario.active_figure


@app.route('/views', methods=['PUT'])
def views():

    (s, solve_reach, solve_sight, scenario_id,
     viewpoints) = unpack_scenario_forviews(request.data)

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    solution: dict[str,
                   list[list[tuple[int, int]]] |
                   int] = {
        'scenario_id': scenario_id,
    }

    if solve_reach:
        solution['reach'] = s.solve_reaches(viewpoints)
    if solve_sight:
        solution['sight'] = s.solve_sights(viewpoints)

    # if IsDebugEnv:
        # print solution
    return jsonify(solution)


def unpack_scenario_forviews(data: bytes) -> tuple['Solver', bool, bool, int, list[int]]:
    # if IsDebugEnv:
    #   print packed_scenario

    # todo: validate packed scenario format
    packed_scenario = json.loads(data)
    action_rang = int(packed_scenario['range'])
    action_targe = int(packed_scenario['target'])
    monster = Monster(action_range=action_rang, action_target=action_targe)
    rule = int(packed_scenario.get('game_rules', '0'))

    solve_view = packed_scenario['solve_view']

    contents = ['X' if i in packed_scenario['map']['walls'] else ' ' for i in range(
        packed_scenario['width']*packed_scenario['height'])]

    remap = {
        1: 0,
        0: 1,
        2: 5,
    }

    walls: list[list[bool]] = [
        [False] * 6 for _ in range(packed_scenario['width']*packed_scenario['height'])]
    for _ in packed_scenario['map']['thin_walls']:
        walls[_[0]][remap[_[1]]] = True
    gmap = GloomhavenMap(packed_scenario['width'], packed_scenario['height'], monster, [
    ], contents, [], walls,  Rule(rule))
    s = Solver(Rule(rule), gmap)
    return (s, solve_view > 0, solve_view > 0, packed_scenario['scenario_id'], packed_scenario['viewpoints'])


@dataclass(frozen=True)
class MapData:
    walls: List[int]
    obstacles: List[int]
    traps: List[int]
    hazardous: List[int]
    difficult: List[int]
    icy: List[int]
    characters: List[int]
    monsters: List[int]
    thin_walls: List[List[int]]
    initiatives: List[int]


@dataclass(frozen=True)
class ScenarioData:
    width: int
    height: int
    solve_view: int
    move: int
    range: int
    target: int
    flying: int
    muddled: int
    teleport: int
    aoe: List[int]
    map: MapData
    active_figure: int
    scenario_id: int
    game_rules: str = "0"
    debug_toggle: str = "0"
