
import textwrap
import itertools
from functools import partial
from typing import Callable
from typing import Any
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from solver.monster import Monster
class Solver:
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
        self.show_each_action_separately = True
        self.debug_lines = set()
        self.message = ''
        self.debug_toggle = False
        self.rule=rule
        #LOS is only checked between vertices
        self.RULE_VERTEX_LOS = rule == Rule.Gloom
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl

    def calculate_monster_move(self) -> list[tuple[int, int, list[int], frozenset[int], list[int], set[tuple[tuple[float, float], tuple[float, float]]]]]:

        monster = self.map.get_active_monster()
        if self.logging:
            self.map.print()
            if self.map.monster.is_aoe():
                self.map.print_aoe_map()
            self.map.print_initiative_map()
            self.map.print_summary(self.debug_toggle)
            if self.message:
                print(textwrap.fill(self.message, 82))

        #self.map.print_custom_map(bottom_label=trap_counts)

        # find active monster
        active_monster = self.map.get_active_monster_location()

        # find characters        
        characters = self.map.get_characters()

        if not characters:
            return [(active_monster, -1, [], frozenset(), [], set())]

        # process aoe
        aoe, aoe_pattern_list = self.map.process_aoe() if monster.is_aoe() else ([],[])

        # find monster focuses
        travel_distances, trap_counts = self.map.find_path_distances(active_monster)

        character_location = self.find_attackable_location_for_characters_for_focus(travel_distances, aoe, aoe_pattern_list, characters, monster)

        focuses, focus_ranks = self.find_focus(travel_distances, trap_counts, characters,active_monster,character_location)

        character_location = self.find_attackable_location_for_characters(travel_distances, aoe, aoe_pattern_list, characters, monster)

        # if we find no actions, stand still
        if not focuses:
            return [(active_monster, -1, [], frozenset(), [], set())]

        solution: list[tuple[int, int,list[int], frozenset[int], list[int],  set[tuple[tuple[float, float], tuple[float, float]]]]] = []

        solution = [(
                focus,
                solution_for_focus[2],
                [solution_for_focus[2]] if travel_distances[solution_for_focus[2]] <= monster.action_move else self.move_closer_to_destinations(travel_distances, trap_counts, solution_for_focus[2],monster),
                solution_for_focus[1] if travel_distances[solution_for_focus[2]] <= monster.action_move and monster.has_attack() else frozenset(),
                solution_for_focus[0] if travel_distances[solution_for_focus[2]] <= monster.action_move and monster.has_attack() else [],
                {self.map.find_shortest_sightline(solution_for_focus[2], attack, self.RULE_VERTEX_LOS) for attack in solution_for_focus[1]} if travel_distances[solution_for_focus[2]] <= monster.action_move and monster.has_attack() else set()
                ) for focus in focuses for solution_for_focus in self.solve_for_focus(focus, travel_distances, focus_ranks, monster, trap_counts,character_location)] # players choose among focus ties     

        if self.logging:
            self.print_solution(active_monster, solution)

        return solution

    def solve_for_focus(self, focus: int, travel_distances: list[int], focus_ranks :dict[int,int], monster : Monster, trap_counts: list[int],character_location: list[tuple[frozenset[int], int, frozenset[int], frozenset[int], frozenset[int]]]) -> list[tuple[list[int], frozenset[int], int]]:
        locations = self.best_location_to_attack_focus(focus,travel_distances,monster,trap_counts,character_location)

        locations = self.find_all_locations_to_attack_best_target_group(travel_distances, focus_ranks, locations)
           
        return self.find_best_locations_to_attack_best_target_group(travel_distances, monster, locations)
        
    def find_best_locations_to_attack_best_target_group(self, travel_distances: list[int], monster: Monster, locations: list[tuple[frozenset[int], frozenset[int], int, int]]):
        return self.find_minimums_values(locations, lambda x: self.calculate_destination_score(travel_distances,x,monster))

    def best_location_to_attack_focus(self, focus: int, travel_distances: list[int],  monster : Monster, trap_counts: list[int],character_location: list[tuple[frozenset[int], int, frozenset[int], frozenset[int], frozenset[int]]]):
        
        locations:set[int] = set(self.find_minimums_values([char_loc[1] for char_loc in character_location if focus in char_loc[0]], partial(self.calculate_location_score, travel_distances, trap_counts, focus,monster)))
        max_non_aoe_target = monster.max_potential_non_aoe_targets()
        return [(aoe_hexes,
                    frozenset(aoe_targets.union(tup)),
                    location,
                    len(aoe_targets)+min(max_non_aoe_target, len(non_aoe_targets))
                    )
                    for _,location,aoe_targets, aoe_hexes, non_aoe_targets in character_location
                    if location in locations
                    if (max_non_aoe_target != 0 and focus in non_aoe_targets) or focus in aoe_targets
                    for tup in itertools.combinations(non_aoe_targets, min(max_non_aoe_target, len(non_aoe_targets)))
                    if focus in aoe_targets.union(tup)
                    ]

    def find_all_locations_to_attack_best_target_group(self, travel_distances: list[int], focus_ranks: dict[int, int], targets_properties: list[tuple[frozenset[int], frozenset[int], int, int]])-> list[tuple[frozenset[int], frozenset[int], int, int]]:
        
        best_groups:set[frozenset[int]] = {grp[1] for grp in self.find_minimums_values(targets_properties,lambda x: self.calculate_aoe_score(travel_distances, x, focus_ranks))}
        return [dest for dest in targets_properties if dest[1] in best_groups]
  
    def print_solution(self, active_monster:int, solution: list[tuple[ int, int,list[int], frozenset[int], list[int], set[tuple[tuple[float, float], tuple[float, float]]]]]):
        map_debug_tags = [' '] * self.map.map_size
        self.map.figures[active_monster] = ' '
        map_debug_tags[active_monster] = 's'
        if not self.show_each_action_separately:
            for action in solution:
                self.print_single_solution_summary(active_monster, action[1], list(action[3]))
                for possible_move in action[2]:                
                    self.map.figures[possible_move] = 'A'
                map_debug_tags[action[1]] = 'd'
                for target in action[3]:
                    map_debug_tags[target] = 'a'
            self.map.print_solution_map( map_debug_tags )
        else:
            for action in solution:
                self.print_single_solution_summary(active_monster, action[1], list(action[3]))
                action_debug_tags = list(map_debug_tags)
                for possible_move in action[2]:                
                    self.map.figures[possible_move] = 'A'
                action_debug_tags[action[1]] = 'd'
                for target in action[3]:
                    action_debug_tags[target] = 'a'
                self.map.print_solution_map( action_debug_tags )
                for possible_move in action[2]:                
                    self.map.figures[possible_move] = ' '

    def print_single_solution_summary(self, active_monster:int, move:int, target:list[int]):
        if move == active_monster:
            out = '- no movement'
        else:
            out = f'- move to {move}'
        if target:
            for attack in target:
                out += f', attack {attack}'
        print(out)

    def find_minimums_values(self,iterable:list[Any],key:Callable[[Any],Any]):
        score=[key(col) for col in iterable]
        best_score=min(score)
        return [iterable[i] for i,x in enumerate(score) if x == best_score]

    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int, monster : Monster)->list[int]:

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

    def calculate_location_score(self,travel_distances:list[int],trap_counts:list[int], focus:int, monster :Monster, dest: int):
        # best_groupss = (
        #     MAX_VALUE - 1,  # traps to the attack location
        #     0,             # can reach the attack location
        #     1,             # disadvantage against the focus
        #     0,             # total number of targets
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_destination = (
            trap_counts[dest],
            -(travel_distances[dest] <= monster.action_move),
            int(monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest, focus))
        )

        return this_destination

    def calculate_destination_score(self, travel_distances:list[int], dest:tuple[list[int],tuple[int,int],int], monster : Monster):

        this_destination = (
                sum((monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[2], target) for target in dest[1])),
                travel_distances[dest[2]])

        return this_destination

    def get_attacks_targets(self,aoe_hexes:list[int],characters:list[int],location:int,targetable_character:set[int]):
        aoe_targets = { target for target in aoe_hexes if target in characters and self.map.test_los_between_locations(target, location, self.RULE_VERTEX_LOS)}
        non_aoe_targets = targetable_character - aoe_targets
        return aoe_targets, aoe_hexes, non_aoe_targets

    def enumerate_aoe_possiblity(self,aoe: list[tuple[int, int, int]],location: int, aoe_pattern_list: list[list[tuple[int, int, int]]],
     characters: list[int], monster : Monster) ->list[tuple[set[int], list[int], set[int]]]:

        non_aoe_targetable_character,distances = self.find_targetable_character_around_location(location, characters, monster.attack_range())

        if not monster.is_aoe():
            return [self.get_attacks_targets([],characters,location,non_aoe_targetable_character)]
        if monster.is_melee_aoe():
            # add non-AoE targets and consider result
            aoe_hexess = [self.get_attacks_targets([self.map.apply_rotated_aoe_offset(location, aoe_offset, aoe_rotation)
                        # loop over each hex in the aoe, adding targets
                                                    for aoe_offset in aoe],
                                                    characters,location,non_aoe_targetable_character)
                    # loop over every possible aoe placement
                    for aoe_rotation in range(12)]
        else:
            aoe_hexess =  [self.get_attacks_targets(aoe_hexes,characters,location,non_aoe_targetable_character)
                                 for aoe_hexes in
                                [# loop over each hex in the aoe, adding targets
                                    [self.map.apply_aoe_offset(aoe_location, aoe_offset) for aoe_offset in aoe_pattern]
                                # loop over all aoe placements that hit characters
                                for aoe_pattern in aoe_pattern_list
                                for aoe_location in characters]
                    if any(distances[target] <= monster.attack_range() for target in aoe_hexes)]

        return aoe_hexess

    def find_targetable_character_around_location(self, location:int, characters:list[int], range:int) -> tuple[set[int],list[int]]:
        distances = self.map.find_proximity_distances_within_range(location,range)
        targetable_character={_ for _ in characters if distances[_] <= range and self.map.test_los_between_locations(_, location, self.RULE_VERTEX_LOS)}
        return targetable_character,distances
        
    def calculate_aoe_score(self, travel_distances:list[int], dest: tuple[frozenset[int], frozenset[int], int, int], focus_ranks:dict[int,int]):
        targets_of_rank = [0] * (max(focus_ranks.values()) + 1)
        for target in dest[1]:
            targets_of_rank[focus_ranks[target]] -= 1
        # best_groupss = (
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_group = (
                -(dest[3]),
                travel_distances[dest[2]],
                ) + tuple(targets_of_rank)

        return this_group
    
    def find_focus(self,travel_distances: list[int], trap_counts: list[int],characters: list[int], active_monster:int,character_location:list[tuple[int, set[int], list[int]]]) -> tuple[set[int], dict[int, int]]:

        character_location2 =[(charp,
                        char_loc[0])
                        for char_loc in character_location
                        for charp in char_loc[1]]
          
        proximity_distances = self.map.find_proximity_distances(active_monster)
        
        focuses:set[int]={focus[0]
                for focus in self.find_minimums_values(character_location2,lambda x: self.calculate_focus_score(travel_distances, trap_counts, proximity_distances, x[0], x[1]))} if len(character_location2)>0 else set()

        # rank characters for secondary targeting

        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in characters]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}

        return focuses, focus_ranks

    def find_attackable_location_for_characters(self, travel_distances: list[int], aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int], monster:Monster)-> list[tuple[frozenset[int], int, frozenset[int], frozenset[int], frozenset[int]]]:
        location_where_char_can_be_attacked=       list({location for character in characters
                        for location,distance in enumerate(self.map.find_proximity_distances_within_range(character,monster.attack_range() + monster.aoe_reach()-monster.is_melee_aoe()))                        
                        if distance != MAX_VALUE and
                            travel_distances[location] != MAX_VALUE and
                            self.map.can_end_move_on(location)})
        return list({(frozenset(aoe_targets.union(non_aoe_targets)),location,frozenset(aoe_targets),frozenset(aoe_hexes),frozenset(non_aoe_targets))
                        for location in location_where_char_can_be_attacked
                        for aoe_targets, aoe_hexes, non_aoe_targets in self.enumerate_aoe_possiblity(aoe, location, aoe_pattern_list, characters,monster)
                         })

    def find_attackable_location_for_characters_for_focus(self, travel_distances: list[int], aoe: list[tuple[int, int, int]], aoe_pattern_list: list[list[tuple[int, int, int]]], characters: list[int], monster:Monster)-> list[tuple[int, set[int], list[int]]]:
        location_where_char_can_be_attacked=       list({location for character in characters
                        for location,distance in enumerate(self.map.find_proximity_distances_within_range(character,monster.attack_range()+monster.aoe_reach()-monster.is_melee_aoe()))                        
                        if distance != MAX_VALUE and
                            travel_distances[location] != MAX_VALUE and
                            self.map.can_end_move_on(location)})
        return [(location,)+self.find_targetable_character_around_location(location, characters, monster.attack_range()+monster.aoe_reach()-monster.is_melee_aoe())
                        for location in location_where_char_can_be_attacked]

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
        sights = [self.map.solve_sight(_,MAX_VALUE, self.RULE_VERTEX_LOS) for _ in viewpoints]

        if self.logging:
            for sight in sights:
                visible_locations = [False] * self.map.map_size
                visible_locations[self.map.get_active_monster_location()] = True
                for visible_range in sight:
                    for location in range(*visible_range):
                        visible_locations[location] = True
                self.map.print_los_map(visible_locations)

        return sights