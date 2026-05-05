import time
import os
import collections
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, List, TypeAlias, TypeVar, cast

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
MappedAction: TypeAlias = tuple[int, list[int], set[frozenset[int]], set[int], set[SightLine], set[int], set[int], list[int]]
ExplainPayload: TypeAlias = dict[str, Any]
ActionPayload: TypeAlias = dict[str, Any]


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
        return [(info[0][0], [], empty_aoe_patterns, empty_ints, empty_sightlines, set(), set(), [0])]
    focusdict: dict[tuple[int, ...], set[int]] = collections.defaultdict(set)
    destdict: dict[tuple[int, ...], set[int]] = collections.defaultdict(set)
    aoedict: dict[tuple[int, ...], set[frozenset[int]]] = collections.defaultdict(set)
    raw_indexdict: dict[tuple[int, ...], list[int]] = collections.defaultdict(list)
    for raw_index, iinf in enumerate(info):
        for act in iinf[2]:
            key = (act,) + tuple(sorted(iinf[3]))
            destdict[key].update({iinf[0]})
            focusdict[key].update({iinf[1]})
            aoedict[key].update(iinf[4])
            raw_indexdict[key].append(raw_index)

    solution = list({((act,)+tuple(sorted(iinf[3]))):
                     (act,
                      sorted(list(iinf[3])),
                      aoedict[(act,)+tuple(sorted(iinf[3]))],
                      destdict[(act,)+tuple(sorted(iinf[3]))],
                      iinf[5],
                      debug_lines,
                      focusdict[(act,)+tuple(sorted(iinf[3]))],
                      raw_indexdict[(act,)+tuple(sorted(iinf[3]))])
                     for iinf in info for act in iinf[2]}.values())

    return solution


def build_display_move_stage(move: int, move_options: list[int]) -> ExplainPayload:
    unique_moves = sorted(set(move_options))
    candidates: list[ExplainPayload] = [
        {
            'key': f'end-hex:{location}',
            'label': f'End on hex {location}',
            'location': location,
            'selected': location == move,
        }
        for location in unique_moves
    ]
    if len(unique_moves) == 1:
        summary = 'Only one legal end hex remains for this displayed action.'
        before_count = 1
        after_count = 1
    else:
        summary = f'This displayed action is one of {len(unique_moves)} tied end hexes that remain legal after every rule.'
        before_count = len(unique_moves)
        after_count = 1
    return {
        'id': f'displayed-move-{move}',
        'title': 'Displayed movement option',
        'description': 'The remaining end hexes are still tied after every rule.',
        'summary': summary,
        'before_count': before_count,
        'after_count': after_count,
        'candidates': candidates,
    }


def build_action_explain(
    choice_explain: ExplainPayload | None,
    raw_indices: list[int],
    move: int,
) -> ExplainPayload | None:
    if choice_explain is None:
        return None

    raw_paths = choice_explain.get('actions')
    if not isinstance(raw_paths, list):
        return None

    typed_raw_paths = cast(list[ExplainPayload], raw_paths)
    paths: list[ExplainPayload] = []
    for raw_index in raw_indices:
        if raw_index >= len(typed_raw_paths):
            continue
        raw_path = typed_raw_paths[raw_index]

        move_options_value = raw_path.get('move_options', [move])
        if not isinstance(move_options_value, list):
            move_options = [move]
        else:
            typed_move_options = cast(list[Any], move_options_value)
            move_options = [location for location in typed_move_options if isinstance(location, int)]
            if not move_options:
                move_options = [move]
        stages_value = raw_path.get('stages', [])
        stages = list(cast(list[ExplainPayload], stages_value)) if isinstance(stages_value, list) else []
        stages.append(build_display_move_stage(move, move_options))
        paths.append(
            {
                'label': raw_path.get('label', f'Path {raw_index + 1}'),
                'focus': raw_path.get('focus'),
                'attack_location': raw_path.get('attack_location'),
                'targets': raw_path.get('targets', []),
                'move_options': move_options,
                'selected_move': move,
                'stages': stages,
            }
        )

    if not paths:
        return None

    note: str
    if len(paths) > 1:
        note = f'{len(paths)} equivalent internal paths still lead to this displayed action.'
    elif len(paths[0]['move_options']) > 1:
        note = f'This path still has {len(paths[0]["move_options"])} tied end hexes.'
    else:
        note = 'This displayed action follows a single internal reasoning path.'

    return {
        'path_count': len(paths),
        'current_move': move,
        'note': note,
        'paths': paths,
    }


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

    monster_moves = s.calculate_monster_move()
    choice_explain = s.get_choice_explain()
    raw_actions = map_solution(monster_moves)

    actions: list[ActionPayload] = []
    for raw_action in raw_actions:
        aoe_patterns = list(raw_action[2])
        action: ActionPayload = {
            'move': raw_action[0],
            'attacks': list(raw_action[1]),
            'aoe': list(aoe_patterns[0]) if aoe_patterns else [],
            'destinations': list(raw_action[6]),
            'focuses': list(raw_action[3]),
            'sightlines': list(raw_action[4]),
        }
        action_explain = build_action_explain(choice_explain, raw_action[7], raw_action[0])
        if action_explain is not None:
            action['explain'] = action_explain
        actions.append(action)

    if IsDebugEnv:
        for _, raw_action in enumerate(raw_actions):
            actions[_]['debug_lines'] = list(raw_action[5])

    solution: dict[str, object] = {
        'scenario_id': scenario_id,
        'actions': actions,
    }
    if choice_explain is not None:
        solution['choice_explain'] = {
            'shared_stages': choice_explain.get('shared_stages', []),
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
    solver.explain_choice = scenario.explain_choice

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
    explain_choice: bool = False


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
