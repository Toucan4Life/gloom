from typing import Iterable
from solver.settings import *
from functools import cmp_to_key
from pipe import Pipe

COS_30 = math.cos(30.0 / 180.0 * math.pi)
EPSILON = 1e-12


# def debug(expression):
#     # traceback.print_stack()
#     frame = sys._getframe(1)
#     a = eval(expression, frame.f_globals, frame.f_locals)
#     r = pprint.pformat(a)
#     print('%s = %s' % (expression, r))

@Pipe
def minima(iterable,func):
    iterable = [x for x in iterable]
    if len(iterable) == 0 :
        return list()
    iterable = list(iterable)
    current_score:int=func(iterable[0])
    best_iterable:list[Any]=[iterable[0]]

    for _,candidate in enumerate(iterable[1:]):
        evaluation = func(candidate)
        if (current_score<evaluation):
            continue
        if(current_score==evaluation):
            best_iterable.append(candidate)
        else:
            current_score=evaluation
            best_iterable=[candidate]

    return best_iterable

def get_offset(center: int, location: int, grid_height: int) -> tuple[int, int, int]:
    location_row = location % grid_height
    location_column = location // grid_height
    center_row = center % grid_height
    center_column = center // grid_height

    x = location_row - center_row

    column_delta = center_column - location_column
    if center_column % 2 == 0:
        y = (column_delta + 1) // 2
    else:
        y = column_delta // 2

    z = column_delta - y

    return (x, y, z)


def apply_offset(center: int, offset: tuple[int, int, int], grid_height: int, grid_size: int) -> int:
    location = center
    column = center // grid_height

    column_delta = offset[1] + offset[2]

    location += offset[0] - offset[2]
    location -= column_delta * grid_height
    location += (column_delta + column % 2) // 2

    column -= column_delta

    # test whether we went off the top or bottom of the board
    final_column = location // grid_height
    if final_column != column:
        return -1

    # test whether we went off the left or right of the board
    if location < 0 or location >= grid_size:
        return -1

    return location


def rotate_offset(offset: tuple[int, int, int], rotation: int) -> tuple[int, int, int]:
    # rotations 6 through 11 are mirrored
    if rotation < 6:
        offsetRot = (offset[0], offset[1], offset[2], 0, 0, 0)
    else:
        rotation -= 6
        offsetRot = (offset[0], 0, 0, 0, offset[2], offset[1])

    offsetRot = offsetRot[rotation:] + offsetRot[:rotation]

    return (
        offsetRot[0] - offsetRot[3],
        offsetRot[1] - offsetRot[4],
        offsetRot[2] - offsetRot[5],
    )


def pin_offset(offset: tuple[int, int, int], pin: tuple[int, int, int]) -> tuple[int, int, int]:
    return (
        offset[0] - pin[0],
        offset[1] - pin[1],
        offset[2] - pin[2],
    )


