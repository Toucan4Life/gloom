import collections
from functools import partial
import textwrap
import itertools
from typing import Callable
from solver.hexagonal_grid import hexagonal_grid
from solver.settings import MAX_VALUE
from solver.utils import get_offset, pin_offset, rotate_offset, apply_offset
from typing import Any
from solver.monster import Monster
from enum import Enum

class Rule(Enum):
    Frost = 0
    Gloom = 1
    Jotl = 2

class Scenario:

    logging: bool
    debug_visuals: bool
    show_each_action_separately: bool
    debug_lines: set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]
    debug_toggle: bool
    message: str

    figures: list[str]
    initiatives: list[int]
    walls: list[list[bool]]
    contents: list[str]
    monster: Monster
    rule:Rule
    def __init__(self, width: int, height: int, monster:Monster, rule:Rule):
        self.monster = monster
        self.map = hexagonal_grid(width, height)
        self.logging = False
        self.debug_visuals = False
        self.show_each_action_separately = False
        self.debug_lines = set()

        self.figures = [' '] * self.map.map_size
        self.initiatives = [0] * self.map.map_size

        self.walls = [[False] * 6 for _ in range(self.map.map_size)]
        self.contents = [' '] * self.map.map_size
        self.message = ''
        self.debug_toggle = False
        self.rule=rule
        #LOS is only checked between vertices
        self.RULE_VERTEX_LOS = rule == Rule.Gloom
        #difficult terrain effects the last hex of a jump move
        self.RULE_DIFFICULT_TERRAIN_JUMP = rule == Rule.Gloom
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl

    def prepare_map(self) -> None:
        self.map.prepare_map(self.walls, self.contents)

       


    def can_end_move_on(self, location: int) -> bool:
        if self.monster.flying:
            return self.map.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']

    def can_travel_through(self, location: int) -> bool:
        if self.monster.flying | self.monster.jumping:
            return self.map.contents[location] in [' ', 'T', 'H', 'D', 'O']
        return self.map.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] != 'C'

    def is_trap(self, location: int) -> bool:
        if self.monster.flying:
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
                    int(not self.monster.flying and not self.monster.jumping and self.map.additional_path_cost(
                        neighbor))
                neighbor_trap = int(not self.monster.jumping) * \
                    trap + int(self.is_trap(neighbor))
                if (neighbor_trap, neighbor_distance) < (traps[neighbor], distances[neighbor]):
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance
                    traps[neighbor] = neighbor_trap

        if self.RULE_DIFFICULT_TERRAIN_JUMP and self.monster.jumping:
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
        if not self.monster.flying:
            if not self.monster.jumping or self.RULE_DIFFICULT_TERRAIN_JUMP:
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


        if self.logging:

            # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in range( self.MAP_SIZE ) ] )
            if self.monster.is_aoe():
                false_contents = ['   '] * self.monster.aoe_size
                if self.monster.is_melee_aoe():
                    false_contents[self.monster.aoe_center()] = ' A '
                # print_map( self, self.AOE_WIDTH, self.AOE_HEIGHT, [ [ False ] * 6 ] * self.AOE_SIZE, false_contents, [ format_aoe( _ ) for _ in self.monster.aoe ] )
            # print_map( self, self.MAP_WIDTH, self.MAP_HEIGHT, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ] )

            out = ''
            if self.rule == Rule.Frost:
                out += ', FROSTHAVEN'
            if self.rule == Rule.Gloom:
                out += ', GLOOMHAVEN'
            if self.rule == Rule.Jotl:
                out += ', JAWS OF THE LION'
            if self.monster.action_move > 0:
                out += f', MOVE {self.monster.action_move}'
            if self.monster.action_range > 0 and self.monster.action_target > 0:
                out += f', RANGE {self.monster.action_range}'
            if self.monster.action_target > 0:
                out += ', ATTACK'
            if self.monster.is_aoe():
                out += ', AOE'
            if self.monster.plus_target() > 0:
                if self.monster.is_max_targets():
                    out += ', TARGET ALL'
                else:
                    out += f', +TARGET {self.monster.plus_target()}'
            if self.monster.flying:
                out += ', FLYING'
            elif self.monster.jumping:
                out += ', JUMPING'
            if self.monster.muddled:
                out += ', MUDDLED'
            out += f', DEBUG_TOGGLE = {self.debug_toggle}'
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

        aoe, aoe_pattern_list = self.process_aoe() if self.monster.is_aoe() else ([],[])

        # find characters
        characters = [_ for _, figure in enumerate(self.figures) if figure == 'C']

        if not characters:
            return [(active_monster, [], [], set(), set(), self.debug_lines, set())]

        # find monster focuses
        focuses, focus_ranks = self.find_focus(travel_distances, trap_counts, proximity_distances,travel_distance_sorted_map, aoe, aoe_pattern_list, characters)
        # if we find no actions, stand still

        if not focuses:
            return [(active_monster, [], [], set(), set(), self.debug_lines, set())]

        info: list[tuple[list[int],tuple[int] | tuple[()],list[int],set[int],set[int]]] = []
        # players choose among focus ties
        for focus in focuses:
            destinationsss = [y for y in [self.compute_location_property(self.monster.plus_target() if self.monster.is_aoe() else 1 + self.monster.plus_target_for_movement(), focus, location, aoe_hexes, aoe_targets, non_aoe_targets)
                                for location in range(self.map.map_size)
                                if self.can_end_move_on(location)
                                for aoe_targets, aoe_hexes, non_aoe_targets in self.get_targets(aoe, location, aoe_pattern_list, characters)]
                            if y is not None]

            # find best location on board, disregarding ennemies other than focus
            destinationsss = self.find_minimums_values(destinationsss, partial(self.calculate_location_score,
                travel_distances, trap_counts, focus))

            # for the remaining considered location calculate potential target
            destinationsss = [(dest[0], dest[1], dest[2], dest[3], tuple(sorted(dest[2].union(tup)))if focus in dest[2].union(tup) else (), dest[5])
                              for dest in destinationsss
                              for tup in itertools.combinations(dest[0], min(dest[1], len(dest[0]))if not self.monster.is_max_targets() else len(dest[0]))]

            # find the best group of targets based on the following priorities
            groups = self.find_minimums_values(destinationsss,lambda x: self.calculate_aoe_score(travel_distances, x, focus_ranks))

            destinationsss= [dest for dest in destinationsss if dest[4] in {grp[4] for grp in groups}]

            # given the target group, find the best destinations to attack from
            # based on the following priorities

            destinationsss = self.find_minimums_values(destinationsss,lambda x: self.calculate_destination_score(travel_distances,x))

            # determine the best move based on the chosen destinations
            can_reach_destinations = travel_distances[destinationsss[0][5]] <= self.monster.action_move
            info.extend([(
                [destination[5]] if can_reach_destinations else self.move_closer_to_destinations(travel_distances, trap_counts, destination[5]),
                destination[4] if can_reach_destinations and self.monster.plus_target() > -1 else tuple(),
                destination[3] if can_reach_destinations and self.monster.plus_target() > -1 else list(),
                {destination[5]},
                {focus}
                ) for destination in destinationsss])

        focusdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        destdict:dict[tuple[int]|tuple[int,int],set[int]] = collections.defaultdict(set)
        
        for iinf in info:
            for act in iinf[0]:
                destdict[(act,)+iinf[1]].update(iinf[4])
                focusdict[(act,)+iinf[1]].update(iinf[3])

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

    def find_minimums_values(self,iterable:list[Any],key:Callable[[Any],Any]):
        score=[key(col) for col in iterable]
        best_score=min(score)
        return [iterable[i] for i,x in enumerate(score) if x == best_score]

    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int):

        distance_to_destination, traps_to_destination = self.find_path_distances_reverse(destination)

        valid_locations = [location for location in range(self.map.map_size)
                            if travel_distances[location] <= self.monster.action_move and
                            self.can_end_move_on(location)]

        return self.find_minimums_values(valid_locations,lambda x: self.calculate_location_score_for_movement(travel_distances, trap_counts, distance_to_destination, traps_to_destination, x))

    def calculate_location_score_for_movement(self, travel_distances:list[int], trap_counts:list[int], distance_to_destination:list[int], traps_to_destination:list[int], location:int):
        # traps to destination and along travel
        # distance to destination
        # travel distance
        return (traps_to_destination[location] + trap_counts[location],
                distance_to_destination[location],
                travel_distances[location])

    def calculate_location_score(self,travel_distances:list[int],trap_counts:list[int], focus:int, dest:tuple[set[int],int,set[int],list[int],tuple[int,int],int]):
        # best_groupss = (
        #     MAX_VALUE - 1,  # traps to the attack location
        #     0,             # can reach the attack location
        #     1,             # disadvantage against the focus
        #     0,             # total number of targets
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_destination = (
                trap_counts[dest[5]],
                -(travel_distances[dest[5]] <= self.monster.action_move),
                int(self.monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[5], focus)),
                -(len(dest[2])+min(dest[1],len(dest[0]))if not self.monster.is_max_targets() else len( dest[0] ))
            )

        return this_destination

    def calculate_destination_score(self, travel_distances:list[int], dest:tuple[set[int],int,set[int],list[int],tuple[int,int],int]):

        this_destination = (
                sum([self.monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[5], target) for target in dest[4]]),
                travel_distances[dest[5]],
            )

        return this_destination

    def get_targets(self,aoe: list[tuple[int, int, int]],location: int, aoe_pattern_list: list[list[tuple[int, int, int]]],
     characters: list[int]) -> list[tuple[set[int], list[int], set[int]]]:
        targetable_character={_ for _ in characters if self.map.find_proximity_distances(location)[_] <= self.monster.attack_range() and self.map.test_los_between_locations(_, location, self.RULE_VERTEX_LOS)}
        if not self.monster.is_aoe():
            return [self.get_attacks_targets([],characters,location,targetable_character)]
        if self.monster.is_melee_aoe():
            # add non-AoE targets and consider result
            aoe_hexess = [self.get_attacks_targets([self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation)
                        # loop over each hex in the aoe, adding targets
                                                    for aoe_offset in aoe],
                                                    characters,location,targetable_character)
                    # loop over every possible aoe placement
                    for aoe_rotation in range(12) ]
        else:
            distances = self.map.find_proximity_distances(location)
            aoe_hexess =  [self.get_attacks_targets(aoe_hexes,characters,location,targetable_character)
                                 for aoe_hexes in
                                [# loop over each hex in the aoe, adding targets
                                    [self.map.apply_aoe_offset(aoe_location, aoe_offset) for aoe_offset in aoe_pattern]
                                # loop over all aoe placements that hit characters
                                for aoe_pattern in aoe_pattern_list
                                for aoe_location in characters]
                    if any(distances[target] <= self.monster.attack_range() for target in aoe_hexes)]

        return aoe_hexess

    def get_attacks_targets(self,aoe_hexes:list[int],characters:list[int],location:int,targetable_character:set[int]):
        aoe_targets = { target for target in aoe_hexes if target in characters and self.map.test_los_between_locations(target, location, self.RULE_VERTEX_LOS)}
        non_aoe_targets = targetable_character - aoe_targets
        return aoe_targets, aoe_hexes, non_aoe_targets

    def compute_location_property(self, plus_target:int, focus:int, location:int, aoe_hexes:list[int], aoe_targets:set[int], non_aoe_targets:set[int]):
        return (non_aoe_targets, plus_target, aoe_targets, aoe_hexes,(),location) if (plus_target != 0 and focus in non_aoe_targets) or focus in aoe_targets else None

    def calculate_aoe_score(self, travel_distances:list[int], dest:tuple[set[int],int,set[int],list[int],tuple[int,int],int], focus_ranks:dict[int,int]):
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

    def find_focus(self,travel_distances: list[int], trap_counts: list[int], proximity_distances: list[int],
                   travel_distance_sorted_map: list[int], aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int]) -> tuple[set[int], dict[int, int]]:

        characterss = [(character,location)
                        for location in travel_distance_sorted_map
                        for character in characters
                        if travel_distances[location] != MAX_VALUE and
                            self.can_end_move_on(location) and
                            any(len(y[0]) >0 or len(y[2]) >0 for y in self.get_targets(aoe, location, aoe_pattern_list, [character]))]

        focuses:set[int]={focus[0]
                for focus in self.find_minimums_values(characterss,lambda x: self.calculate_focus_score(travel_distances, trap_counts, proximity_distances, x[0], x[1]))} if len(characterss)>0 else set()

        # rank characters for secondary targeting

        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in characters]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}

        return focuses, focus_ranks

    def calculate_secondary_focus_score(self,proximity_distances:list[int], character:int):
        return (proximity_distances[character], self.initiatives[character]),character

    def calculate_focus_score(self, travel_distances:list[int], trap_counts:list[int], proximity_distances:list[int], character:int, location:int):
        return (trap_counts[location],
                travel_distances[location],
                0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[character],
                self.initiatives[character])

    def process_aoe(self) -> tuple[list[tuple[int, int, int]], list[list[tuple[int, int, int]]]]:
        aoe_pattern_list: list[list[tuple[int, int, int]]] = []
        aoe: list[tuple[int, int, int]] = []

        if self.monster.is_melee_aoe():
            return [get_offset(self.monster.aoe_center(), location, self.monster.aoe_height) for location in range(self.monster.aoe_size) if self.monster.aoe[location]], []

        # precalculate aoe patterns to remove degenerate cases
        aoe = [get_offset(self.monster.aoe.index(True), location, self.monster.aoe_height)
            for location in range(self.monster.aoe_size) if self.monster.aoe[location]]

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

    def solve_reaches(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.map.solve_sight(_,1 if self.monster.action_range == 0 else self.monster.action_range, self.RULE_VERTEX_LOS) for _ in viewpoints] if  self.monster.action_target != 0 else []

    def solve_sights(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.map.solve_sight(_,MAX_VALUE, self.RULE_VERTEX_LOS) for _ in viewpoints]