import collections
import textwrap
import itertools
from functools import partial
from typing import Callable, Generator
from typing import Any
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from solver.monster import Monster

class Scenario:
    logging: bool
    debug_visuals: bool
    show_each_action_separately: bool
    debug_lines: set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]
    debug_toggle: bool
    message: str
    rule:Rule
    def __init__(self, rule:Rule, gmap: GloomhavenMap ):
        self.map = gmap
        self.logging = False
        self.debug_visuals = False
        self.show_each_action_separately = False
        self.debug_lines = set()
        self.message = ''
        self.debug_toggle = False
        self.rule=rule
        #LOS is only checked between vertices
        self.RULE_VERTEX_LOS = rule == Rule.Gloom
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl

    def calculate_monster_move(self) -> list[tuple[
        int,
        list[int],
        list[int],
        set[int],
        set[tuple[tuple[float, float], tuple[float, float]]],
        set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]],
        set[int]]]:

        monster = self.map.get_active_monster()
        if self.logging:
            self.map.print()
            if self.map.monster.is_aoe():
                self.map.print_aoe_map()
            self.map.print_initiative_map()
            self.map.print_summary(self.debug_toggle)
            if self.message:
                print(textwrap.fill(self.message, 82))

        # find active monster
        active_monster = self.map.get_active_monster_location()
        travel_distances, trap_counts = self.map.find_path_distances(active_monster)
        proximity_distances = self.map.find_proximity_distances(active_monster)
        #self.map.print_custom_map(bottom_label=trap_counts)
        #self.map.print_custom_map(bottom_label=proximity_distances)
        
        # doesn't speed things up but makes los testing order more intuitive for debugging
        travel_distance_sorted_map = sorted(list(range(self.map.map_size)), key=lambda x: travel_distances[x])

        # process aoe
        aoe, aoe_pattern_list = self.map.process_aoe() if monster.is_aoe() else ([],[])

        # find characters
        characters = self.map.get_characters()

        if not characters:
            return [(active_monster, [], [], set(), set(), self.debug_lines, set())]

        # find monster focuses
        focuses, focus_ranks = self.find_focus(travel_distances, trap_counts, proximity_distances,travel_distance_sorted_map, aoe, aoe_pattern_list, characters,monster)
        # if we find no actions, stand still

        if not focuses:
            return [(active_monster, [], [], set(), set(), self.debug_lines, set())]

        info: list[tuple[list[int],tuple[int] | tuple[()],list[int],set[int],set[int]]] = []
        # players choose among focus ties
        for focus in focuses:
            destinationsss = [(non_aoe_targets,
                                monster.plus_target() if monster.is_aoe() else 1 + monster.plus_target_for_movement(),
                                aoe_targets,
                                aoe_hexes,
                                (),
                                location)
                                for location in range(self.map.map_size)
                                if self.map.can_end_move_on(location)
                                for aoe_targets, aoe_hexes, non_aoe_targets in self.get_targets(aoe, location, aoe_pattern_list, characters,monster)
                                if ((monster.plus_target() if monster.is_aoe() else 1 + monster.plus_target_for_movement()) != 0 and
                                            focus in non_aoe_targets)
                                            or focus in aoe_targets]
                            

            # find best location on board, disregarding ennemies other than focus
            destinationsss = self.find_minimums_values(destinationsss, partial(self.calculate_location_score,
                travel_distances, trap_counts, focus,monster))

            # for the remaining considered location calculate potential target
            destinationsss = [((), (), (), dest[3], tuple(sorted(dest[2].union(tup)))if focus in dest[2].union(tup) else (), dest[5])
                              for dest in destinationsss
                              for tup in itertools.combinations(dest[0], min(dest[1], len(dest[0]))if not monster.is_max_targets() else len(dest[0]))]

            # find the best group of targets based on the following priorities
            groups = self.find_minimums_values(destinationsss,lambda x: self.calculate_aoe_score(travel_distances, x, focus_ranks))

            destinationsss= [dest for dest in destinationsss if dest[4] in {grp[4] for grp in groups}]

            # given the target group, find the best destinations to attack from
            # based on the following priorities

            destinationsss = self.find_minimums_values(destinationsss,lambda x: self.calculate_destination_score(travel_distances,x,monster))

            # determine the best move based on the chosen destinations
            can_reach_destinations = travel_distances[destinationsss[0][5]] <= monster.action_move
            info.extend([(
                [destination[5]] if can_reach_destinations else self.move_closer_to_destinations(travel_distances, trap_counts, destination[5],monster),
                destination[4] if can_reach_destinations and monster.plus_target() > -1 else tuple(),
                destination[3] if can_reach_destinations and monster.plus_target() > -1 else [],
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
            self.map.figures[active_monster] = ' '
            map_debug_tags[active_monster] = 's'
            if not self.show_each_action_separately:
                for action in solution:
                    self.map.figures[action[0]] = 'A'
                    for destination in action[6]:
                        map_debug_tags[destination] = 'd'
                    for target in action[1]:
                        map_debug_tags[target] = 'a'
                self.map.print_solution_map( map_debug_tags )
            else:
                for action in solution:
                    figures = list(self.map.figures)
                    action_debug_tags = list(map_debug_tags)
                    figures[action[0]] = 'A'
                    for destination in action[6]:
                        action_debug_tags[destination] = 'd'
                    for target in action[1]:
                        action_debug_tags[target] = 'a'
                    self.map.print_solution_map( map_debug_tags )

        return solution

    def find_minimums_values(self,iterable:list[Any],key:Callable[[Any],Any]):
        score=[key(col) for col in iterable]
        best_score=min(score)
        return [iterable[i] for i,x in enumerate(score) if x == best_score]

    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int, monster : Monster):

        distance_to_destination, traps_to_destination = self.map.find_path_distances_reverse(destination)

        valid_locations = [location for location in range(self.map.map_size)
                            if travel_distances[location] <= monster.action_move and
                            self.map.can_end_move_on(location)]

        return self.find_minimums_values(valid_locations,lambda x: self.calculate_location_score_for_movement(travel_distances, trap_counts, distance_to_destination, traps_to_destination, x))

    def calculate_location_score_for_movement(self, travel_distances:list[int], trap_counts:list[int], distance_to_destination:list[int], traps_to_destination:list[int], location:int):
        # traps to destination and along travel
        # distance to destination
        # travel distance
        return (traps_to_destination[location] + trap_counts[location],
                distance_to_destination[location],
                travel_distances[location])

    def calculate_location_score(self,travel_distances:list[int],trap_counts:list[int], focus:int, monster :Monster, dest:tuple[set[int],int,set[int],list[int],tuple[int,int],int]):
        # best_groupss = (
        #     MAX_VALUE - 1,  # traps to the attack location
        #     0,             # can reach the attack location
        #     1,             # disadvantage against the focus
        #     0,             # total number of targets
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_destination = (
            trap_counts[dest[5]],
            -(travel_distances[dest[5]] <= monster.action_move),
            int(monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[5], focus)),
            -(len(dest[2])+min(dest[1], len(dest[0])) if not monster.is_max_targets() else len(dest[0]))
        )

        return this_destination

    def calculate_destination_score(self, travel_distances:list[int], dest:tuple[set[int],int,set[int],list[int],tuple[int,int],int], monster : Monster):

        this_destination = (
                sum((monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[5], target) for target in dest[4])),
                travel_distances[dest[5]])

        return this_destination

    def get_targets(self,aoe: list[tuple[int, int, int]],location: int, aoe_pattern_list: list[list[tuple[int, int, int]]],
     characters: list[int], monster : Monster) ->Generator[tuple[set[int], list[int], set[int]], None, None]:
        targetable_character={_ for _ in characters if self.map.find_proximity_distances(location)[_] <= monster.attack_range() and self.map.test_los_between_locations(_, location, self.RULE_VERTEX_LOS)}
        if not monster.is_aoe():
            return (self.get_attacks_targets([],characters,location,targetable_character) for _ in [1])
        if monster.is_melee_aoe():
            # add non-AoE targets and consider result
            aoe_hexess = (self.get_attacks_targets([self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation)
                        # loop over each hex in the aoe, adding targets
                                                    for aoe_offset in aoe],
                                                    characters,location,targetable_character)
                    # loop over every possible aoe placement
                    for aoe_rotation in range(12))
        else:
            distances = self.map.find_proximity_distances(location)
            aoe_hexess =  (self.get_attacks_targets(aoe_hexes,characters,location,targetable_character)
                                 for aoe_hexes in
                                [# loop over each hex in the aoe, adding targets
                                    [self.map.apply_aoe_offset(aoe_location, aoe_offset) for aoe_offset in aoe_pattern]
                                # loop over all aoe placements that hit characters
                                for aoe_pattern in aoe_pattern_list
                                for aoe_location in characters]
                    if any(distances[target] <= monster.attack_range() for target in aoe_hexes))

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
                   travel_distance_sorted_map: list[int], aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int],monster:Monster) -> tuple[set[int], dict[int, int]]:

        characterss = [(character,location)
                        for location in travel_distance_sorted_map
                        for character in characters
                        if travel_distances[location] != MAX_VALUE and
                            self.map.can_end_move_on(location) and
                            any(len(y[0]) >0 or len(y[2]) >0 for y in self.get_targets(aoe, location, aoe_pattern_list, [character],monster))]

        focuses:set[int]={focus[0]
                for focus in self.find_minimums_values(characterss,lambda x: self.calculate_focus_score(travel_distances, trap_counts, proximity_distances, x[0], x[1]))} if len(characterss)>0 else set()

        # rank characters for secondary targeting

        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in characters]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}

        return focuses, focus_ranks

    def calculate_secondary_focus_score(self,proximity_distances:list[int], character:int):
        return (proximity_distances[character], self.map.get_character_initiative(character)),character

    def calculate_focus_score(self, travel_distances:list[int], trap_counts:list[int], proximity_distances:list[int], character:int, location:int):
        return (trap_counts[location],
                travel_distances[location],
                0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[character],
                self.map.get_character_initiative(character))

    def solve_reaches(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        monster = self.map.get_active_monster()
        return [self.map.solve_sight(_,1 if monster.action_range == 0 else monster.action_range, self.RULE_VERTEX_LOS) for _ in viewpoints] if  monster.action_target != 0 else []

    def solve_sights(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        return [self.map.solve_sight(_,MAX_VALUE, self.RULE_VERTEX_LOS) for _ in viewpoints]