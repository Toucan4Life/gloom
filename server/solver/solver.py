import collections
import textwrap
import itertools
from solver.utils import *
from solver.settings import *
from solver.print_map import *
from solver.hexagonal_grid import *
class Scenario:
    logging:bool
    debug_visuals:bool
    show_each_action_separately:bool
    debug_lines: set[tuple[int,tuple[tuple[float,float],tuple[float,float]]]]
    action_move:int
    action_range:int
    action_target:int
    flying:bool
    jumping:bool
    muddled:bool
    debug_toggle:bool
    message:str

    figures:list[str]
    initiatives:list[int]
    aoe_width:int
    aoe_height:int
    aoe_size:int
    aoe:list[bool]
    aoe_center:int
    walls:list[list[bool]]
    contents:list[str]

    def __init__(self, width: int, height: int, aoe_width: int, aoe_height: int):
        self.map = hexagonal_grid(width, height)
        self.logging = False
        self.debug_visuals = False
        self.show_each_action_separately = False
        self.debug_lines = set()

        self.figures = [' '] * self.map.map_size
        self.initiatives = [0] * self.map.map_size

        self.aoe_width = aoe_width
        self.aoe_height = aoe_height
        self.aoe_size = self.aoe_width * self.aoe_height
        self.aoe_center = (self.aoe_size - 1) // 2
        self.aoe = [False] * self.aoe_size
        self.walls = [[False] * 6 for _ in range(self.map.map_size)]
        self.contents = [' '] * self.map.map_size
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
            
    def prepare_map(self) -> None:
        self.map.prepare_map(self.walls, self.contents)

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

    def can_end_move_on(self, location: int) -> bool:
        if(self.flying):
            return self.map.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']

    def can_travel_through(self, location: int) -> bool:
        if(self.flying | self.jumping):
            return self.map.contents[location] in [' ', 'T', 'H', 'D', 'O']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] != 'C'

    def is_trap(self, location: int) -> bool:
        if(self.flying):
            return False
        return self.map.contents[location] in ['T', 'H']

    def find_path_distances(self, start: int) -> tuple[list[int], list[int]]:

        distances = [MAX_VALUE] * self.map.map_size
        traps = [MAX_VALUE] * self.map.map_size

        frontier:collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0
        traps[start] = 0

        while not len(frontier) == 0:
            current = frontier.popleft()
            distance = distances[current]
            trap = traps[current]
            for edge, neighbor in enumerate(self.map.neighbors[current]):
                if neighbor == -1:
                    continue
                if not self.can_travel_through(neighbor):
                    continue
                if self.map.walls[current][edge]:
                    continue
                neighbor_distance = distance + 1 + \
                    int(not self.flying and not self.jumping and self.map.additional_path_cost(
                        neighbor))
                neighbor_trap = int(not self.jumping) * \
                    trap + int(self.is_trap(neighbor))
                if (neighbor_trap, neighbor_distance) < (traps[neighbor], distances[neighbor]):
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance
                    traps[neighbor] = neighbor_trap

        if self.RULE_DIFFICULT_TERRAIN_JUMP:
            if self.jumping:
                for location in range(self.map.map_size):
                    distances[location] += self.map.additional_path_cost(location)
                distances[start] -= self.map.additional_path_cost(start)

        return distances, traps

    def find_path_distances_reverse(self, destination: int) -> tuple[list[int], list[int]]:
        # reverse in that we find the path distance to the destination from every location
        # path distance is symetric except for difficult terrain and traps
        # we correct for the asymetry of starting vs ending on difficult terrain
        # we correct for the asymetry of starting vs ending on traps

        distances, traps = self.find_path_distances(
            destination)
        distances = list(distances)
        traps = list(traps)
        if not self.flying:
            if not self.jumping or self.RULE_DIFFICULT_TERRAIN_JUMP:
                destination_additional_path_cost = self.map.additional_path_cost(
                    destination)
                if destination_additional_path_cost > 0:
                    distances = [
                        _ + destination_additional_path_cost if _ != MAX_VALUE else _ for _ in distances]
                for location in range(self.map.map_size):
                    distances[location] -= self.map.additional_path_cost(location)

            if self.is_trap(destination):
                traps = [_ + 1 if _ != MAX_VALUE else _ for _ in traps]
            for location in range(self.map.map_size):
                traps[location] -= int(self.is_trap(location))

        return distances, traps
 
    def calculate_monster_move(self) -> tuple[
        set[tuple[int,int,int]],
        dict[tuple[int,int,int],tuple[int,int,int]],
        dict[tuple[int,int,int],set[int]],
        dict[tuple[int,int,int],set[int]],
        dict[tuple[int,int,int],set[tuple[tuple[float,float],tuple[tuple[float,float]]]]],
        dict[tuple[int,int,int],set[int]]]:
        map_debug_tags = [' '] * self.map.map_size
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
            active_monster)
        proximity_distances = self.map.find_proximity_distances(active_monster)
        # rev_travel_distances, rev_trap_counts = self.find_path_distances_reverse( active_monster)
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
            list(range(self.map.map_size)), key=lambda x: travel_distances[x])
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
                    if self.map.test_los_between_locations(character, location, self.RULE_VERTEX_LOS):
                        s.focuses.add(character)
                if this_path < s.shortest_path:
                    if self.map.test_los_between_locations(character, location, self.RULE_VERTEX_LOS):
                        s.shortest_path = this_path
                        s.focuses = {character}

            for character in characters:
                range_to_character = self.map.find_proximity_distances(character)
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
                        if self.can_end_move_on(location):
                            if not AOE_ACTION or PLUS_TARGET > 0:
                                if range_to_character[location] <= ATTACK_RANGE:
                                    consider_focus()
                                    return
                            if AOE_ACTION:
                                if AOE_MELEE:
                                    for aoe_rotation in range(12):
                                        for aoe_offset in aoe:
                                            if character == self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation):
                                                consider_focus()
                                                return
                                else:
                                    distances = self.map.find_proximity_distances(
                                        location)
                                    for aoe_pattern in aoe_pattern_list:
                                        for aoe_offset in aoe_pattern:
                                            target = self.map.apply_aoe_offset(
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

            for location in range(self.map.map_size):
                if self.can_end_move_on(location):
                    can_reach_location = travel_distances[location] <= self.action_move

                    # early test of location using the first two elements of the minimized tuple
                    if trap_counts[location] > t.best_group[0]:
                        continue
                    if trap_counts[location] == t.best_group[0]:
                        if not can_reach_location and t.best_group[1] == -1:
                            continue

                    has_disadvantage_against_focus = SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(
                        location, focus)

                    # determine the set of characters attackable by non-AoE attacks
                    range_to_location = self.map.find_proximity_distances(location)
                    targetable_characters = {
                        _
                        for _ in characters
                        if range_to_location[_] <= ATTACK_RANGE and self.map.test_los_between_locations(_, location,self.RULE_VERTEX_LOS)
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
                                target = self.map.apply_rotated_aoe_offset(
                                    location, aoe_offset, aoe_rotation)
                                aoe_hexes.append(target)
                                if target in characters:
                                    if self.map.test_los_between_locations(target, location,self.RULE_VERTEX_LOS):
                                        aoe_targets.append(target)
                                        aoe_targets_of_rank[focus_ranks[target]] += 1
                                        aoe_targets_disadvantage += int(
                                            SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(location, target))

                            # add non-AoE targets and consider result
                            if aoe_targets:
                                consider_group(
                                    PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

                    else:
                        # loop over all aoe placements that hit characters
                        distances = self.map.find_proximity_distances(location)
                        for aoe_location in characters:
                            for aoe_pattern in aoe_pattern_list:
                                aoe_targets = []
                                aoe_targets_of_rank = [0] * num_focus_ranks
                                aoe_targets_disadvantage = 0
                                aoe_hexes = []

                                # loop over each hex in the aoe, adding targets
                                in_range = False
                                for aoe_offset in aoe_pattern:
                                    target = self.map.apply_aoe_offset(
                                        aoe_location, aoe_offset)
                                    if target:
                                        if distances[target] <= ATTACK_RANGE:
                                            in_range = True
                                        aoe_hexes.append(target)
                                        if target in characters:
                                            if self.map.test_los_between_locations(target, location,self.RULE_VERTEX_LOS):
                                                aoe_targets.append(target)
                                                aoe_targets_of_rank[focus_ranks[target]] += 1
                                                aoe_targets_disadvantage += int(
                                                    SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(location, target))

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
                            SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(location, target))

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

            for location in range(self.map.map_size):
                if self.can_end_move_on(location):

                    # early test of location using the first two elements of the minimized tuple

                    if trap_counts[location] != t.best_group[0]:
                        continue

                    can_reach_location = travel_distances[location] <= self.action_move
                    if -can_reach_location != t.best_group[1]:
                        continue

                    has_disadvantage_against_focus = SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(
                        location, focus)
                    if int(has_disadvantage_against_focus) != t.best_group[2]:
                        continue

                    # determine the set of characters attackable by non-AoE attacks
                    range_to_location = self.map.find_proximity_distances(location)
                    targetable_characters = {
                        _
                        for _ in characters
                        if range_to_location[_] <= ATTACK_RANGE and self.map.test_los_between_locations(_, location,self.RULE_VERTEX_LOS)
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
                                target = self.map.apply_rotated_aoe_offset(
                                    location, aoe_offset, aoe_rotation)
                                aoe_hexes.append(target)
                                if target in characters:
                                    if self.map.test_los_between_locations(target, location,self.RULE_VERTEX_LOS):
                                        aoe_targets.append(target)
                                        aoe_targets_of_rank[focus_ranks[target]] += 1
                                        aoe_targets_disadvantage += int(
                                            SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(location, target))

                            # add non-AoE targets and consider result
                            if aoe_targets:
                                consider_destination(
                                    PLUS_TARGET, aoe_targets, aoe_targets_of_rank, aoe_targets_disadvantage, aoe_hexes)

                    else:
                        # loop over all aoe placements that hit characters
                        distances = self.map.find_proximity_distances(location)
                        for aoe_location in characters:
                            for aoe_pattern in aoe_pattern_list:
                                aoe_targets = []
                                aoe_targets_of_rank = [0] * num_focus_ranks
                                aoe_targets_disadvantage = 0
                                aoe_hexes = []

                                # loop over each hex in the aoe, adding targets
                                in_range = False
                                for aoe_offset in aoe_pattern:
                                    target = self.map.apply_aoe_offset(
                                        aoe_location, aoe_offset)
                                    if target:
                                        if distances[target] <= ATTACK_RANGE:
                                            in_range = True
                                        aoe_hexes.append(target)
                                        if target in characters:
                                            if self.map.test_los_between_locations(target, location,self.RULE_VERTEX_LOS):
                                                aoe_targets.append(target)
                                                aoe_targets_of_rank[focus_ranks[target]] += 1
                                                aoe_targets_disadvantage += int(
                                                    SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(location, target))

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
                        destination[0])
                    for location in range(self.map.map_size):
                        if travel_distances[location] <= self.action_move:
                            if self.can_end_move_on(location):
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
                        self.map.find_shortest_sightline(action[0], attack,self.RULE_VERTEX_LOS))

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

        distances = self.map.find_proximity_distances(monster)

        reach:list[tuple[int,int]] = []
        run_begin = None
        for location in range(self.map.map_size):
            has_reach = False
            if distances[location] <= ATTACK_RANGE:
                if not self.map.blocks_los(location):
                    if location != monster:
                        if self.map.test_los_between_locations(monster, location,self.RULE_VERTEX_LOS):
                            has_reach = True
            if has_reach:
                if run_begin == None:
                    run_begin = location
            elif run_begin != None:
                reach.append((run_begin, location))
                run_begin = None
        if run_begin != None:
            reach.append((run_begin, self.map.map_size))
        return reach

    def solve_sight(self, monster: int) -> list[tuple[int, int]]:
        sight:list[tuple[int,int]] = []
        run_begin = None
        for location in range(self.map.map_size):
            has_sight = False
            if not self.map.blocks_los(location):
                if location != monster:
                    if self.map.test_los_between_locations(monster, location,self.RULE_VERTEX_LOS):
                        has_sight = True
            if has_sight:
                if run_begin == None:
                    run_begin = location
            elif run_begin != None:
                sight.append((run_begin, location))
                run_begin = None
        if run_begin != None:
            sight.append((run_begin, self.map.map_size))
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

        # def dereduce_location(self, location: int) -> int:
        #     return location
        