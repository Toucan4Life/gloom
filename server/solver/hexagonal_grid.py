from solver.utils import *
import collections

class hexagonal_grid:
    def __init__(self, width: int, height: int):
        self.map_width = width
        self.map_height = height
        self.map_size = self.map_width * self.map_height
        self.neighbors: dict[int, list[int]]= {}
        self.walls: list[list[bool]]
        self.contents: list[str]
        self.effective_walls:list[list[bool]]
        self.extra_walls:list[list[bool]]
        self.vertices:list[tuple[float, float]]
        self.visibility_cache :dict[tuple[int,int],bool]={}
        self.path_cache : dict[int,list[int]]=[{}]
        self.path_cache_with_range : dict[int,list[int]]=[{}]
    #Gloomhaven logic below
    def prepare_map(self,walls: list[list[bool]], contents: list[str]) -> None:
        self.walls = walls
        self.contents = contents
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

    def does_block_los(self,  location: int) -> bool:
        return self.contents[location] == 'X'

    def additional_path_cost(self, location: int) -> int:
        return int(self.contents[location] == 'D')

    def get_vertex(self, location: int, vertex: int) -> tuple[float, float]:
        return self.vertices[location * 6 + vertex]
                                        
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

                if self.does_block_los(location):
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

                if self.does_block_los(location):
                    encoded_wall += 1 << 3

                if encoded_wall != 0:
                    yield location, encoded_wall

    def test_line(self, bounds: tuple[int, int, int, int], vertex_position_a: tuple[float, float], vertex_position_b: tuple[float, float]) -> bool:
        if vertex_position_a == vertex_position_b:
            return True

        return all((not line_line_intersection((vertex_position_a, vertex_position_b), occluder) for occluder in self.occluders_in(bounds)))

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

    def test_los_between_locations(self, location_a: int, location_b: int, rule_vertex_los:bool) -> bool:
        cache_key = visibility_cache_key(location_a, location_b)
        if cache_key in self.visibility_cache:
            return self.visibility_cache[cache_key]

        if not rule_vertex_los:
            result = self.test_full_hex_los_between_locations(
                location_a, location_b)
        else:
            result = self.test_vertex_los_between_locations(
                location_a, location_b)

        self.visibility_cache[cache_key] = result
        return result

    def test_vertex_los_between_locations(self, location_a: int, location_b: int) -> bool:
        bounds = self.calculate_bounds(location_a, location_b)        

        return any((self.test_line(bounds, self.get_vertex(location_a, vertex_a), self.get_vertex(location_b, vertex_b))
                    for vertex_a in range(6) for vertex_b in range(6)
                    if not self.vertex_at_wall(location_b, vertex_b)
                    and not self.vertex_at_wall(location_a, vertex_a)))
        

    def find_shortest_sightline(self, location_a: int, location_b: int, rule_vertex_los:bool) -> tuple[tuple[float, float], tuple[float, float]]:
        if not rule_vertex_los:
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

    def find_proximity_distances(self, start: int) -> list[int]:
        cache_key = (start)
        if cache_key in self.path_cache[0]:
            return self.path_cache[0][cache_key]

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
                if self.does_block_los(neighbor):
                    continue
                if self.walls[current][edge]:
                    continue
                neighbor_distance = distance + 1
                if neighbor_distance < distances[neighbor]:
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance

        self.path_cache[0][cache_key] = distances
        return distances

    def find_proximity_distances_within_range(self, start: int, range:int) -> list[int]:
        cache_key = (start,range)
        if cache_key in self.path_cache_with_range[0]:
          return self.path_cache_with_range[0][cache_key]

        distances = [MAX_VALUE] * self.map_size

        frontier:collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0
        neighbor_distance =0
        while len(frontier) != 0:
            current = frontier.popleft()
            distance = distances[current]
            for edge, neighbor in enumerate(self.neighbors[current]):

                if neighbor == -1:
                    continue
                if self.does_block_los(neighbor):
                    continue
                if self.walls[current][edge]:
                    continue

                neighbor_distance = distance + 1
                if neighbor_distance -1 > range :
                    distances = [distance[0] for distance in enumerate(distances) if 0 < distance[1] <= range]                  
                    self.path_cache_with_range[0][cache_key] = distances
                    return distances
                elif neighbor_distance < distances[neighbor]:
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance

        distances = [distance[0] for distance in enumerate(distances) if 0 < distance[1] <= range]
        self.path_cache_with_range[0][cache_key] = distances
        return distances

    def to_axial_coordinate(self, location:int, height:int) -> tuple[int,int]:
        column = location % height
        row = location // height
        return (column - row // 2, row)
        
    def crow_flies_distances(self, start:int, end:int)->int:
        axial_start = self.to_axial_coordinate(start,self.map_height)
        axial_end = self.to_axial_coordinate(end,self.map_height)
        return int((abs(axial_start[0] - axial_end[0]) 
          + abs(axial_start[0] + axial_start[1] - axial_end[0] - axial_end[1])
          + abs(axial_start[1] - axial_end[1])) / 2)

    def from_axial_coordinate(self, coordinate:tuple[int,int], height:int, width:int)->int:
       
        column = coordinate[1]
        if not (0 <= column < width):
            return -1
        row = coordinate[0]
        if not (0 - column // 2 <= row < height - column // 2):
            return -1
        return row + column // 2 + column * height

    def solve_sight(self, monster: int,upper_bound:int, RULE_VERTEX_LOS:bool) -> list[tuple[int, int]]:

        distances = self.find_proximity_distances(monster)

        reach: list[tuple[int, int]] = []
        has_run_begun = False
        run = 0
        for location in range(self.map_size):
            if distances[location] <= upper_bound and not self.does_block_los(location) and location != monster and self.test_los_between_locations(monster, location, RULE_VERTEX_LOS):
                if not has_run_begun :
                    run = location
                    has_run_begun = True
            elif has_run_begun :
                reach.append((run, location))
                has_run_begun = False

        if has_run_begun :
            reach.append((run, self.map_size))
        return reach

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