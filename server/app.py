import time
import os
import collections
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import List, TypeVar

from dacite import Config, from_dict
from dacite.exceptions import DaciteError
from flask import Flask, jsonify, request, render_template

from solver.monster import Monster
from solver.solver import GloomhavenMap, MonsterMove, Rule, Solver

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

ScenarioDataT = TypeVar('ScenarioDataT')
SightLine = tuple[tuple[float, float], tuple[float, float]]
MappedAction = tuple[int, list[int], set[frozenset[int]], set[int], set[SightLine], set[int], set[int]]


class InvalidScenarioError(ValueError):
    pass

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


def templates(filename: str, params: dict[str, bool] | None = None) -> str:
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
        **(params or {})
    )


def unpack_payload(data: bytes, schema: type[ScenarioDataT]) -> ScenarioDataT:
    try:
        return from_dict(schema, json.loads(data), Config(cast=[int, str], strict=True))
    except (DaciteError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise InvalidScenarioError('invalid scenario payload') from exc


def validate_positions(total_cells: int, positions: list[int], label: str) -> None:
    if any(not 0 <= pos < total_cells for pos in positions):
        raise InvalidScenarioError(f'{label} contains out-of-bounds locations')


def map_thin_walls(total_cells: int, thin_walls: list[list[int]]) -> list[list[bool]]:
    remap = {
        1: 0,
        0: 1,
        2: 5,
    }
    walls = [[False] * 6 for _ in range(total_cells)]
    for wall_pos, wall_dir in thin_walls:
        if not 0 <= wall_pos < total_cells:
            raise InvalidScenarioError('thin_walls contains out-of-bounds locations')
        if wall_dir not in remap:
            raise InvalidScenarioError('thin_walls contains an invalid direction')
        walls[wall_pos][remap[wall_dir]] = True
    return walls


def map_solution(info: Sequence[MonsterMove]) -> list[MappedAction]:
    debug_lines: set[int] = set()
    if info[0][1] == -1:
        empty_aoe_patterns: set[frozenset[int]] = set()
        empty_ints: set[int] = set()
        empty_sightlines: set[SightLine] = set()
        return [(info[0][0], [], empty_aoe_patterns, empty_ints, empty_sightlines, set(), set())]
    focusdict: dict[tuple[int, ...], set[int]] = collections.defaultdict(set)
    destdict: dict[tuple[int, ...], set[int]] = collections.defaultdict(set)
    aoedict: dict[tuple[int, ...], set[frozenset[int]]] = collections.defaultdict(set)
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

    try:
        (s, solve_reach, solve_sight, scenario_id,
         _start_location) = unpack_scenario(request.data)
    except InvalidScenarioError as exc:
        return jsonify({'error': str(exc)}), 400

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    raw_actions = map_solution(s.calculate_monster_move())

    actions: list[dict[str, int | list[int] | list[SightLine]]] = []
    for raw_action in raw_actions:
        aoe_patterns = list(raw_action[2])
        actions.append(
            {
                'move': raw_action[0],
                'attacks': list(raw_action[1]),
                'aoe': list(aoe_patterns[0]) if aoe_patterns else [],
                'destinations': list(raw_action[6]),
                'focuses': list(raw_action[3]),
                'sightlines': list(raw_action[4]),
            }
        )

    if IsDebugEnv:
        for _, raw_action in enumerate(raw_actions):
            actions[_]['debug_lines'] = list(raw_action[5])

    solution: dict[str, object] = {
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
    scenario = unpack_payload(data, ScenarioData)

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
    if not 0 <= scenario.active_figure < total_cells:
        raise InvalidScenarioError('active_figure is out of bounds')

    # Populate all grids using dictionary mapping
    content_map = {'walls': 'X', 'obstacles': 'O', 'traps': 'T','hazardous': 'H', 'difficult': 'D', 'icy': 'I'}
    figure_map = {'characters': 'C', 'monsters': 'M'}

    for attr, char in content_map.items():
        positions = getattr(scenario.map, attr)
        validate_positions(total_cells, positions, attr)
        for pos in positions:
            contents[pos] = char

    for attr, char in figure_map.items():
        positions = getattr(scenario.map, attr)
        validate_positions(total_cells, positions, attr)
        for pos in positions:
            figures[pos] = char

    if figures[scenario.active_figure] not in {'C', 'M'}:
        raise InvalidScenarioError('active_figure must refer to a character or monster')

    # Handle active figure and faction switching
    if figures[scenario.active_figure] == 'C':
        figures = ['M' if f == 'C' else 'C' if f == 'M' else f for f in figures]
        figures[scenario.active_figure] = 'A'
        victims = scenario.map.monsters
    else:
        figures[scenario.active_figure] = 'A'
        victims = scenario.map.characters

    # Build walls
    walls = map_thin_walls(total_cells, scenario.map.thin_walls)

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

    try:
        (s, solve_reach, solve_sight, scenario_id,
         viewpoints) = unpack_scenario_forviews(request.data)
    except InvalidScenarioError as exc:
        return jsonify({'error': str(exc)}), 400

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    solution: dict[str, object] = {
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
    scenario = unpack_payload(data, ViewScenarioData)
    total_cells = scenario.width * scenario.height
    validate_positions(total_cells, scenario.map.walls, 'walls')
    validate_positions(total_cells, scenario.viewpoints, 'viewpoints')

    monster = Monster(action_range=scenario.range, action_target=scenario.target)
    contents = ['X' if i in scenario.map.walls else ' ' for i in range(total_cells)]
    walls = map_thin_walls(total_cells, scenario.map.thin_walls)
    rule = Rule(int(scenario.game_rules))
    gmap = GloomhavenMap(scenario.width, scenario.height, monster, [], contents, [], walls, rule)
    s = Solver(rule, gmap)
    return (s, scenario.solve_view > 0, scenario.solve_view > 0, scenario.scenario_id, scenario.viewpoints)


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


@dataclass(frozen=True)
class ViewMapData:
    walls: List[int]
    thin_walls: List[List[int]]


@dataclass(frozen=True)
class ViewScenarioData:
    width: int
    height: int
    solve_view: int
    range: int
    target: int
    map: ViewMapData
    viewpoints: List[int]
    scenario_id: int
    game_rules: str = "0"
