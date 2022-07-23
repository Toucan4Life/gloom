import collections
import textwrap
import itertools
from typing import Callable
from solver.scenarios import *
from solver.utils import *
from solver.settings import *
from solver.print_map import *

class Scenario:
    logging:bool
    debug_visuals:bool
    show_each_action_separately:bool
    visibility_cache :dict[tuple[int,int],bool]
    path_cache : list[tuple[
        dict[tuple[int,Callable[['Scenario',int], bool]],tuple[list[int],list[int]]],
        dict[tuple[int,Callable[['Scenario',int], bool]],tuple[list[int],list[int]]],
        dict[tuple[int,Callable[['Scenario',int], bool]],list[int]],
        dict[tuple[int,Callable[['Scenario',int], bool]],list[int]]]]
    debug_lines: set[tuple[int,tuple[tuple[float,float],tuple[float,float]]]]
    action_move:int
    action_range:int
    action_target:int
    flying:bool
    jumping:bool
    muddled:bool
    debug_toggle:bool
    message:str
    map_width :int
    map_height:int
    map_size:int
    map_vertex_count:int
    walls:list[list[bool]]
    contents:list[str]
    figures:list[str]
    initiatives:list[int]
    aoe_width:int
    aoe_height:int
    aoe_size:int
    aoe:list[bool]
    aoe_center:int

    def __init__(self, width: int, height: int, aoe_width: int, aoe_height: int):
        self.logging = False
        self.debug_visuals = False
        self.show_each_action_separately = False
        self.visibility_cache = {}
        self.path_cache = [{}, {}, {}, {}]
        self.debug_lines = set()

        self.map_width = width
        self.map_height = height
        self.map_size = self.map_width * self.map_height
        self.map_vertex_count = 6 * self.map_size
        self.walls = [[False] * 6 for _ in range(self.map_size)]
        self.contents = [' '] * self.map_size
        self.figures = [' '] * self.map_size
        self.initiatives = [0] * self.map_size

        self.aoe_width = aoe_width
        self.aoe_height = aoe_height
        self.aoe_size = self.aoe_width * self.aoe_height
        self.aoe_center = (self.aoe_size - 1) // 2
        self.aoe = [False] * self.aoe_size

        self.message = ''
        self.action_move = 0
        self.action_range = 0
        self.action_target = 1
        self.flying = False
        self.jumping = False
        self.muddled = False
        self.debug_toggle = False

        if self.aoe_width != 7 or self.aoe_height != 7:
            exit()
        if int(self.aoe_center) - self.aoe_center != 0:
            exit('aoe has no center')

    #def reduce_map(self):
        #self.reduced = True
        # print self.effective_walls
        # if hasattr( self, 'effective_walls' ):
        #   exit(-1)

        # TODO: currently not used
        #assert False

        # # TODO: make sure we don't prepare twice

        # old_height = self.MAP_HEIGHT
        # old_width = self.MAP_WIDTH
        # old_walls = self.walls
        # old_contents = self.contents
        # old_figures = self.figures
        # old_initiatives = self.initiatives

        # min_row = 9999
        # min_column = 9999
        # max_row = 0
        # max_column = 0
        # targets_min_row = 9999
        # targets_min_column = 9999
        # targets_max_row = 0
        # targets_max_column = 0

        # # TODO: don't need to prepare_map first map

        # figures = [ _ for _, figure in enumerate( self.figures ) if figure != ' ' ]
        # contents = [ _ for _, content in enumerate( self.contents ) if content != ' ' ]
        # walls = [
        #   [ _ for _, wall in enumerate( self.walls ) if wall[a] ]
        #   for a in range( 6 )
        # ]

        # # TODO
        # # only need ACTION_RANGE to potential targets
        # # handle AOE based range extensions (need test cases)
        # # time

        # for location in figures:
        #   column = old_div(location , old_height)
        #   min_column = min( min_column, column )
        #   max_column = max( max_column, column )
        #   row = location % old_height
        #   min_row = min( min_row, row )
        #   max_row = max( max_row, row )
        #   if old_figures[location] == 'C':
        #     targets_min_column = min( targets_min_column, column )
        #     targets_max_column = max( targets_max_column, column )
        #     targets_min_row = min( targets_min_row, row )
        #     targets_max_row = max( targets_max_row, row )
        # for location in contents:
        #   column = location / old_height
        #   min_column = min( min_column, column )
        #   max_column = max( max_column, column )
        #   row = location % old_height
        #   min_row = min( min_row, row )
        #   max_row = max( max_row, row )
        # for i in range( 6 ):
        #   for location in walls[i]:
        #     column = location / old_height
        #     min_column = min( min_column, column )
        #     max_column = max( max_column, column )
        #     row = location % old_height
        #     min_row = min( min_row, row )
        #     max_row = max( max_row, row )

        # edge = 1
        # # edge = max( 1, self.ACTION_RANGE )
        # min_row = max( min_row - edge, 0 )
        # min_column = max( min_column - edge, 0 )
        # max_row = min( max_row + edge, old_height - 1 )
        # max_column = min( max_column + edge, old_width - 1 )

        # attack_range = self.ACTION_RANGE
        # # TODO - account for AOE here
        # edge = max( 1, attack_range )
        # targets_min_row = max( targets_min_row - edge, 0 )
        # targets_min_column = max( targets_min_column - edge, 0 )
        # targets_max_row = min( targets_max_row + edge, old_height - 1 )
        # targets_max_column = min( targets_max_column + edge, old_width - 1 )

        # min_row = min( min_row, targets_min_row )
        # min_column = min( min_column, targets_min_column )
        # max_row = max( max_row, targets_max_row )
        # max_column = max( max_column, targets_max_column )

        # reduce_column = min_column / 2 * 2
        # reduce_row = min_row

        # self.REDUCE_COLUMN = reduce_column
        # self.REDUCE_ROW = reduce_row
        # self.ORIGINAL_MAP_HEIGHT = old_height

        # width = max_column - reduce_column + 1
        # height = max_row - reduce_row + 1

        # # init( scenario, width, height, s.AOE_WIDTH, s.AOE_HEIGHT )
        # self.MAP_WIDTH = width
        # self.MAP_HEIGHT = height
        # self.MAP_SIZE = self.MAP_WIDTH * self.MAP_HEIGHT
        # self.MAP_VERTEX_COUNT = 6 * self.MAP_SIZE
        # # s.MAP_CENTER = ( s.MAP_SIZE - 1 ) / 2;

        # self.walls = [ [ False ] * 6 for _ in range( self.MAP_SIZE ) ]
        # self.contents = [ ' ' ] * self.MAP_SIZE
        # self.figures = [ ' ' ] * self.MAP_SIZE
        # self.initiatives = [ 0 ] * self.MAP_SIZE

        # for location in figures:
        #   column = location / old_height
        #   row = location % old_height
        #   column -= reduce_column
        #   row -= reduce_row
        #   new_location = row + column * self.MAP_HEIGHT
        #   self.figures[new_location] = old_figures[location]
        #   self.initiatives[new_location] = old_initiatives[location]
        # for location in contents:
        #   column = location / old_height
        #   row = location % old_height
        #   column -= reduce_column
        #   row -= reduce_row
        #   new_location = row + column * self.MAP_HEIGHT
        #   self.contents[new_location] = old_contents[location]
        # for i in range( 6 ):
        #   for location in walls[i]:
        #     column = location / old_height
        #     row = location % old_height
        #     column -= reduce_column
        #     row -= reduce_row
        #     new_location = row + column * self.MAP_HEIGHT
        #     self.walls[new_location][i] = True

        # self.prepare_map()

    def prepare_map(self) -> None:
        self.setup_vertices_list()
        self.setup_neighbors_mapping()

        contents_walls = [[False] *6]* self.map_size
        self.effective_walls = [[False] *6]* self.map_size
        for location in range(self.map_size):
            if self.contents[location] == 'X':
                contents_walls[location] = [True] * 6
                self.effective_walls[location] = [True] * 6
            else:
                contents_walls[location] = [False] * 6
                self.effective_walls[location] = list(self.walls[location])

        for location in range(self.map_size):
            for edge, neighbor in enumerate(self.neighbors[location]):
                if neighbor != -1:
                    neighbor_edge = (edge + 3) % 6
                    if self.walls[location][edge]:
                        self.walls[neighbor][neighbor_edge] = True
                    if self.effective_walls[location][edge]:
                        self.effective_walls[neighbor][neighbor_edge] = True
                    if contents_walls[location][edge]:
                        contents_walls[neighbor][neighbor_edge] = True

        self.extra_walls = [[False] *6]* self.map_size
        for location in range(self.map_size):
            self.extra_walls[location] = [self.walls[location][_]
                                          and not contents_walls[location][_] for _ in range(6)]

    def set_rules(self, rules: int) -> None:
        self.FROST_RULES = rules == 0
        self.GLOOM_RULES = rules == 1
        self.JOTL_RULES = rules == 2
        self.set_rules_flags()

    def set_rules_flags(self) -> None:
        # RULE_VERTEX_LOS:                LOS is only checked between vertices
        # RULE_JUMP_DIFFICULT_TERRAIN:    difficult terrain effects the last hex of a jump move
        # RULE_PROXIMITY_FOCUS:           proximity is ignored when determining moster focus
        if self.FROST_RULES:
            self.RULE_VERTEX_LOS = False
            self.RULE_DIFFICULT_TERRAIN_JUMP = False
            self.RULE_PROXIMITY_FOCUS = False
        elif self.GLOOM_RULES:
            self.RULE_VERTEX_LOS = True
            self.RULE_DIFFICULT_TERRAIN_JUMP = True
            self.RULE_PROXIMITY_FOCUS = False
        elif self.JOTL_RULES:
            self.RULE_VERTEX_LOS = False
            self.RULE_DIFFICULT_TERRAIN_JUMP = False
            self.RULE_PROXIMITY_FOCUS = True

    def can_end_move_on_standard(self, location: int) -> bool:
        return self.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']

    def can_end_move_on_flying(self, location: int) -> bool:
        return self.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']

    def can_travel_through_standard(self, location: int) -> bool:
        return self.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] != 'C'

    def can_travel_through_flying(self, location: int) -> bool:
        return self.contents[location] in [' ', 'T', 'H', 'D', 'O']

    def is_trap_standard(self, location: int) -> bool:
        return self.contents[location] in ['T', 'H']

    def is_trap_flying(self, location: int) -> bool:
        return False

    def measure_proximity_through(self,  location: int) -> bool:
        return self.contents[location] != 'X'

    def blocks_los(self,  location: int) -> bool:
        return self.contents[location] == 'X'

    def additional_path_cost(self, location: int) -> int:
        return int(self.contents[location] == 'D')

    def setup_vertices_list(self) -> None:
        def calculate_vertex(location:int, vertex:int)->tuple[float,float]:
            hex_row = location % self.map_height
            hex_column = location // self.map_height

            vertex_column = hex_column + [1, 1, 0, 0, 0, 1][vertex]
            vertex_row = 2 * hex_row + \
                [1, 2, 2, 1, 0, 0][vertex] + (hex_column % 2)

            x = 3 * (vertex_column // 2)
            if vertex_row % 2 == 0:
                x += 0.5 + vertex_column % 2
            else:
                x += 2.0 * (vertex_column % 2)

            y = SQRT_3_OVER_2 * vertex_row

            return (x, y)

        self.vertices = ([(0.0, 0.0)] * (self.map_size * 6))
        for location in range(self.map_size):
            for vertex in range(6):
                self.vertices[location * 6 +
                              vertex] = calculate_vertex(location, vertex)

    def get_vertex(self, location: int, vertex: int) -> tuple[float, float]:
        return self.vertices[location * 6 + vertex]

    def setup_neighbors_mapping(self) -> None:
        def get_neighbors(location:int)-> list[int]:
            row = location % self.map_height
            column = location // self.map_height

            bottom_edge = row == 0
            top_edge = row == self.map_height - 1
            left_edge = column == 0
            right_edge = column == self.map_width - 1
            base_column_value = (column + 1) % 2
            base_column = base_column_value == 1

            neighbors = [-1, -1, -1, -1, -1, -1]
            if not left_edge:
                if not bottom_edge or not base_column:
                    neighbors[3] = location - \
                        self.map_height - base_column_value
                if not top_edge or base_column:
                    neighbors[2] = location - \
                        self.map_height + 1 - base_column_value
            if not top_edge:
                neighbors[1] = location + 1
            if not right_edge:
                if not top_edge or base_column:
                    neighbors[0] = location + \
                        self.map_height + 1 - base_column_value
                if not bottom_edge or not base_column:
                    neighbors[5] = location + \
                        self.map_height - base_column_value
            if not bottom_edge:
                neighbors[4] = location - 1

            return neighbors

        self.neighbors = {
            _: get_neighbors(_)
            for _ in range(self.map_size)
        }

    def is_adjacent(self, location_a: int, location_b: int) -> bool:
        if location_b not in self.neighbors[location_a]:
            return False
        distances = self.find_proximity_distances(location_a)
        return distances[location_b] == 1

    def apply_rotated_aoe_offset(self, center: int, offset: tuple[int, int, int], rotation: int) -> int:
        offset = rotate_offset(offset, rotation)
        return apply_offset(center, offset, self.map_height, self.map_size)

    def apply_aoe_offset(self, center: int, offset: tuple[int, int, int]):
        return apply_offset(center, offset, self.map_height, self.map_size)

    def calculate_bounds(self, location_a: int, location_b: int) -> tuple[int, int, int, int]:
        column_a = location_a // self.map_height
        column_b = location_b // self.map_height
        if column_a < column_b:
            column_lower = max(column_a - 1, 0)
            column_upper = min(column_b + 2, self.map_width)
        else:
            column_lower = max(column_b - 1, 0)
            column_upper = min(column_a + 2, self.map_width)

        row_a = location_a - column_a * self.map_height
        row_b = location_b - column_b * self.map_height
        if row_a < row_b:
            row_lower = max(row_a - 1, 0)
            row_upper = min(row_b + 2, self.map_height)
        else:
            row_lower = max(row_b - 1, 0)
            row_upper = min(row_a + 2, self.map_height)

        return (row_lower, column_lower, row_upper, column_upper)

    def occluders_in(self, bounds: tuple[int, int, int, int]) -> Iterable[tuple[tuple[float, float], tuple[float, float]]]:
        for column in range(bounds[1], bounds[3]):
            column_location = column * self.map_height
            for row in range(bounds[0], bounds[2]):
                location = column_location + row

                if self.blocks_los(location):
                    for vertex in range(3):
                        hex_edge_a = self.get_vertex(location, vertex)
                        hex_edge_b = self.get_vertex(
                            location, (vertex + 3) % 6)
                        yield (hex_edge_a, hex_edge_b)

                for edge in range(3):
                    if self.extra_walls[location][edge]:
                        wall_vertex_a = self.get_vertex(location, edge)
                        wall_vertex_b = self.get_vertex(
                            location, (edge + 1) % 6)
                        yield (wall_vertex_a, wall_vertex_b)

    def walls_in(self, bounds: tuple[int, int, int, int]) -> Iterable[tuple[int, int]]:
        for column in range(bounds[1], bounds[3]):
            column_location = column * self.map_height
            for row in range(bounds[0], bounds[2]):
                location = column_location + row

                encoded_wall = 0
                for edge in range(3):
                    if self.extra_walls[location][edge]:
                        encoded_wall += 1 << edge

                if self.blocks_los(location):
                    encoded_wall += 1 << 3

                if encoded_wall != 0:
                    yield location, encoded_wall

    def test_line(self, bounds: tuple[int, int, int, int], vertex_position_a: tuple[float, float], vertex_position_b: tuple[float, float]) -> bool:
        if vertex_position_a == vertex_position_b:
            return True
        for occluder in self.occluders_in(bounds):
            if line_line_intersection((vertex_position_a, vertex_position_b), occluder):
                return False
        return True

    def determine_los_cross_section_edge(self, location_a: int, location_b: int) -> int:
        hex_to_hex_direction = direction(
            (self.get_vertex(location_a, 0), self.get_vertex(location_b, 0)))
        dot_with_up = hex_to_hex_direction[1]
        if dot_with_up > COS_30:
            return 0
        elif dot_with_up <= -COS_30:
            return 3
        else:
            cross_with_up = hex_to_hex_direction[0]
            if dot_with_up > 0.0:
                if cross_with_up < 0.0:
                    return 1
                else:
                    return 5
            else:
                if cross_with_up < 0.0:
                    return 2
                else:
                    return 4

    def calculate_occluder_mapping_set(self, location_a: int, location_b: int) -> tuple[
            list[tuple[float, float, float]],
            list[tuple[tuple[float, float, float], int]],
            list[tuple[tuple[float, float, float], int]],
            list[tuple[tuple[float, float, float], tuple[float, float, float], int, int]]] | None :
        # determine the appropiate cross section to represent the hex volumes
        cross_section_edge = self.determine_los_cross_section_edge(
            location_a, location_b)

        # setup quadrilateral bounding occluders
        source_vertex_0 = self.get_vertex(location_a, cross_section_edge)
        source_vertex_1 = self.get_vertex(
            location_a, (cross_section_edge + 3) % 6)
        target_vertex_0 = self.get_vertex(location_b, cross_section_edge)
        target_vertex_1 = self.get_vertex(
            location_b, (cross_section_edge + 3) % 6)
        edge_source = (source_vertex_0, source_vertex_1)
        edge_one = (source_vertex_1, target_vertex_1)
        edge_target = (target_vertex_1, target_vertex_0)
        edge_zero = (target_vertex_0, source_vertex_0)
        edge_direction_source = direction(edge_source)
        edge_direction_one = direction(edge_one)
        edge_direction_target = direction(edge_target)
        edge_direction_zero = direction(edge_zero)

        def calculate_occluder_mapping(point:tuple[float,float])->tuple[float,float,float]:
            value_at_zero = occluder_target_intersection(
                (source_vertex_0, point), (target_vertex_0, target_vertex_1))
            value_at_one = occluder_target_intersection(
                (source_vertex_1, point), (target_vertex_0, target_vertex_1))
            return (
                value_at_zero,
                value_at_one,
                value_at_one - value_at_zero
            )

        occluder_mappings = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0)]
        occluder_mappings_below:list[tuple[tuple[float,float,float],int]] = []
        occluder_mappings_above:list[tuple[tuple[float,float,float],int]] = []
        occluder_mappings_internal:list[tuple[tuple[float, float, float], tuple[float, float, float], int, int]] = []
        for line in self.occluders_in(self.calculate_bounds(location_a, location_b)):
            # self.debug_lines.add( (1, line ) )

            if not within_bound(line[0], edge_source, edge_direction_source) or not within_bound(line[0], edge_target, edge_direction_target):
                if not within_bound(line[1], edge_source, edge_direction_source) or not within_bound(line[1], edge_target, edge_direction_target):
                    continue

            if within_bound(line[0], edge_one, edge_direction_one):
                if within_bound(line[0], edge_zero, edge_direction_zero):
                    status_a = VERTEX_INSIDE
                else:
                    status_a = VERTEX_OUTSIDE_BOUND_ZERO
            else:
                status_a = VERTEX_OUTSIDE_BOUND_ONE
            if within_bound(line[1], edge_one, edge_direction_one):
                if within_bound(line[1], edge_zero, edge_direction_zero):
                    status_b = VERTEX_INSIDE
                else:
                    status_b = VERTEX_OUTSIDE_BOUND_ZERO
            else:
                status_b = VERTEX_OUTSIDE_BOUND_ONE

            if (status_a == VERTEX_OUTSIDE_BOUND_ZERO and status_b == VERTEX_OUTSIDE_BOUND_ONE) or (status_a == VERTEX_OUTSIDE_BOUND_ONE and status_b == VERTEX_OUTSIDE_BOUND_ZERO):
                return None

            elif status_a == VERTEX_INSIDE and status_b == VERTEX_OUTSIDE_BOUND_ZERO:
                mapping = calculate_occluder_mapping(line[0])
                occluder_mappings_below.append(
                    (mapping, len(occluder_mappings)))
                occluder_mappings.append(mapping)

            elif status_a == VERTEX_INSIDE and status_b == VERTEX_OUTSIDE_BOUND_ONE:
                mapping = calculate_occluder_mapping(line[0])
                occluder_mappings_above.append(
                    (mapping, len(occluder_mappings)))
                occluder_mappings.append(mapping)

            elif status_a == VERTEX_OUTSIDE_BOUND_ZERO and status_b == VERTEX_INSIDE:
                mapping = calculate_occluder_mapping(line[1])
                occluder_mappings_below.append(
                    (mapping, len(occluder_mappings)))
                occluder_mappings.append(mapping)

            elif status_a == VERTEX_OUTSIDE_BOUND_ONE and status_b == VERTEX_INSIDE:
                mapping = calculate_occluder_mapping(line[1])
                occluder_mappings_above.append(
                    (mapping, len(occluder_mappings)))
                occluder_mappings.append(mapping)

            elif status_a == VERTEX_INSIDE and status_b == VERTEX_INSIDE:
                mapping_0 = calculate_occluder_mapping(line[0])
                mapping_1 = calculate_occluder_mapping(line[1])
                occluder_mappings_internal.append(
                    (mapping_0, mapping_1, len(occluder_mappings), len(occluder_mappings) + 1))
                occluder_mappings.append(mapping_0)
                occluder_mappings.append(mapping_1)

        return occluder_mappings, occluder_mappings_below, occluder_mappings_above, occluder_mappings_internal

    # def plot_debug_visibility_graph(self, occluder_mapping_set):
    #     (
    #         occluder_mappings,
    #         occluder_mappings_below,
    #         occluder_mappings_above,
    #         occluder_mappings_internal
    #     ) = occluder_mapping_set

    #     # the visibility windows are:
    #     # - below all blue lines
    #     # - above all purple lines
    #     # - below green and above red line pairs

    #     # upper bounds - blue
    #     self.debug_plot_line(3, ((0.0, 1.0), (1.0, 1.0)))
    #     for mapping, _ in occluder_mappings_above:
    #         self.debug_plot_line(3, ((0.0, mapping[0]), (1.0, mapping[1])))

    #     # lower bounds - purple
    #     self.debug_plot_line(0, ((0.0, 0.0), (1.0, 0.0)))
    #     for mapping, _ in occluder_mappings_below:
    #         self.debug_plot_line(0, ((0.0, mapping[0]), (1.0, mapping[1])))

    #     # top of internal occluder - red
    #     # bottom of internal occluder - green
    #     for mapping in occluder_mappings_internal:
    #         half_point = (lerp(mapping[0][0], mapping[0][1], 0.5), lerp(
    #             mapping[1][0], mapping[1][1], 0.5))

    #         value_0 = get_occluder_value_at(mapping[0], 0.0)
    #         value_1 = get_occluder_value_at(mapping[1], 0.0)
    #         color = (1, 2) if occluder_greater_than(
    #             value_0, value_1) else (2, 1)
    #         self.debug_plot_line(
    #             color[0], ((0.0, mapping[0][0]), (0.5, half_point[0])))
    #         self.debug_plot_line(
    #             color[1], ((0.0, mapping[1][0]), (0.5, half_point[1])))

    #         value_0 = get_occluder_value_at(mapping[0], 1.0)
    #         value_1 = get_occluder_value_at(mapping[1], 1.0)
    #         color = (1, 2) if occluder_greater_than(
    #             value_0, value_1) else (2, 1)
    #         self.debug_plot_line(
    #             color[0], ((0.5, half_point[0]), (1.0, mapping[0][1])))
    #         self.debug_plot_line(
    #             color[1], ((0.5, half_point[1]), (1.0, mapping[1][1])))

    #     # shade the graph to indicate visibility windows
    #     POINT_DENSITY = 40
    #     for nx in range(POINT_DENSITY):
    #         x = old_div(nx, float(POINT_DENSITY - 1))
    #         windows = get_visibility_windows_at(x, occluder_mapping_set, False)
    #         for ny in range(POINT_DENSITY):
    #             y = old_div(ny, float(POINT_DENSITY - 1))
    #             for window in windows:
    #                 if y >= window[1] and y <= window[2]:
    #                     color = 7
    #                     break
    #             else:
    #                 color = 6
    #             self.debug_plot_point(color, (x, y))

    # def calculate_symmetric_coordinates(self, origin, location):
    #     column_a = old_div(origin, self.MAP_HEIGHT)
    #     row_a = origin % self.MAP_HEIGHT
    #     column_b = old_div(location, self.MAP_HEIGHT)
    #     row_b = location % self.MAP_HEIGHT

    #     c = column_b - column_a
    #     r = row_b - row_a
    #     q = column_a % 2

    #     if c == 0:
    #         if r > 0:
    #             t = 0
    #         else:
    #             t = 3
    #     elif c < 0:
    #         if r < old_div((q + c), 2):
    #             t = 3
    #         elif r < old_div((q - c), 2):
    #             t = 2
    #         else:
    #             t = 1
    #     else:
    #         if r <= old_div((q - c), 2):
    #             t = 4
    #         elif r <= old_div((q + c), 2):
    #             t = 5
    #         else:
    #             t = 0

    #     if t == 0:
    #         u = r - old_div((q - c), 2)
    #         v = c
    #     elif t == 1:
    #         u = r - old_div((q + c), 2)
    #         v = r - old_div((q - c), 2)
    #     elif t == 2:
    #         u = -c
    #         v = r - old_div((q + c), 2)
    #     elif t == 3:
    #         u = -r + old_div((q - c), 2)
    #         v = -c
    #     elif t == 4:
    #         u = -r + old_div((q + c), 2)
    #         v = -r + old_div((q - c), 2)
    #     else:
    #         u = c
    #         v = -r + old_div((q + c), 2)

    #     return t, u, v

    # can be used to implement a long-term collision cache
    # that is, a server-wide cache not cleared between scenarios
    # to do so, use FileSystemCache of flask_caching
    # tested, but not in use do to size concerns
    # cache quickly grows to be many MB and has relatively unbounded size
    # gives ~24% speed up on standard (simple) senarios with long, blocking walls
    # gives ~10% speed up on 131 (complex unit test)
    # gives no speed up on many unit tests (as they have very few occluders)
    # the savings was measured with an in-memory cache (dictionary), not a file system, which may be slower
    # def calculate_occluder_cache_key(self, location_a, location_b):
    #     # does not take advantage of reflection symetry
    #     t, u, v = self.calculate_symmetric_coordinates(location_a, location_b)
    #     orientation = 6 - t
    #     cache_key = [(u, v)]

    #     for location, encoded_wall in self.walls_in(self.calculate_bounds(location_a, location_b)):
    #         t, u, v = self.calculate_symmetric_coordinates(
    #             location_a, location)
    #         t = (t + orientation) % 6
    #         cache_key.append((t, u, v, encoded_wall))

    #     if len(cache_key) == 1:
    #         # no occluders; use None to short circuit los test in calling function
    #         return None

    #     cache_key.sort()
    #     return tuple(cache_key)

    def test_full_hex_los_between_locations(self, location_a: int, location_b: int) -> bool:
        # handle simple case of neighboring locations
        if location_b in self.neighbors[location_a]:
            edge = self.neighbors[location_a].index(location_b)
            if not self.effective_walls[location_a][edge]:
                return True
            neighbor_edge = (edge + 3) % 6
            if not self.effective_walls[location_a][(edge + 1) % 6] and not self.effective_walls[location_b][(neighbor_edge + 5) % 6]:
                return True
            if not self.effective_walls[location_a][(edge + 5) % 6] and not self.effective_walls[location_b][(neighbor_edge + 1) % 6]:
                return True
            return False

        # A visibility test between two hexes can be simplified to a visibility test
        # between two lines. Any point on one line can potentially see any point on
        # the other line. That visibility space between the two lines can be mapped to
        # a unit square.

        # An occluder blocks visibility in an area bound on one side by a line cutting
        # through the square. Such lines are determined by how that occluder's end point
        # maps one line onto the other. Those are lines, not curves, when the two tested
        # lines are parallel.

        # Testing for visibility is equivalent to overlaying all blocked areas onto the
        # square, then testing if any unblocked regions remain.

        # find occluders and generate the lines that bound each occluder's blocked area
        occluder_mapping_set = self.calculate_occluder_mapping_set(
            location_a, location_b)
        if occluder_mapping_set is None:
            return False
        # at each line intersection, determine whether there is a visibility window
        for x in occluder_intersections(occluder_mapping_set[0]):
            if len(get_visibility_windows_at(x, occluder_mapping_set))>0:
                return True

        # this logic can be used to prove that both cross_sections are not needed with
        # Gloomhaven's grid-locked occluders
        # https://www.reddit.com/r/Gloomhaven/comments/saevcj/comment/huedfq9/?utm_source=share&utm_medium=web2x&context=3
        # the third parameter to calculate_occluder_mapping_set is meant to return the
        # second-most perpendicular cross section
        # # for each cross section line
        # for cross_section in [ False, True ]:
        #   # find occluders and generate the lines that bound each occluder's blocked area
        #   occluder_mapping_set = self.calculate_occluder_mapping_set( location_a, location_b, cross_section )
        #   if occluder_mapping_set is None:
        #     continue
        #   # at each line intersection, determine whether there is a visibility window
        #   for x in occluder_intersections( occluder_mapping_set[0] ):
        #     if get_visibility_windows_at( x, occluder_mapping_set, True ):
        #       assert not cross_section
        #       return True

        return False

    def find_best_full_hex_los_sightline(self, location_a: int, location_b: int) -> tuple[tuple[float, float],tuple[float, float]]:
        # Find the unblocked region in the visibility square with the largest area.
        # Place the sightline at its center of mass.

        # find occluders and generate the lines that bound each occluder's blocked area
        occluder_mapping_set = self.calculate_occluder_mapping_set(
            location_a, location_b)
        if occluder_mapping_set is None:
            return ((-1.0, -1.0),(-1.0, -1.0))
        occluder_mappings = occluder_mapping_set[0]

        # self.plot_debug_visibility_graph( occluder_mapping_set )

        # translate the occluder mappings (which are stored as the value of y at
        # x = 0 and x = 1) into 2d lines and include the x = 0 and x = 1 vertial
        # lines
        lines:list[tuple[tuple[tuple[float, float], tuple[float, float]],tuple[float, float]]] = []
        for occluder in occluder_mappings:
            line = ((0.0, occluder[0]), (1.0, occluder[1]))
            lines.append((line, direction(line)))
        lines.append((((0.0, 0.0), (0.0, 1.0)), (0.0, 1.0)))
        lines.append((((1.0, 0.0), (1.0, 1.0)), (0.0, 1.0)))

        # loop over every window at every occluder mapping intersection
        window_polygons:list[tuple[float, tuple[float, float]]] = []
        polygon_starts = []
        for x in occluder_intersections(occluder_mappings):
            for window in get_visibility_windows_at(x, occluder_mapping_set):
                # build a polygon around the open area
                polygon = map_window_polygon(
                    window, polygon_starts, occluder_mappings, lines)
                if polygon is not None:
                    window_polygons.append(
                        calculate_polygon_properties(polygon))

        # place the sightline at the center of the polygon with the largest area
        _, (x, y) = max(window_polygons, key=lambda polygon: polygon[0])
        # self.debug_plot_point( 4, ( x, y ) )

        # clip the sightline to the hex edges
        cross_section_edge = self.determine_los_cross_section_edge(
            location_a, location_b)
        source_vertex_0 = self.get_vertex(location_a, cross_section_edge)
        source_vertex_1 = self.get_vertex(
            location_a, (cross_section_edge + 3) % 6)
        target_vertex_0 = self.get_vertex(location_b, cross_section_edge)
        target_vertex_1 = self.get_vertex(
            location_b, (cross_section_edge + 3) % 6)
        edge_source = (source_vertex_0, source_vertex_1)
        edge_target = (target_vertex_1, target_vertex_0)
        start_point = lerp_along_line(edge_source, x)
        end_point = lerp_along_line(edge_target, 1.0 - y)
        sightline_start = (0.0 , 0.0)
        for edge in [cross_section_edge, (cross_section_edge + 1) % 6, (cross_section_edge + 2) % 6]:
            edge_line = (self.get_vertex(location_a, edge),
                         self.get_vertex(location_a, (edge + 1) % 6))
            factor = line_hex_edge_intersection(
                (start_point, end_point), edge_line)
            if factor is not None:
                sightline_start = lerp_along_line(edge_line, factor)
                break
        sightline_end = (0.0 , 0.0)
        for edge in [(cross_section_edge + 3) % 6, (cross_section_edge + 4) % 6, (cross_section_edge + 5) % 6]:
            edge_line = (self.get_vertex(location_b, edge),
                         self.get_vertex(location_b, (edge + 1) % 6))
            factor = line_hex_edge_intersection(
                (start_point, end_point), edge_line)
            if factor is not None:
                sightline_end = lerp_along_line(edge_line, factor)
                break

        # edge_one = ( source_vertex_1, target_vertex_1 )
        # edge_zero = ( target_vertex_0, source_vertex_0 )
        # self.debug_lines.add( ( 2, edge_source ) )
        # self.debug_lines.add( ( 2, edge_one ) )
        # self.debug_lines.add( ( 2, edge_target ) )
        # self.debug_lines.add( ( 2, edge_zero ) )
        # N = 4
        # for n in range( N ):
        #   x = n / float( N - 1 )
        #   y, _ = get_occluder_value_at( occluder_mappings[2], x )
        #   self.debug_lines.add( ( 3, ( lerp_along_line( edge_source, x ), lerp_along_line( edge_target, 1.0 - y ) ) ) )

        return (sightline_start, sightline_end)

    def vertex_at_wall(self, location:int, vertex:int)->bool:
        if self.effective_walls[location][vertex]:
            return True
        if self.effective_walls[location][(vertex + 5) % 6]:
            return True
        if self.effective_walls[self.neighbors[location][vertex]][(vertex + 4) % 6]:
            return True
        return False

    def test_los_between_locations(self, location_a: int, location_b: int) -> bool:
        cache_key = visibility_cache_key(location_a, location_b)
        if cache_key in self.visibility_cache:
            return self.visibility_cache[cache_key]

        if not self.RULE_VERTEX_LOS:
            result = self.test_full_hex_los_between_locations(
                location_a, location_b)
        else:
            result = self.test_vertex_los_between_locations(
                location_a, location_b)

        self.visibility_cache[cache_key] = result
        return result

    def test_vertex_los_between_locations(self, location_a: int, location_b: int) -> bool:
        bounds = self.calculate_bounds(location_a, location_b)

        for vertex_a in range(6):
            if self.vertex_at_wall(location_a, vertex_a):
                continue
            vertex_position_a = self.get_vertex(location_a, vertex_a)

            for vertex_b in range(6):
                if self.vertex_at_wall(location_b, vertex_b):
                    continue
                vertex_position_b = self.get_vertex(location_b, vertex_b)

                if self.test_line(bounds, vertex_position_a, vertex_position_b):
                    return True

        return False

    def find_shortest_sightline(self, location_a: int, location_b: int) -> tuple[tuple[float, float], tuple[float, float]]:
        if not self.RULE_VERTEX_LOS:
            return self.find_best_full_hex_los_sightline(location_a, location_b)

        bounds = self.calculate_bounds(location_a, location_b)

        class v:
            shortest_length = float('inf')
            shortest_line = ((-1.0, -1.0),(-1.0, -1.0))

        def consider_sightline(location_a:int, vertex_a:int, location_b:int, vertex_b:int):
            length = calculate_distance(vertex_position_a, vertex_position_b)
            if length < v.shortest_length:
                if self.test_line(bounds, vertex_position_a, vertex_position_b):
                    v.shortest_length = length
                    v.shortest_line = (self.get_vertex(
                        location_a, vertex_a), self.get_vertex(location_b, vertex_b))

        for vertex_a in range(6):
            if self.vertex_at_wall(location_a, vertex_a):
                continue
            vertex_position_a = self.get_vertex(location_a, vertex_a)

            for vertex_b in range(6):
                if self.vertex_at_wall(location_b, vertex_b):
                    continue
                vertex_position_b = self.get_vertex(location_b, vertex_b)

                consider_sightline(location_a, vertex_a, location_b, vertex_b)

        return v.shortest_line

    # def pack_point(self, location:int, vertex:int):
    #     if vertex == 2:
    #         if self.neighbors[location][2] != -1:
    #             location = self.neighbors[location][2]
    #             vertex = 0
    #     elif vertex == 3:
    #         if self.neighbors[location][3] != -1:
    #             location = self.neighbors[location][3]
    #             vertex = 1
    #         elif self.neighbors[location][2] != -1:
    #             location = self.neighbors[location][2]
    #             vertex = 5
    #     elif vertex == 4:
    #         if self.neighbors[location][3] != -1:
    #             location = self.neighbors[location][3]
    #             vertex = 0
    #         elif self.neighbors[location][4] != -1:
    #             location = self.neighbors[location][4]
    #             vertex = 2
    #     elif vertex == 5:
    #         if self.neighbors[location][4] != -1:
    #             location = self.neighbors[location][4]
    #             vertex = 1
    #     return self.dereduce_location(location) * 6 + vertex

    # def pack_line(self, location_a, vertex_a, location_b, vertex_b):
    #     point_a = self.pack_point(location_a, vertex_a)
    #     point_b = self.pack_point(location_b, vertex_b)
    #     return point_a * self.MAP_VERTEX_COUNT + point_b

    def dereduce_location(self, location: int) -> int:
        return location
        

    def find_path_distances(self, start: int, traversal_test: Callable[['Scenario',int], bool]) -> tuple[list[int], list[int]]:
        cache_key = (start, traversal_test)
        if cache_key in self.path_cache[0]:
            return self.path_cache[0][cache_key]

        distances = [MAX_VALUE] * self.map_size
        traps = [MAX_VALUE] * self.map_size

        frontier:collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0
        traps[start] = 0

        while not len(frontier) == 0:
            current = frontier.popleft()
            distance = distances[current]
            trap = traps[current]
            for edge, neighbor in enumerate(self.neighbors[current]):
                if neighbor == -1:
                    continue
                if not traversal_test(self, neighbor):
                    continue
                if self.walls[current][edge]:
                    continue
                neighbor_distance = distance + 1 + \
                    int(not self.flying and not self.jumping and self.additional_path_cost(
                        neighbor))
                neighbor_trap = int(not self.jumping) * \
                    trap + int(self.is_trap(self, neighbor))
                if (neighbor_trap, neighbor_distance) < (traps[neighbor], distances[neighbor]):
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance
                    traps[neighbor] = neighbor_trap

        if self.RULE_DIFFICULT_TERRAIN_JUMP:
            if self.jumping:
                for location in range(self.map_size):
                    distances[location] += self.additional_path_cost(location)
                distances[start] -= self.additional_path_cost(start)

        self.path_cache[0][cache_key] = (distances, traps)
        return distances, traps

    def find_path_distances_reverse(self, destination: int, traversal_test: Callable[['Scenario',int], bool]) -> tuple[list[int], list[int]]:
        # reverse in that we find the path distance to the destination from every location
        # path distance is symetric except for difficult terrain and traps
        # we correct for the asymetry of starting vs ending on difficult terrain
        # we correct for the asymetry of starting vs ending on traps
        cache_key = (destination, traversal_test)
        if cache_key in self.path_cache[1]:
            return self.path_cache[1][cache_key]

        distances, traps = self.find_path_distances(
            destination, traversal_test)
        distances = list(distances)
        traps = list(traps)
        if not self.flying:
            if not self.jumping or self.RULE_DIFFICULT_TERRAIN_JUMP:
                destination_additional_path_cost = self.additional_path_cost(
                    destination)
                if destination_additional_path_cost > 0:
                    distances = [
                        _ + destination_additional_path_cost if _ != MAX_VALUE else _ for _ in distances]
                for location in range(self.map_size):
                    distances[location] -= self.additional_path_cost(location)

            if self.is_trap(self, destination):
                traps = [_ + 1 if _ != MAX_VALUE else _ for _ in traps]
            for location in range(self.map_size):
                traps[location] -= int(self.is_trap(self, location))

        self.path_cache[1][cache_key] = (distances, traps)
        return distances, traps

    def find_proximity_distances(self, start: int) -> list[int]:
        cache_key = (start)
        if cache_key in self.path_cache[2]:
            return self.path_cache[2][cache_key]

        distances = [MAX_VALUE] * self.map_size

        frontier:collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0

        while not len(frontier) == 0:
            current = frontier.popleft()
            distance = distances[current]
            for edge, neighbor in enumerate(self.neighbors[current]):
                if neighbor == -1:
                    continue
                if not self.measure_proximity_through(neighbor):
                    continue
                if self.walls[current][edge]:
                    continue
                neighbor_distance = distance + 1
                if neighbor_distance < distances[neighbor]:
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance

        self.path_cache[2][cache_key] = distances
        return distances

    # def find_distances(self, start: int) -> list[int]:
    #     cache_key = (start)
    #     if cache_key in self.path_cache[3]:
    #         return self.path_cache[3][cache_key]

    #     distances = [MAX_VALUE] * self.MAP_SIZE

    #     frontier = collections.deque()
    #     frontier.append(start)
    #     distances[start] = 0

    #     while not len(frontier) == 0:
    #         current = frontier.popleft()
    #         distance = distances[current]
    #         for neighbor in self.neighbors[current]:
    #             if neighbor == -1:
    #                 continue
    #             neighbor_distance = distance + 1
    #             if neighbor_distance < distances[neighbor]:
    #                 frontier.append(neighbor)
    #                 distances[neighbor] = neighbor_distance

    #     self.path_cache[3][cache_key] = distances
    #     return distances

    def calculate_monster_move(self) -> tuple[
        set[tuple[int,int,int]],
        dict[tuple[int,int,int],tuple[int,int,int]],
        dict[tuple[int,int,int],set[int]],
        dict[tuple[int,int,int],set[int]],
        dict[tuple[int,int,int],set[tuple[tuple[float,float],tuple[tuple[float,float]]]]],
        dict[tuple[int,int,int],set[int]]]:
        map_debug_tags = [' '] * self.map_size
        if self.action_range == 0 or self.action_target == 0:
            ATTACK_RANGE = 1
            SUSCEPTIBLE_TO_DISADVANTAGE = False
        else:
            ATTACK_RANGE = self.action_range
            SUSCEPTIBLE_TO_DISADVANTAGE = not self.muddled
        PLUS_TARGET = self.action_target - 1
        PLUS_TARGET_FOR_MOVEMENT = max(0, PLUS_TARGET)
        ALL_TARGETS = self.action_target == 6

        AOE_ACTION = self.action_target > 0 and True in self.aoe
        AOE_MELEE = AOE_ACTION and self.action_range == 0

        if self.flying:
            self.can_end_move_on = Scenario.can_end_move_on_flying
            self.can_travel_through = Scenario.can_travel_through_flying
            self.is_trap = Scenario.is_trap_flying
        elif self.jumping:
            self.can_end_move_on = Scenario.can_end_move_on_standard
            self.can_travel_through = Scenario.can_travel_through_flying
            self.is_trap = Scenario.is_trap_standard
        else:
            self.can_end_move_on = Scenario.can_end_move_on_standard
            self.can_travel_through = Scenario.can_travel_through_standard
            self.is_trap = Scenario.is_trap_standard

        if self.logging:
            
            # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in range( self.MAP_SIZE ) ] )
            if AOE_ACTION:
                false_contents = ['   '] * self.aoe_size
                if AOE_MELEE:
                    false_contents[self.aoe_center] = ' A '
                # print_map( self, self.AOE_WIDTH, self.AOE_HEIGHT, [ [ False ] * 6 ] * self.AOE_SIZE, false_contents, [ format_aoe( _ ) for _ in self.aoe ] )
            # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ] )

            out = ''
            if self.FROST_RULES:
                out += ', FROSTHAVEN'
            if self.GLOOM_RULES:
                out += ', GLOOMHAVEN'
            if self.JOTL_RULES:
                out += ', JAWS OF THE LION'
            if self.action_move > 0:
                out += ', MOVE %i' % self.action_move
            if self.action_range > 0 and self.action_target > 0:
                out += ', RANGE %i' % self.action_range
            if self.action_target > 0:
                out += ', ATTACK'
            if AOE_ACTION:
                out += ', AOE'
            if PLUS_TARGET > 0:
                if ALL_TARGETS:
                    out += ', TARGET ALL'
                else:
                    out += ', +TARGET %i' % PLUS_TARGET
            if self.flying:
                out += ', FLYING'
            elif self.jumping:
                out += ', JUMPING'
            if self.muddled:
                out += ', MUDDLED'
            out += ', DEBUG_TOGGLE = %s' % (
                'TRUE' if self.debug_toggle else 'FALSE')
            if out == '':
                out = 'NO ACTION'
            else:
                out = out[2:]
            print(out)
            if self.message:
                print(textwrap.fill(self.message, 82))

        actions:set[tuple[int,int]] = set()
        aoes:dict[tuple[int,int],list[int]] = {}
        destinations:dict[tuple[int,int],set[int]] = {}
        focus_map:dict[tuple[int,int],int] = {}

        # find active monster
        active_monster = self.figures.index('A')
        travel_distances, trap_counts = self.find_path_distances(
            active_monster, self.can_travel_through)
        proximity_distances = self.find_proximity_distances(active_monster)
        # rev_travel_distances, rev_trap_counts = self.find_path_distances_reverse( active_monster, self.can_travel_through )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in trap_counts ] )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in travel_distances ] )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in proximity_distances ] )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in rev_travel_distances ] )

        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( self.calculate_symmetric_coordinates( active_monster, _ )[0] ) for _ in range( self.MAP_SIZE ) ] )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( self.calculate_symmetric_coordinates( active_monster, _ )[1] ) for _ in range( self.MAP_SIZE ) ] )
        # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( self.calculate_symmetric_coordinates( active_monster, _ )[2] ) for _ in range( self.MAP_SIZE ) ] )
        # _ = [ self.calculate_symmetric_coordinates( active_monster, _ ) for _ in range( self.MAP_SIZE ) ]

        # doesn't speed things up but makes los testing order more intuitive for debugging
        travel_distance_sorted_map = sorted(
            list(range(self.map_size)), key=lambda x: travel_distances[x])
        aoe=([(int(0), int(0),int(0))] * 2)
        # process aoe
        if AOE_ACTION:
            center_location = self.aoe_center if AOE_MELEE else self.aoe.index(
                True)
            aoe = [
                get_offset(center_location, location, self.aoe_height)
                for location in range(self.aoe_size) if self.aoe[location]
            ]

        # precalculate aoe patterns to remove degenerate cases
        if AOE_ACTION and not AOE_MELEE:
            PRECALC_GRID_HEIGHT = 21
            PRECALC_GRID_WIDTH = 21
            PRECALC_GRID_SIZE = PRECALC_GRID_HEIGHT * PRECALC_GRID_WIDTH
            PRECALC_GRID_CENTER = (PRECALC_GRID_SIZE - 1) // 2

            aoe_pattern_set:set[tuple[int]] = set()
            for aoe_pin in aoe:
                for aoe_rotation in range(12):
                    aoe_hexes:list[int] = []
                    for aoe_offset in aoe:
                        aoe_offset = pin_offset(aoe_offset, aoe_pin)
                        aoe_offset = rotate_offset(aoe_offset, aoe_rotation)
                        location = apply_offset(
                            PRECALC_GRID_CENTER, aoe_offset, PRECALC_GRID_HEIGHT, PRECALC_GRID_SIZE)
                        aoe_hexes.append(location)
                    aoe_hexes.sort()
                    aoe_pattern_set.add(tuple(aoe_hexes))

            aoe_pattern_list = [
                [
                    get_offset(PRECALC_GRID_CENTER,
                               location, PRECALC_GRID_HEIGHT)
                    for location in aoe
                ]
                for aoe in aoe_pattern_set
            ]

        # find characters
        characters = [_ for _, figure in enumerate(
            self.figures) if figure == 'C']

        # find monster focuses
        num_focus_ranks=0
        if not len(characters):
            focuses:set[int] = set()

        else:
            class s:
                focuses:set[int] = set()
                shortest_path = (
                    MAX_VALUE - 1,  # traps to attack potential focus
                    MAX_VALUE - 1,  # distance to attack potential focus
                    MAX_VALUE - 1,  # proximity of potential focus
                    MAX_VALUE - 1,  # initiative of potential focus
                )
            
            def consider_focus():
                this_path = (
                    trap_counts[location],
                    travel_distances[location],
                    0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[character],
                    self.initiatives[character],
                )
                if this_path == s.shortest_path:
                    if self.test_los_between_locations(character, location):
                        s.focuses.add(character)
                if this_path < s.shortest_path:
                    if self.test_los_between_locations(character, location):
                        s.shortest_path = this_path
                        s.focuses = {character}

            for character in characters:
                range_to_character = self.find_proximity_distances(character)
                # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( _ ) for _ in self.contents ], [ format_numerical_label( _ ) for _ in range_to_character ] )

                for location in travel_distance_sorted_map:
                    # for location in range( self.MAP_SIZE ):

                    # early test of location using the first two elements of the minimized tuple
                    if trap_counts[location] > s.shortest_path[0]:
                        continue
                    if trap_counts[location] == s.shortest_path[0]:
                        if travel_distances[location] > s.shortest_path[1]:
                            continue

                    def inner():
                        if self.can_end_move_on(self, location):
                            if not AOE_ACTION or PLUS_TARGET > 0:
                                if range_to_character[location] <= ATTACK_RANGE:
                                    consider_focus()
                                    return
                            if AOE_ACTION:
                                if AOE_MELEE:
                                    for aoe_rotation in range(12):
                                        for aoe_offset in aoe:
                                            if character == self.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation):
                                                consider_focus()
                                                return
                                else:
                                    distances = self.find_proximity_distances(
                                        location)
                                    for aoe_pattern in aoe_pattern_list:
                                        for aoe_offset in aoe_pattern:
                                            target = self.apply_aoe_offset(
                                                character, aoe_offset)
                                            if target:
                                                if distances[target] <= ATTACK_RANGE:
                                                    consider_focus()
                                                    return

                    inner()

            focuses = s.focuses

            # rank characters for secondary targeting
            focus_ranks:dict[int,int] = {}
            sorted_infos = sorted(
                ((proximity_distances[_], self.initiatives[_]), _)
                for _ in characters
            )
            best_info = sorted_infos[0][0]
            rank = 0
            for info, character in sorted_infos:
                if info != best_info:
                    rank += 1
                    best_info = info
                focus_ranks[character] = rank
            num_focus_ranks = rank + 1

        # players choose among focus ties
        for focus in focuses:

            # find the best group of targets based on the following priorities

            class t:
                groups:set[tuple[int]] = set()
                best_group = (
                    MAX_VALUE - 1,  # traps to the attack location
                    0,             # can reach the attack location
                    1,             # disadvantage against the focus
                    0,             # total number of targets
                    MAX_VALUE - 1,  # path length to the attack location
                ) + tuple([0] * num_focus_ranks)  # target count for each focus rank

            def consider_group(num_targets:int, preexisting_targets:list[int], preexisting_targets_of_rank:list[int], preexisting_targets_disadvantage:int, aoe_hexes:list[int]):
                available_targets = targetable_characters - \
                    set(preexisting_targets)
                max_num_targets = min(num_targets, len(
                    available_targets)) if not ALL_TARGETS else len(available_targets)

                # loop over every possible set of potential targets
                for target_set in itertools.combinations(available_targets, max_num_targets):
                    targets = preexisting_targets + list(target_set)

                    # only consider actions that hit the focus
                    if not focus in targets:
                        continue

                    targets_of_rank = list(preexisting_targets_of_rank)
                    for target in target_set:
                        targets_of_rank[focus_ranks[target]] += 1

                    this_group = (
                        trap_counts[location],
                        -can_reach_location,
                        int(has_disadvantage_against_focus),
                        -len(targets),
                        travel_distances[location],
                    ) + tuple(-_ for _ in targets_of_rank)

                    # print location, this_group, t.best_group
                    if this_group == t.best_group:
                        group = tuple(sorted(targets))
                        t.groups.add(group)
                    elif this_group < t.best_group:
                        group = tuple(sorted(targets))
                        t.best_group = this_group
                        t.groups = {group}
                    # print t.groups

            for location in range(self.map_size):
                if self.can_end_move_on(self, location):
                    can_reach_location = travel_distances[location] <= self.action_move

                    # early test of location using the first two elements of the minimized tuple
                    if trap_counts[location] > t.best_group[0]:
                        continue
                    if trap_counts[location] == t.best_group[0]:
                        if not can_reach_location and t.best_group[1] == -1:
                            continue

                    has_disadvantage_against_focus = SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(
                        location, focus)

                    # determine the set of characters attackable by non-AoE attacks
                    range_to_location = self.find_proximity_distances(location)
                    targetable_characters = {
                        _
                        for _ in characters
                        if range_to_location[_] <= ATTACK_RANGE and self.test_los_between_locations(_, location)
                    }

                    if not AOE_ACTION:
                        # add non-AoE targets and consider resulting actions
                        consider_group(1 + PLUS_TARGET_FOR_MOVEMENT,
                                       [], [0] * num_focus_ranks, 0, [])

                    elif AOE_MELEE:
                        # loop over every possible aoe placement
                        for aoe_rotation in range(12):
                            aoe_targets:list[int] = []
                            aoe_targets_of_rank = [0] * num_focus_ranks
                            aoe_targets_disadvantage = 0
                            aoe_hexes = []

                            # loop over each hex in the aoe, adding targets
                            for aoe_offset in aoe:
                                target = self.apply_rotated_aoe_offset(
                                    location, aoe_offset, aoe_rotation)
                                aoe_hexes.append(target)
                                if target in characters:
                                    if self.test_los_between_locations(target, location):
                                        aoe_targets.append(target)
                                        aoe_targets_of_rank[focus_ranks[target]] += 1
                                        aoe_targets_disadvantage += int(
                                            SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(location, target))

                            # add non-AoE targets and consider result
                            if aoe_targets:
                                consider_group(
                                    PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

                    else:
                        # loop over all aoe placements that hit characters
                        distances = self.find_proximity_distances(location)
                        for aoe_location in characters:
                            for aoe_pattern in aoe_pattern_list:
                                aoe_targets = []
                                aoe_targets_of_rank = [0] * num_focus_ranks
                                aoe_targets_disadvantage = 0
                                aoe_hexes = []

                                # loop over each hex in the aoe, adding targets
                                in_range = False
                                for aoe_offset in aoe_pattern:
                                    target = self.apply_aoe_offset(
                                        aoe_location, aoe_offset)
                                    if target:
                                        if distances[target] <= ATTACK_RANGE:
                                            in_range = True
                                        aoe_hexes.append(target)
                                        if target in characters:
                                            if self.test_los_between_locations(target, location):
                                                aoe_targets.append(target)
                                                aoe_targets_of_rank[focus_ranks[target]] += 1
                                                aoe_targets_disadvantage += int(
                                                    SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(location, target))

                                # add non-AoE targets and consider result
                                if in_range:
                                    if aoe_targets:
                                        consider_group(
                                            PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

            # given the target group, find the best destinations to attack from
            # based on the following priorities

            class u:
                destinations:set[tuple[int,int]] = set()
                aoes:dict[tuple[int],list[int]] = {}
                best_destination = (
                    MAX_VALUE - 1,  # number of targts with disadvantage
                    MAX_VALUE - 1,  # path length to the destination
                )

            def consider_destination(num_targets:int, preexisting_targets:list[int], preexisting_targets_of_rank:list[int], preexisting_targets_disadvantage:int, aoe_hexes:list[int]):
                available_targets = targetable_characters - \
                    set(preexisting_targets)
                max_num_targets = min(num_targets, len(
                    available_targets)) if not ALL_TARGETS else len(available_targets)

                # if its impossible to attack a group as big as a chosen target group
                if len(preexisting_targets) + max_num_targets != -t.best_group[3]:
                    return

                # loop over every possible set of potential targets
                for target_set in itertools.combinations(available_targets, max_num_targets):
                    targets = preexisting_targets + list(target_set)

                    # if this target group does not match any chosen group
                    group = tuple(sorted(targets))
                    if not group in t.groups:
                        continue

                    targets_disadvantage = preexisting_targets_disadvantage
                    for target in target_set:
                        targets_disadvantage += int(
                            SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(location, target))

                    this_destination = (
                        targets_disadvantage,
                        travel_distances[location],
                    )

                    if this_destination == u.best_destination:
                        action = (location, ) + group
                        u.destinations.add(action)
                        u.aoes[action] = aoe_hexes
                    elif this_destination < u.best_destination:
                        action = (location, ) + group
                        u.best_destination = this_destination
                        u.destinations = {action}
                        u.aoes = {action: aoe_hexes}
                    # print action, this_destination, u.best_destination
                    # print u.destinations

            for location in range(self.map_size):
                if self.can_end_move_on(self, location):

                    # early test of location using the first two elements of the minimized tuple

                    if trap_counts[location] != t.best_group[0]:
                        continue

                    can_reach_location = travel_distances[location] <= self.action_move
                    if -can_reach_location != t.best_group[1]:
                        continue

                    has_disadvantage_against_focus = SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(
                        location, focus)
                    if int(has_disadvantage_against_focus) != t.best_group[2]:
                        continue

                    # determine the set of characters attackable by non-AoE attacks
                    range_to_location = self.find_proximity_distances(location)
                    targetable_characters = {
                        _
                        for _ in characters
                        if range_to_location[_] <= ATTACK_RANGE and self.test_los_between_locations(_, location)
                    }

                    if not AOE_ACTION:
                        # add non-AoE targets and consider resulting actions
                        consider_destination(
                            1 + PLUS_TARGET_FOR_MOVEMENT, [], [0] * num_focus_ranks, 0, [])

                    elif AOE_MELEE:
                        # loop over every possible aoe placement
                        for aoe_rotation in range(12):
                            aoe_targets = []
                            aoe_targets_of_rank = [0] * num_focus_ranks
                            aoe_targets_disadvantage = 0
                            aoe_hexes = []

                            # loop over each hex in the aoe, adding targets
                            for aoe_offset in aoe:
                                target = self.apply_rotated_aoe_offset(
                                    location, aoe_offset, aoe_rotation)
                                aoe_hexes.append(target)
                                if target in characters:
                                    if self.test_los_between_locations(target, location):
                                        aoe_targets.append(target)
                                        aoe_targets_of_rank[focus_ranks[target]] += 1
                                        aoe_targets_disadvantage += int(
                                            SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(location, target))

                            # add non-AoE targets and consider result
                            if aoe_targets:
                                consider_destination(
                                    PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

                    else:
                        # loop over all aoe placements that hit characters
                        distances = self.find_proximity_distances(location)
                        for aoe_location in characters:
                            for aoe_pattern in aoe_pattern_list:
                                aoe_targets = []
                                aoe_targets_of_rank = [0] * num_focus_ranks
                                aoe_targets_disadvantage = 0
                                aoe_hexes = []

                                # loop over each hex in the aoe, adding targets
                                in_range = False
                                for aoe_offset in aoe_pattern:
                                    target = self.apply_aoe_offset(
                                        aoe_location, aoe_offset)
                                    if target:
                                        if distances[target] <= ATTACK_RANGE:
                                            in_range = True
                                        aoe_hexes.append(target)
                                        if target in characters:
                                            if self.test_los_between_locations(target, location):
                                                aoe_targets.append(target)
                                                aoe_targets_of_rank[focus_ranks[target]] += 1
                                                aoe_targets_disadvantage += int(
                                                    SUSCEPTIBLE_TO_DISADVANTAGE and self.is_adjacent(location, target))

                                # add non-AoE targets and consider result
                                if in_range:
                                    if aoe_targets:
                                        consider_destination(
                                            PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

            # determine the best move based on the chosen destinations

            can_reach_destinations = t.best_group[1] == -1
            actions_for_this_focus:set[tuple[int,int]] = []
            destinations_for_this_focus:dict[tuple[int],tuple[int,int]] = {}
            if can_reach_destinations:
                
                if PLUS_TARGET >= 0:
                    actions_for_this_focus = u.destinations
                    aoes_for_this_focus = u.aoes
                else:
                    actions_for_this_focus = [(_[0], ) for _ in u.destinations]
                    aoes_for_this_focus: dict[tuple[int], list[int]] = {_: []
                                           for _ in actions_for_this_focus}
                destinations_for_this_focus = {_: {_[0]} for _ in actions_for_this_focus}
            else:                
                for destination in u.destinations:
                    actions_for_this_destination = []
                    best_move = (
                        MAX_VALUE - 1,  # traps to destination and along travel
                        MAX_VALUE - 1,  # distance to destination
                        MAX_VALUE - 1,  # travel distance
                    )
                    distance_to_destination, traps_to_destination = self.find_path_distances_reverse(
                        destination[0], self.can_travel_through)
                    for location in range(self.map_size):
                        if travel_distances[location] <= self.action_move:
                            if self.can_end_move_on(self, location):
                                this_move = (
                                    traps_to_destination[location] +
                                    trap_counts[location],
                                    distance_to_destination[location],
                                    travel_distances[location],
                                )
                                if this_move == best_move:
                                    actions_for_this_destination.append(
                                        (location, ))
                                elif this_move < best_move:
                                    best_move = this_move
                                    actions_for_this_destination = [
                                        (location, )]
                                # print ( location, ), this_move, best_move
                                # print actions_for_this_destination

                    actions_for_this_focus += actions_for_this_destination

                    for action in actions_for_this_destination:
                        if action in destinations_for_this_focus:
                            destinations_for_this_focus[action].add(
                                destination[0])
                        else:
                            destinations_for_this_focus[action] = {
                                destination[0]}

                aoes_for_this_focus = {_: [] for _ in actions_for_this_focus}

            actions_for_this_focus = set(actions_for_this_focus)
            actions |= actions_for_this_focus
            aoes.update(aoes_for_this_focus)
            for action in actions_for_this_focus:
                if action in destinations:
                    destinations[action] |= destinations_for_this_focus[action]
                else:
                    destinations[action] = destinations_for_this_focus[action]
                if action in focus_map:
                    focus_map[action].add(focus)
                else:
                    focus_map[action] = {focus}

        # if we find no actions, stand still
        if not actions:
            action = (active_monster, )
            actions.add(action)
            aoes[action] = []
            destinations[action] = {}
            focus_map[action] = {}

        # calculate sightlines for visualization
        sightlines:dict[tuple[int,int],set[tuple[tuple[float, float], tuple[float, float]]]] = {}
        debug_lines:dict[tuple[int,int],set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]] = {}
        for action in actions:
            sightlines[action] = set()
            if action[1:]:
                for attack in action[1:]:
                    sightlines[action].add(
                        self.find_shortest_sightline(action[0], attack))

            debug_lines[action] = self.debug_lines
            self.debug_lines = set()

        # move monster
        if self.logging:
            self.figures[active_monster] = ' '
            map_debug_tags[active_monster] = 's'
            if not self.show_each_action_separately:
                for action in actions:
                    self.figures[action[0]] = 'A'
                    for destination in destinations[action]:
                        map_debug_tags[destination] = 'd'
                    for target in action[1:]:
                        map_debug_tags[target] = 'a'
                # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ], map_debug_tags )
            else:
                for action in actions:
                    figures = list(self.figures)
                    action_debug_tags = list(map_debug_tags)
                    figures[action[0]] = 'A'
                    for destination in destinations[action]:
                        action_debug_tags[destination] = 'd'
                    for target in action[1:]:
                        action_debug_tags[target] = 'a'
                    # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ], action_debug_tags )

        return actions, aoes, destinations, focus_map, sightlines, debug_lines

    def solve_reach(self, monster: int) -> list[tuple[int, int]]:
        if self.action_target == 0:
            return []
        if self.action_range == 0:
            ATTACK_RANGE = 1
        else:
            ATTACK_RANGE = self.action_range

        distances = self.find_proximity_distances(monster)

        reach:list[tuple[int,int]] = []
        run_begin = None
        for location in range(self.map_size):
            has_reach = False
            if distances[location] <= ATTACK_RANGE:
                if not self.blocks_los(location):
                    if location != monster:
                        if self.test_los_between_locations(monster, location):
                            has_reach = True
            if has_reach:
                if run_begin == None:
                    run_begin = location
            elif run_begin != None:
                reach.append((run_begin, location))
                run_begin = None
        if run_begin != None:
            reach.append((run_begin, self.map_size))
        return reach

    def solve_sight(self, monster: int) -> list[tuple[int, int]]:
        sight:list[tuple[int,int]] = []
        run_begin = None
        for location in range(self.map_size):
            has_sight = False
            if not self.blocks_los(location):
                if location != monster:
                    if self.test_los_between_locations(monster, location):
                        has_sight = True
            if has_sight:
                if run_begin == None:
                    run_begin = location
            elif run_begin != None:
                sight.append((run_begin, location))
                run_begin = None
        if run_begin != None:
            sight.append((run_begin, self.map_size))
        return sight

    def solve_reaches(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.solve_reach(_) for _ in viewpoints]

    def solve_sights(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.solve_sight(_) for _ in viewpoints]

    # def debug_plot_line(self, color, line):
    #     self.debug_lines.add((color, (scale_vector(
    #         DEBUG_PLOT_SCALE, line[0]), scale_vector(DEBUG_PLOT_SCALE, line[1]))))

    # def debug_plot_point(self, color, point):
    #     self.debug_lines.add(
    #         (color, (scale_vector(DEBUG_PLOT_SCALE, point), )))
