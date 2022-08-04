import collections
import textwrap
import itertools
from solver.hexagonal_grid import hexagonal_grid
from solver.settings import MAX_VALUE
from solver.utils import get_offset, pin_offset, rotate_offset, apply_offset

class Scenario:
    logging: bool
    debug_visuals: bool
    show_each_action_separately: bool
    debug_lines: set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]
    action_move: int
    action_range: int
    action_target: int
    flying: bool
    jumping: bool
    muddled: bool
    debug_toggle: bool
    message: str

    figures: list[str]
    initiatives: list[int]
    aoe_width: int
    aoe_height: int
    aoe_size: int
    aoe: list[bool]
    aoe_center: int
    walls: list[list[bool]]
    contents: list[str]

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
        # RULE_PROXIMITY_FOCUS:           proximity is ignored when determining monster focus

        self.RULE_VERTEX_LOS = self.GLOOM_RULES
        self.RULE_DIFFICULT_TERRAIN_JUMP = self.GLOOM_RULES 
        self.RULE_PROXIMITY_FOCUS = self.JOTL_RULES

    def can_end_move_on(self, location: int) -> bool:
        if self.flying:
            return self.map.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']

    def can_travel_through(self, location: int) -> bool:
        if self.flying | self.jumping:
            return self.map.contents[location] in [' ', 'T', 'H', 'D', 'O']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] != 'C'

    def is_trap(self, location: int) -> bool:
        if self.flying:
            return False
        return self.map.contents[location] in ['T', 'H']

    def find_path_distances(self, start: int) -> tuple[list[int], list[int]]:

        distances = [MAX_VALUE] * self.map.map_size
        traps = [MAX_VALUE] * self.map.map_size

        frontier: collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0
        traps[start] = 0

        while len(frontier) != 0:
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

        if self.RULE_DIFFICULT_TERRAIN_JUMP and self.jumping:
            for location in range(self.map.map_size):
                distances[location] += self.map.additional_path_cost(
                    location)
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
                    distances[location] -= self.map.additional_path_cost(
                        location)

            if self.is_trap(destination):
                traps = [_ + 1 if _ != MAX_VALUE else _ for _ in traps]
            for location in range(self.map.map_size):
                traps[location] -= int(self.is_trap(location))

        return distances, traps

    def calculate_monster_move(self) -> list[tuple[
        int,
        list[int],
        list[int],
        set[int],
        set[tuple[tuple[float, float], tuple[float, float]]],
        set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]],
        set[int]]]:

        ATTACK_RANGE = 1 if self.action_range == 0 or self.action_target == 0 else self.action_range
        SUSCEPTIBLE_TO_DISADVANTAGE = False if self.action_range == 0 or self.action_target == 0 else not self.muddled
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

        # find active monster
        active_monster = self.figures.index('A')
        travel_distances, trap_counts = self.find_path_distances(active_monster)
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
        travel_distance_sorted_map = sorted(list(range(self.map.map_size)), key=lambda x: travel_distances[x])
        # process aoe
        
        aoe, aoe_pattern_list = self.process_aoe(AOE_MELEE) if AOE_ACTION else ([],[])

        # find characters
        characters = [_ for _, figure in enumerate(self.figures) if figure == 'C']

        if not len(characters):
            return [(active_monster, list(), list(), set(), set(), self.debug_lines, set())]

        # find monster focuses
        focuses, focus_ranks = self.find_focus(
            ATTACK_RANGE, AOE_ACTION, AOE_MELEE, travel_distances, trap_counts, proximity_distances,
             travel_distance_sorted_map, aoe, aoe_pattern_list, characters)
        # if we find no actions, stand still

        if not focuses:
            return [(active_monster, list(), list(), set(), set(), self.debug_lines, set())]

        info: list[tuple[list[int],tuple[int] | tuple[()],list[int],set[int],set[int]]] = []
        # players choose among focus ties
        for focus in focuses:
            destinationsss = self.calculate_location_properties(ATTACK_RANGE, PLUS_TARGET, PLUS_TARGET_FOR_MOVEMENT,
                                AOE_ACTION, AOE_MELEE, aoe, aoe_pattern_list, characters,focus)

            # find best location on board, disregarding ennemies other than focus
            destinationsss = self.find_minimums_values(destinationsss,lambda x: self.calculate_location_score(SUSCEPTIBLE_TO_DISADVANTAGE,
                travel_distances, trap_counts, focus, x))

            # for the remaining considered location calculate potential target
            destinationsss = [(dest[0], dest[1], dest[2], dest[3], tuple(sorted(dest[2].union(tup)))if focus in dest[2].union(tup) else (), dest[5])
                              for dest in destinationsss
                              for tup in itertools.combinations(dest[0], min(dest[1], len(dest[0])))]

            # find the best group of targets based on the following priorities
            groups = self.find_minimums_values(destinationsss,lambda x: self.calculate_aoe_score(travel_distances, x, focus_ranks))

            destinationsss= [dest for dest in destinationsss if dest[4] in {grp[4] for grp in groups}]

            # given the target group, find the best destinations to attack from
            # based on the following priorities

            destinationsss = self.find_minimums_values(destinationsss,lambda x: self.calculate_destination_score(SUSCEPTIBLE_TO_DISADVANTAGE,
                travel_distances,x))
                
            # determine the best move based on the chosen destinations
            can_reach_destinations = travel_distances[destinationsss[0][5]] <= self.action_move
            info.extend([(
                [destination[5]] if can_reach_destinations else self.move_closer_to_destinations(travel_distances, trap_counts, destination[5]),
                destination[4] if can_reach_destinations and PLUS_TARGET > -1 else tuple(),
                destination[3] if can_reach_destinations and PLUS_TARGET > -1 else list(),
                {destination[5]},
                {focus}
                ) for destination in destinationsss])

        focusdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        destdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        [destdict[(act,)+iinf[1]].update(iinf[4]) for iinf in info for act in iinf[0]]
        [focusdict[(act,)+iinf[1]].update(iinf[3]) for iinf in info for act in iinf[0]]

        solution = list({((act,)+iinf[1]):
            (act,
            list(iinf[1]),
            iinf[2],
            destdict[(act,)+iinf[1]],
            {self.map.find_shortest_sightline(act, attack, self.RULE_VERTEX_LOS) for attack in iinf[1]},
            self.debug_lines,
            focusdict[(act,)+iinf[1]])
            for iinf in info for act in iinf[0]}.values())

         # move monster
        if self.logging:
            map_debug_tags = [' '] * self.map.map_size
            self.figures[active_monster] = ' '
            map_debug_tags[active_monster] = 's'
            if not self.show_each_action_separately:
                for action in solution:
                    self.figures[action[0]] = 'A'
                    for destination in action[6]:
                        map_debug_tags[destination] = 'd'
                    for target in action[1]:
                        map_debug_tags[target] = 'a'
                # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ], map_debug_tags )
            else:
                for action in solution:
                    figures = list(self.figures)
                    action_debug_tags = list(map_debug_tags)
                    figures[action[0]] = 'A'
                    for destination in action[6]:
                        action_debug_tags[destination] = 'd'
                    for target in action[1]:
                        action_debug_tags[target] = 'a'
                    # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ], action_debug_tags )

        return solution

    def find_minimums_values(self,collections,key):
        score=[key(col) for col in collections]
        best_score=min(score)
        return [collections[i] for i,x in enumerate(score) if x == best_score]
    
    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int):

        distance_to_destination, traps_to_destination = self.find_path_distances_reverse(destination)

        valid_locations = [location for location in range(self.map.map_size)
                            if travel_distances[location] <= self.action_move and
                            self.can_end_move_on(location)]

        return self.find_minimums_values(valid_locations,lambda x: self.calculate_location_score_for_movement(travel_distances, trap_counts, distance_to_destination, traps_to_destination, x))

    def calculate_location_score_for_movement(self, travel_distances, trap_counts, distance_to_destination, traps_to_destination, location):
        # traps to destination and along travel
        # distance to destination
        # travel distance
        return (traps_to_destination[location] + trap_counts[location],
                distance_to_destination[location],
                travel_distances[location])

    def calculate_location_score(self, SUSCEPTIBLE_TO_DISADVANTAGE, travel_distances,trap_counts, focus, dest):
        # best_groupss = (
        #     MAX_VALUE - 1,  # traps to the attack location
        #     0,             # can reach the attack location
        #     1,             # disadvantage against the focus
        #     0,             # total number of targets
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_destination = (
                trap_counts[dest[5]],
                -(travel_distances[dest[5]] <= self.action_move),
                int(SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(dest[5], focus)),
                -(len(dest[2])+min(dest[1],len(dest[0])))
            )
        
        return this_destination

    def calculate_destination_score(self, SUSCEPTIBLE_TO_DISADVANTAGE, travel_distances, dest):

        this_destination = (
                sum([SUSCEPTIBLE_TO_DISADVANTAGE and self.map.is_adjacent(dest[5], target) for target in dest[4]]),
                travel_distances[dest[5]],
            )
        
        return this_destination

    def maximize_aoe_pattern_hits(self, ATTACK_RANGE: int,AOE_MELEE: bool, aoe: list[tuple[int, int, int]],
     location: int, aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int]) -> list[list[int]]:

        if AOE_MELEE:
            # add non-AoE targets and consider result
            return [
                        [aoe_hex for aoe_hex in (self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation)
                        # loop over each hex in the aoe, adding targets
                        for aoe_offset in aoe)
                        if aoe_hex >-1]
                    # loop over every possible aoe placement
                    for aoe_rotation in range(12)]
        else:
            distances = self.map.find_proximity_distances(location)
            return [aoe_hexes for aoe_hexes in
                                [# loop over each hex in the aoe, adding targets
                                    [aoe_hex for aoe_hex in (self.map.apply_aoe_offset(aoe_location, aoe_offset) for aoe_offset in aoe_pattern)
                                    if aoe_hex > -1]
                                # loop over all aoe placements that hit characters
                                for aoe_pattern in aoe_pattern_list
                                for aoe_location in characters]
                    if any(distances[target] <= ATTACK_RANGE for target in aoe_hexes)]

    def calculate_location_properties(self, ATTACK_RANGE: int, PLUS_TARGET: int, PLUS_TARGET_FOR_MOVEMENT: int,
                                               AOE_ACTION: bool, AOE_MELEE: bool, aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]],
                                               characters: list[int], focus):
        location_properties=[]

        for location in range(self.map.map_size):
            if self.can_end_move_on(location):
                targetable_character={_ for _ in characters
                    if self.map.find_proximity_distances(location)[_] <= ATTACK_RANGE and self.map.test_los_between_locations(_, location, self.RULE_VERTEX_LOS)}

                if not AOE_ACTION:
                    location_properties.extend(self.compute_location_property(1 + PLUS_TARGET_FOR_MOVEMENT, focus, location, [], set(), targetable_character))
                else :
                    for aoe_hexes in self.maximize_aoe_pattern_hits(ATTACK_RANGE, AOE_MELEE, aoe,
                     location, aoe_pattern_list, characters):
                        aoe_targets={ target for target in aoe_hexes if target in characters and self.map.test_los_between_locations(target, location, self.RULE_VERTEX_LOS)}

                        location_properties.extend(self.compute_location_property(PLUS_TARGET, focus, location, aoe_hexes, aoe_targets, targetable_character-aoe_targets))

        return location_properties

    def compute_location_property(self, PLUS_TARGET, focus, location, aoe_hexes, aoe_targets:set[int], targets):
        return [(targets, PLUS_TARGET, aoe_targets, aoe_hexes,(),location)] if (PLUS_TARGET != 0 and focus in targets) or focus in aoe_targets else []

    def calculate_aoe_score(self, travel_distances, dest, focus_ranks):
        targets_of_rank = [0] * (max(focus_ranks.values()) + 1)
        for target in dest[4]:
            targets_of_rank[focus_ranks[target]] -= 1
        # best_groupss = (
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_group = (
                travel_distances[dest[5]],
                ) + tuple(targets_of_rank)
            
        return this_group

    def can_attack_from_location(self, character: int, location: int, AOE_ACTION: bool, AOE_MELEE: bool, aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], ATTACK_RANGE: int,
                                 range_to_character: int) -> bool:
        if not self.map.test_los_between_locations(character, location, self.RULE_VERTEX_LOS):
            return False

        if not AOE_ACTION:
            return range_to_character <= ATTACK_RANGE

        if AOE_MELEE:
            return any(character == self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation) for aoe_offset in aoe for aoe_rotation in range(12))                            
        
        distances = self.map.find_proximity_distances(location)
        return any(self.get_aoe_offsetted_target(character, aoe_offset,distances,ATTACK_RANGE) for aoe_pattern in aoe_pattern_list for aoe_offset in aoe_pattern )            

    def get_aoe_offsetted_target(self, character, aoe_offset,distances,ATTACK_RANGE):
        target = self.map.apply_aoe_offset(character, aoe_offset)
        if target > -1 and (distances[target] <= ATTACK_RANGE):
            return target

    def find_focus(self, ATTACK_RANGE: int, AOE_ACTION: bool, AOE_MELEE: bool, travel_distances: list[int], trap_counts: list[int], proximity_distances: list[int],
                   travel_distance_sorted_map: list[int], aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int]) -> tuple[set[int], dict[int, int]]:
 
        range_to_character = {character:self.map.find_proximity_distances(character) for character in characters}

        characterss = [(character,location)
                        for location in travel_distance_sorted_map
                        for character in characters
                        if travel_distances[location] != MAX_VALUE and
                            self.can_end_move_on(location) and
                            self.can_attack_from_location(character, location, AOE_ACTION, AOE_MELEE, aoe, aoe_pattern_list, ATTACK_RANGE, range_to_character[character][location])]

        focuses={focus[0]
                for focus in self.find_minimums_values(characterss,lambda x: self.calculate_focus_score(travel_distances, trap_counts, proximity_distances, x[0], x[1]))} if len(characterss)>0 else set()

        # rank characters for secondary targeting

        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in characters]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}

        return focuses, focus_ranks

    def calculate_secondary_focus_score(self,proximity_distances, character):
        return (proximity_distances[character], self.initiatives[character]),character

    def calculate_focus_score(self, travel_distances, trap_counts, proximity_distances, character, location):
        return (trap_counts[location],
                travel_distances[location],
                0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[character],
                self.initiatives[character])

    def process_aoe(self, AOE_MELEE: bool) -> tuple[list[tuple[int, int, int]], list[list[tuple[int, int, int]]]]:
        aoe_pattern_list: list[list[tuple[int, int, int]]] = []
        aoe: list[tuple[int, int, int]] = []

        if AOE_MELEE:
            return [get_offset(self.aoe_center, location, self.aoe_height) for location in range(self.aoe_size) if self.aoe[location]], []

        # precalculate aoe patterns to remove degenerate cases        
        aoe = [get_offset(self.aoe.index(True), location, self.aoe_height)
            for location in range(self.aoe_size) if self.aoe[location]]
            
        PRECALC_GRID_HEIGHT = 21
        PRECALC_GRID_WIDTH = 21
        PRECALC_GRID_SIZE = PRECALC_GRID_HEIGHT * PRECALC_GRID_WIDTH
        PRECALC_GRID_CENTER = (PRECALC_GRID_SIZE - 1) // 2

        aoe_pattern_set: set[tuple[int]] = set()
        for aoe_pin in aoe:
            for aoe_rotation in range(12):
                aoe_hexes = [apply_offset(PRECALC_GRID_CENTER, rotate_offset(pin_offset(aoe_offset, aoe_pin), aoe_rotation), PRECALC_GRID_HEIGHT, PRECALC_GRID_SIZE)
                            for aoe_offset in aoe]
                aoe_hexes.sort()
                aoe_pattern_set.add(tuple(aoe_hexes))

        aoe_pattern_list = [    [get_offset(PRECALC_GRID_CENTER, location, PRECALC_GRID_HEIGHT)
                                for location in aoe]
                            for aoe in aoe_pattern_set]

        return aoe, aoe_pattern_list

    def solve_sight(self, monster: int,attack_range:int) -> list[tuple[int, int]]:
        if attack_range != MAX_VALUE and self.action_target == 0:
            return []

        distances = self.map.find_proximity_distances(monster)

        reach: list[tuple[int, int]] = []
        has_run_begun = False
        run = 0
        for location in range(self.map.map_size):
            if distances[location] <= attack_range and not self.map.blocks_los(location) and location != monster and self.map.test_los_between_locations(monster, location, self.RULE_VERTEX_LOS):                        
                if not has_run_begun :
                    run = location
                    has_run_begun = True         
            elif has_run_begun :
                reach.append((run, location))
                has_run_begun = False

        if has_run_begun :
            reach.append((run, self.map.map_size))
        return reach

    def solve_reaches(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.solve_sight(_,1 if self.action_range == 0 else self.action_range) for _ in viewpoints]

    def solve_sights(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.solve_sight(_,MAX_VALUE) for _ in viewpoints]

    # def debug_plot_line(self, color, line):
    #     self.debug_lines.add((color, (scale_vector(
    #         DEBUG_PLOT_SCALE, line[0]), scale_vector(DEBUG_PLOT_SCALE, line[1]))))

    # def debug_plot_point(self, color, point):
    #     self.debug_lines.add(
    #         (color, (scale_vector(DEBUG_PLOT_SCALE, point), )))

    # def reduce_map(self):
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
