"""Pure Python solve/views API, with no Flask dependency.

This module contains the actual scenario-unpacking and solving logic used by
the Flask app's /solve and /views routes. It is kept free of any web
framework or third-party dependency so it can also be imported and run
inside Pyodide (WebAssembly Python running in the browser) for the GitHub
Pages build, without needing a server or network access to fetch extra
packages at runtime.
"""
import collections
import dataclasses
import enum
import json
import typing
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, List, TypeVar, cast

from solver.monster import Monster
from solver.solver import GloomhavenMap, MonsterMove, Rule, Solver

IsDebugEnv = False


def set_debug_env(is_debug: bool) -> None:
    """Toggle debug logging/visuals for solve_scenario/solve_views.

    Exposed as an explicit function (rather than letting callers poke the
    module attribute directly) because this module doubles as the entry
    point invoked from Pyodide in the browser build, where there is no
    Flask app to hold this setting instead.
    """
    global IsDebugEnv  # pylint: disable=global-statement
    IsDebugEnv = is_debug

ScenarioDataT = TypeVar('ScenarioDataT')
SightLine = tuple[tuple[float, float], tuple[float, float]]
MappedAction = tuple[int, list[int], set[frozenset[int]], set[int], set[SightLine], set[int], set[int]]


class InvalidScenarioError(ValueError):
    pass


def _cast_value(value: object, field_type: object) -> object:
    origin = typing.get_origin(field_type)
    if origin is list:
        if not isinstance(value, list):
            raise InvalidScenarioError('expected a list')
        value_list = cast(list[object], value)
        item_types = typing.get_args(field_type)
        item_type = item_types[0] if item_types else object
        return [_cast_value(item, item_type) for item in value_list]
    if isinstance(field_type, type) and dataclasses.is_dataclass(field_type):
        return _build_dataclass(field_type, value)
    if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
        try:
            return field_type(int(cast(Any, value)))
        except (TypeError, ValueError) as exc:
            raise InvalidScenarioError(f'invalid {field_type.__name__} value: {value!r}') from exc
    if field_type is int:
        return int(cast(Any, value))
    if field_type is str:
        return str(value)
    return value


def _build_dataclass(schema: type[ScenarioDataT], data: object) -> ScenarioDataT:
    if not isinstance(data, dict):
        raise InvalidScenarioError('invalid scenario payload')

    raw_payload = cast(dict[object, object], data)
    if not all(isinstance(name, str) for name in raw_payload):
        raise InvalidScenarioError('invalid scenario payload')

    payload = cast(dict[str, object], raw_payload)
    field_defs = {field.name: field for field in dataclasses.fields(cast(Any, schema))}
    field_types = typing.get_type_hints(schema)
    unknown_fields = set(payload) - set(field_defs)
    if unknown_fields:
        raise InvalidScenarioError(f'unexpected fields: {sorted(unknown_fields)}')

    kwargs: dict[str, object] = {}
    for name, field in field_defs.items():
        if name in payload:
            kwargs[name] = _cast_value(payload[name], field_types.get(name, object))
        elif field.default is dataclasses.MISSING:
            raise InvalidScenarioError(f'missing field: {name}')

    return schema(**kwargs)


def unpack_payload(data: bytes, schema: type[ScenarioDataT]) -> ScenarioDataT:
    try:
        return _build_dataclass(schema, json.loads(data))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
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
    actions: dict[tuple[int, ...], MappedAction] = {}
    for iinf in info:
        sorted_targets = sorted(iinf[3])
        key_suffix = tuple(sorted_targets)
        for act in iinf[2]:
            key = (act,) + key_suffix
            destdict[key].add(iinf[0])
            focusdict[key].add(iinf[1])
            aoedict[key].update(iinf[4])
            # aoedict/destdict/focusdict values are shared set objects, so later
            # updates for this key are still visible through the stored tuple.
            actions[key] = (act, sorted_targets, aoedict[key], destdict[key], iinf[5], debug_lines, focusdict[key])

    return list(actions.values())


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
    game_rules: Rule = Rule.Frost
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
    game_rules: Rule = Rule.Frost


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

    for grid, mapping in ((contents, content_map), (figures, figure_map)):
        for attr, char in mapping.items():
            positions = getattr(scenario.map, attr)
            validate_positions(total_cells, positions, attr)
            for pos in positions:
                grid[pos] = char

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
    gmap = GloomhavenMap(scenario.width, scenario.height, monster, figures,
                         contents, initiatives, walls, scenario.game_rules)
    solver = Solver(scenario.game_rules, gmap)
    solver.debug_toggle = scenario.debug_toggle == '0'

    return solver, scenario.solve_view > 0, scenario.solve_view > 0, scenario.scenario_id, scenario.active_figure


def unpack_scenario_forviews(data: bytes) -> tuple['Solver', bool, bool, int, list[int]]:
    scenario = unpack_payload(data, ViewScenarioData)
    total_cells = scenario.width * scenario.height
    validate_positions(total_cells, scenario.map.walls, 'walls')
    validate_positions(total_cells, scenario.viewpoints, 'viewpoints')

    monster = Monster(action_range=scenario.range, action_target=scenario.target)
    contents = ['X' if i in scenario.map.walls else ' ' for i in range(total_cells)]
    walls = map_thin_walls(total_cells, scenario.map.thin_walls)
    gmap = GloomhavenMap(scenario.width, scenario.height, monster, [], contents, [], walls, scenario.game_rules)
    s = Solver(scenario.game_rules, gmap)
    return (s, scenario.solve_view > 0, scenario.solve_view > 0, scenario.scenario_id, scenario.viewpoints)


def solve_scenario(data: bytes) -> dict[str, object]:
    """Solve a monster's move/attack for the given scenario payload.

    Raises InvalidScenarioError on bad input. Returns a JSON-serializable dict
    with the same shape previously produced by the Flask /solve route.
    """
    (s, solve_reach, solve_sight, scenario_id,
     _start_location) = unpack_scenario(data)

    if IsDebugEnv:
        s.logging = True
        s.debug_visuals = True

    raw_actions = map_solution(s.calculate_monster_move())

    actions: list[dict[str, int | list[int] | list[SightLine]]] = []
    for raw_action in raw_actions:
        aoe_pattern = next(iter(raw_action[2]), cast(frozenset[int], frozenset()))
        actions.append(
            {
                'move': raw_action[0],
                'attacks': list(raw_action[1]),
                'aoe': list(aoe_pattern),
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
        'explanation': s.explanation,
    }
    moves = [raw_action[0] for raw_action in raw_actions]
    if solve_reach:
        solution['reach'] = s.solve_reaches(moves)
    if solve_sight:
        solution['sight'] = s.solve_sights(moves)

    return solution


def solve_views(data: bytes) -> dict[str, object]:
    """Solve reach/sight views for the given viewpoints payload.

    Raises InvalidScenarioError on bad input. Returns a JSON-serializable dict
    with the same shape previously produced by the Flask /views route.
    """
    (s, solve_reach, solve_sight, scenario_id,
     viewpoints) = unpack_scenario_forviews(data)

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

    return solution