def lengthen_line(line: tuple[tuple[float, float], tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    delta = (line[1][0] - line[0][0], line[1][1] - line[0][1])
    length = math.sqrt(delta[0] * delta[0] + delta[1] * delta[1])
    normal = (delta[0]/ length, delta[1]/ length)
    addition = (EPSILON * normal[0], EPSILON * normal[1])
    return (
        (line[0][0] - addition[0], line[0][1] - addition[1]),
        (line[1][0] + addition[0], line[1][1] + addition[1])
    )


def lerp(value_a: float, value_b: float, factor: float) -> float:
    return value_a + (value_b - value_a) * factor


def lerp_along_line(line: tuple[tuple[float, float], tuple[float, float]], factor: float) -> tuple[float, float]:
    return (lerp(line[0][0], line[1][0], factor), lerp(line[0][1], line[1][1], factor))


def dot_product(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> float:
    return vector_a[0] * vector_b[0] + vector_a[1] * vector_b[1]


def cross_product(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> float:
    return vector_a[0] * vector_b[1] - vector_a[1] * vector_b[0]


def direction(line: tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
    delta = (line[1][0] - line[0][0], line[1][1] - line[0][1])
    length = math.sqrt(delta[0] * delta[0] + delta[1] * delta[1])
    return (delta[0] / length, delta[1] / length)


def scale_vector(scalar: float, vector: tuple[float, float]) -> tuple[float, float]:
    return (scalar * vector[0], scalar * vector[1])


def add_vector(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> tuple[float, float]:
    return (vector_a[0] + vector_b[0], vector_a[1] + vector_b[1])


def line_line_intersection(line_a: tuple[tuple[float, float], tuple[float, float]], line_b: tuple[tuple[float, float], tuple[float, float]]) -> bool:
    line_a = lengthen_line(line_a)
    line_b = lengthen_line(line_b)

    a = line_a[0]
    b = line_a[1]
    c = line_b[0]
    d = line_b[1]
    denominator = ((b[0] - a[0]) * (d[1] - c[1])) - \
        ((b[1] - a[1]) * (d[0] - c[0]))
    numerator1 = ((a[1] - c[1]) * (d[0] - c[0])) - \
        ((a[0] - c[0]) * (d[1] - c[1]))
    numerator2 = ((a[1] - c[1]) * (b[0] - a[0])) - \
        ((a[0] - c[0]) * (b[1] - a[1]))

    # if parallel
    if denominator == 0:
        # if collinear
        if numerator1 == 0 and numerator2 == 0:
            if a[0] != b[0]:
                u = min(a[0], b[0])
                v = max(a[0], b[0])
                x = min(c[0], d[0])
                y = max(c[0], d[0])
            else:
                u = min(a[1], b[1])
                v = max(a[1], b[1])
                x = min(c[1], d[1])
                y = max(c[1], d[1])
            if x <= u <= y:
                return True
            if x <= v <= y:
                return True
            if x >= u >= y:
                return True
        return False

    r = numerator1 / denominator
    s = numerator2 / denominator

    return 0 <= r <= 1.0 and 0 <= s <= 1


def line_hex_edge_intersection(line_a: tuple[tuple[float, float], tuple[float, float]], line_b: tuple[tuple[float, float], tuple[float, float]]) -> float | None:
    line_a = lengthen_line(line_a)
    line_b = lengthen_line(line_b)

    a = line_a[0]
    b = line_a[1]
    c = line_b[0]
    d = line_b[1]
    denominator = ((b[0] - a[0]) * (d[1] - c[1])) - \
        ((b[1] - a[1]) * (d[0] - c[0]))
    numerator2 = ((a[1] - c[1]) * (b[0] - a[0])) - \
        ((a[0] - c[0]) * (b[1] - a[1]))

    # if parallel
    if denominator == 0:
        # never collinear
        return None

    s = numerator2 / denominator

    return s if 0 <= s <= 1.0 else None


def occluder_target_intersection(line_a: tuple[tuple[float, float], tuple[float, float]], line_b: tuple[tuple[float, float], tuple[float, float]]):
    a = line_a[0]
    b = line_a[1]
    c = line_b[0]
    d = line_b[1]
    denominator = ((b[0] - a[0]) * (d[1] - c[1])) - \
        ((b[1] - a[1]) * (d[0] - c[0]))
    numerator2 = ((a[1] - c[1]) * (b[0] - a[0])) - \
        ((a[0] - c[0]) * (b[1] - a[1]))
    # never parallel
    return numerator2 / denominator


def visibility_cache_key(location_a: int, location_b: int) -> tuple[int, int]:
    if location_a < location_b:
        return (location_a, location_b)
    else:
        return (location_b, location_a)


def calculate_distance(vertex_position_a: tuple[float, float], vertex_position_b: tuple[float, float]) -> float:
    delta_0 = vertex_position_b[0] - vertex_position_a[0]
    delta_1 = vertex_position_b[1] - vertex_position_a[1]
    distance = math.sqrt(delta_0 * delta_0 + delta_1 * delta_1)
    return distance


def within_bound(location: tuple[float, float], line: tuple[tuple[float, float], tuple[float, float]], line_direction: tuple[float, float]) -> bool:
    if location in (line[0], line[1]):
        return False
    bound_dir = line_direction
    location_dir = direction((line[0], location))
    return cross_product(bound_dir, location_dir) < -EPSILON


def occluder_less_than(xxx_todo_changeme: tuple[float, float], xxx_todo_changeme1: tuple[float, float]) -> bool:
    (value_a, slope_a) = xxx_todo_changeme
    (value_b, slope_b) = xxx_todo_changeme1
    if abs(value_a - value_b) < EPSILON:
        return slope_a < slope_b
    else:
        return value_a < value_b


def occluder_greater_than(xxx_todo_changeme2: tuple[float, float], xxx_todo_changeme3: tuple[float, float]) -> bool:
    (value_a, slope_a) = xxx_todo_changeme2
    (value_b, slope_b) = xxx_todo_changeme3
    if abs(value_a - value_b) < EPSILON:
        return slope_a > slope_b
    else:
        return value_a > value_b


def get_occluder_value_at(xxx_todo_changeme4: tuple[float, float, float], at: float) -> tuple[float, float]:
    (value_at_zero, value_at_one, slope) = xxx_todo_changeme4
    return lerp(value_at_zero, value_at_one, at), slope


def occluder_intersections(occluder_mappings: list[tuple[float, float, float]]) -> Iterable[float]:
    yield 0.0
    for index, occluder_a in enumerate(occluder_mappings):
        for occluder_b in occluder_mappings[:index]:
            divisor = occluder_a[2] - occluder_b[2]
            if divisor == 0.0:
                continue
            t = (occluder_b[0] - occluder_a[0]) / divisor
            if EPSILON < t < 1.0 - EPSILON:
                yield t


def intersection_close(value_a: float, value_b: float) -> bool:
    return abs(value_a - value_b) < EPSILON


def find_previous_intersection(t: float, intersections: list[tuple[float, int, float]]) -> int:
    for index, intersection in enumerate(intersections):
        if intersection_close(t, intersection[0]):
            return index
        if t < intersection[0]:
            return index - 1
    return -1


def find_intersection_at(t: float, intersections: list[tuple[float, int, float]]) -> int:
    for index, intersection in enumerate(intersections):
        if intersection_close(t, intersection[0]):
            return index
    return -1


def get_visibility_windows_at(
        x: float,
        occluder_mapping_set: tuple[
            list[tuple[float, float, float]],
            list[tuple[tuple[float, float, float], int]],
            list[tuple[tuple[float, float, float], int]],
            list[tuple[tuple[float, float, float], tuple[float, float, float], int, int]]]) -> list[tuple[float, float, float, int]]:

    occluder_mappings_below = occluder_mapping_set[1]
    occluder_mappings_above = occluder_mapping_set[2]
    occluder_mappings_internal = occluder_mapping_set[3]
    # is there a visibility window at this point
    # use slope to determine whether a visibility window is opening or closing

    window_bottom = 0.0
    window_top = 1.0
    window_bottom_slope = 0.0
    window_top_slope = 0.0
    window_top_mapping_index = 1

    # determine the visibility window by finding the tightest occluders from above and below
    for occluder, _ in occluder_mappings_below:
        value, slope = get_occluder_value_at(occluder, x)
        if occluder_greater_than((value, slope), (window_bottom, window_bottom_slope)):
            window_bottom = value
            window_bottom_slope = slope
    for occluder, mapping_index in occluder_mappings_above:
        value, slope = get_occluder_value_at(occluder, x)
        if occluder_less_than((value, slope), (window_top, window_top_slope)):
            window_top = value
            window_top_slope = slope
            window_top_mapping_index = mapping_index

    if occluder_greater_than((window_bottom, window_bottom_slope + EPSILON), (window_top, window_top_slope)):
        # no visibility window exists
        return []

    if len(occluder_mappings_internal) == 0:
        # a visibility window exists and there are no internal occluders to cover it
        return [(x, window_bottom, window_top, window_top_mapping_index)]

    # build a sorted list of internal occluders in the window
    internal_values : list[tuple[float, float, int,float,float,int]]
    internal_values=[]
    for internal_occluder in occluder_mappings_internal:
        value_a, slope_a = get_occluder_value_at(internal_occluder[0], x)
        value_b, slope_b = get_occluder_value_at(internal_occluder[1], x)
        mapping_idx_a, mapping_idx_b = internal_occluder[2], internal_occluder[3]
        if occluder_greater_than((value_a, slope_a), (value_b, slope_b)):
            (value_a, slope_a, mapping_idx_a), (value_b, slope_b, mapping_idx_b) = (
                value_b, slope_b, mapping_idx_b), (value_a, slope_a, mapping_idx_a)

        if occluder_greater_than((value_a, slope_a), (window_top, window_top_slope)):
            continue
        if occluder_less_than((value_b, slope_b), (window_bottom, window_bottom_slope)):
            continue
        internal_values.append((value_a, slope_a, mapping_idx_a, value_b, slope_b, mapping_idx_b))
        
    internal_values.sort(key=cmp_to_key(lambda occluder_a, occluder_b:
                                        -1 if occluder_less_than(
                                            (occluder_a[0], occluder_a[1]), (occluder_b[0], occluder_b[1])) else 1
                                        ))

    # loop over the internal occluders from lowest starting point to highest
    windows : list[tuple[float, float,float, int]]
    windows=[]
    for internal_value in internal_values:
        if occluder_greater_than((internal_value[0], internal_value[1] - EPSILON), (window_bottom, window_bottom_slope)):
            # there is a visibility gap below the lowest internal occluder; record then find further windows
            windows.append(
                (x, window_bottom, internal_value[0], internal_value[2]))
            if occluder_greater_than((internal_value[3], internal_value[4] + EPSILON), (window_top, window_top_slope)):
                break
            window_bottom = internal_value[3]
            window_bottom_slope = internal_value[4]
            continue

        if occluder_greater_than((internal_value[3], internal_value[4] + EPSILON), (window_top, window_top_slope)):
            # the internal occluder fully covers the visibilty window; there is no visibility at this intersection
            break

        if occluder_greater_than((internal_value[3], internal_value[4]), (window_bottom, window_bottom_slope)):
            # this internal occluder partially covers the visibilty window; reduce the window
            window_bottom = internal_value[3]
            window_bottom_slope = internal_value[4]
            continue

        
        # this internal occluder is fully below the visibility window and has no impact
        continue

    else:
        # the internal occluders did not cover the visibility window
        windows.append((x, window_bottom, window_top,
                       window_top_mapping_index))

    return windows


def get_line_intersections(line_index: int, occluder_mappings: list[tuple[float, float, float]]) -> list[tuple[float, int, float]]:
    left_wall_index = len(occluder_mappings)
    if line_index < left_wall_index:
        occluder_a = occluder_mappings[line_index]
        intersections = [
            (0.0, left_wall_index, occluder_a[0]),
            (1.0, left_wall_index + 1, occluder_a[1]),
        ]
        for index, occluder_b in enumerate(occluder_mappings):
            divisor = occluder_a[2] - occluder_b[2]
            if divisor == 0.0:
                continue
            intersection = (occluder_b[0] - occluder_a[0])/ divisor
            if intersection > -EPSILON and intersection < 1.0 + EPSILON:
                intersections.append((intersection, index, intersection))

    elif line_index == left_wall_index:
        intersections = [(occluder_mappings[_][0], _, 0.0)
                         for _ in range(len(occluder_mappings))]

    else:
        intersections = [(occluder_mappings[_][1], _, 1.0)
                         for _ in range(len(occluder_mappings))]

    intersections.sort()
    return intersections


def find_intersection_exit(
    occluder_index: int,
    traversing_backwards: bool,
    potential_exits: list[tuple[float, int, float]],
    lines: list[tuple[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[float, float]]]) -> tuple[tuple[float, int, float], bool]:

    best_cross = 0.0
    best_exit = (0.0, 0, 0.0)
    best_exit_is_backwards = False

    current_line_direction = lines[occluder_index][1]
    if traversing_backwards:
        current_line_direction = scale_vector(-1.0, current_line_direction)

    for exit in potential_exits:
        exit_line_direction = lines[exit[1]][1]

        cross = cross_product(exit_line_direction, current_line_direction)
        dot = dot_product(exit_line_direction, current_line_direction)
        backwards = cross < 0.0
        if backwards:
            cross = -cross
            dot = -dot
        if dot < 0.0:
            cross = 2.0 - cross
        if cross > best_cross:
            best_cross = cross
            best_exit = exit
            best_exit_is_backwards = backwards

    return best_exit, best_exit_is_backwards


def calculate_polygon_properties(polygon: list[tuple[float, float]]) -> tuple[float, tuple[float, float]]:
    center_of_mass = (0, 0)
    area = 0.0

    vertex_count = len(polygon)

    prev_bot_index = prev_top_index = min(
        list(range(len(polygon))), key=polygon.__getitem__)
    (prev_bot_x, prev_bot_y) = (prev_top_x,
                                prev_top_y) = polygon[prev_top_index]

    next_top_index = (prev_top_index + 1) % vertex_count
    (next_top_x, next_top_y) = polygon[next_top_index]

    next_bot_index = (prev_bot_index - 1 + vertex_count) % vertex_count
    (next_bot_x, next_bot_y) = polygon[next_bot_index]

    x = prev_top_x
    while True:
        if next_top_x != prev_top_x and next_bot_x != prev_bot_x:
            x_l = x
            x_r = next_top_x if next_top_x < next_bot_x else next_bot_x
            top_y_l = lerp(prev_top_y, next_top_y, 
                (x_l - prev_top_x)/ (next_top_x - prev_top_x))
            top_y_r = lerp(prev_top_y, next_top_y, 
                (x_r - prev_top_x)/ (next_top_x - prev_top_x))
            bot_y_l = lerp(prev_bot_y, next_bot_y, 
                (x_l - prev_bot_x)/ (next_bot_x - prev_bot_x))
            bot_y_r = lerp(prev_bot_y, next_bot_y, 
                (x_r - prev_bot_x)/ (next_bot_x - prev_bot_x))

            delta_x = x_r - x_l

            top_y_max = max(top_y_l, top_y_r)
            top_y_min = min(top_y_l, top_y_r)
            bot_y_max = max(bot_y_l, bot_y_r)
            bot_y_min = min(bot_y_l, bot_y_r)

            area_square = delta_x * (top_y_max - bot_y_min)
            area_top_triangle = 0.5 * delta_x * (top_y_max - top_y_min)
            area_bot_triangle = 0.5 * delta_x * (bot_y_max - bot_y_min)
            subsection_area = area_square - area_top_triangle - area_bot_triangle

            center_of_mass_square = (
                0.5 * (x_r + x_l),
                0.5 * (top_y_max + bot_y_min)
            )

            center_of_mass_top_triangle = (
                (x_l + delta_x/ 3.0 if top_y_l < top_y_r else x_r - delta_x/ 3.0),
                (top_y_min + 2.0 * top_y_max)/ 3.0
            )

            center_of_mass_bot_triangle = (
                (x_l + delta_x/ 3.0 if bot_y_l > bot_y_r else x_r - delta_x/ 3.0),
                (bot_y_max + 2.0 * bot_y_min)/ 3.0
            )

            center_of_mass_square = scale_vector(
                area_square, center_of_mass_square)
            center_of_mass_top_triangle = scale_vector(
                -area_top_triangle, center_of_mass_top_triangle)
            center_of_mass_bot_triangle = scale_vector(
                -area_bot_triangle, center_of_mass_bot_triangle)

            subsection_center_of_mass = add_vector(
                center_of_mass_square, center_of_mass_top_triangle)
            subsection_center_of_mass = add_vector(
                subsection_center_of_mass, center_of_mass_bot_triangle)

            area += subsection_area
            center_of_mass = add_vector(
                center_of_mass, subsection_center_of_mass)

        if next_top_index == next_bot_index:
            break

        if next_top_x < next_bot_x:
            x = next_top_x
            prev_top_index = next_top_index
            next_top_index = (next_top_index + 1) % vertex_count
            (prev_top_x, prev_top_y) = (next_top_x, next_top_y)
            (next_top_x, next_top_y) = polygon[next_top_index]
        else:
            x = next_bot_x
            prev_bot_index = next_bot_index
            next_bot_index = (next_bot_index - 1 + vertex_count) % vertex_count
            (prev_bot_x, prev_bot_y) = (next_bot_x, next_bot_y)
            (next_bot_x, next_bot_y) = polygon[next_bot_index]

    center_of_mass = scale_vector(1.0/ area, center_of_mass)
    return area, center_of_mass


def map_window_polygon(
    window: tuple[float, float, float, int],
    previous_starts: list[tuple[float, float]],
    occluder_mappings: list[tuple[float, float, float]],
    lines: list[tuple[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[float, float]]])-> None|list[tuple[float,float]]:
        
    # build a polygon around the window
    polygon:list[tuple[float,float]]
    polygon = []    
    # start at the top of the window and traverse the line counterclockwise
    # to the first vertex
    line_index = window[3]
    intersections = get_line_intersections(line_index, occluder_mappings)
    intersection_index = find_previous_intersection(window[0], intersections)
    t = intersections[intersection_index][0]
    traversing_backwards = False

    start = (line_index, intersection_index)
    if start in previous_starts:
        # we already mapped this polygon
        return None
    previous_starts.append(start)

    # walk the polygon clockwise until it is closed
    while True:

        # add this vertex to the polygon
        vertex = lerp_along_line(lines[line_index][0], t)
        if len(polygon) >= 3:
            if intersection_close(polygon[0][0], vertex[0]):
                if intersection_close(polygon[0][1], vertex[1]):
                    # the polygon is closed
                    return polygon
        polygon.append(vertex)

        # step to the next intersection along the current line
        previous_t = t
        while True:
            intersection_index += -1 if traversing_backwards else 1
            t = intersections[intersection_index][0]
            if not intersection_close(previous_t, t):
                break

        # find the intersecting line with the tightest inward angle
        potential_exits = [
            _ for _ in intersections if intersection_close(_[0], t)]
        (_, line_index, t), traversing_backwards = find_intersection_exit(
            line_index, traversing_backwards, potential_exits, lines)
        intersections = get_line_intersections(line_index, occluder_mappings)
        intersection_index = find_intersection_at(t, intersections)
