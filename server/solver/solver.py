import textwrap

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

        active_monster = self.map.get_active_monster_location()
    
        characters = self.map.get_characters()

        if not characters:
            return [(active_monster, -1, [], frozenset(), [], set())]

        travel_distances, trap_counts = self.map.find_path_distances(active_monster)

        proximity_distances = self.map.find_proximity_distances(active_monster)

        focuses, focus_ranks = self.find_focus(travel_distances, trap_counts, characters,proximity_distances,list(self.map.get_all_location_attackable_char(self.RULE_VERTEX_LOS)))

        # if we find no actions, stand still
        if not focuses:
            return [(active_monster, -1, [], frozenset(), [], set())]

        solution: list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]] = []

        solution = [(focus, location, [location], list(target), frozenset(y[0] for y in self.map.get_all_attackable_char_combination_for_a_location(location, self.RULE_VERTEX_LOS) if y[1]==target),{self.map.find_shortest_sightline(location, attack, self.RULE_VERTEX_LOS) for attack in target})
                    if travel_distances[location] <= monster.action_move and monster.has_attack()
                    else (focus,location, self.move_closer_to_destinations(travel_distances, trap_counts, location,monster),[],frozenset(),set())
                    for focus in focuses for target,location in self.solve_for_focus(focus, travel_distances, focus_ranks, monster, trap_counts,len(characters))]
                    # players choose among focus ties

        if self.logging:
            self.print_solution(active_monster, solution)

        return solution

    def solve_for_focus(self, focus: int, travel_distances: list[int], focus_ranks :dict[int,int], monster : Monster, trap_counts: list[int],number_of_character:int) -> list[tuple[frozenset[int], int]]:
        locations = self.best_location_to_attack_focus(focus,travel_distances,monster,trap_counts)

        groups = self.find_all_locations_to_attack_best_target_group(travel_distances, focus_ranks, locations,number_of_character,focus)

        return self.find_best_locations_to_attack_best_target_group(travel_distances, monster, groups)
        
    def find_best_locations_to_attack_best_target_group(self, travel_distances: list[int], monster: Monster, groups: list[tuple[frozenset[int], set[int]]])-> list[tuple[frozenset[int], int]]:
        loc = [(dest[0],d) for dest in groups for d in dest[1]]
        return self.find_minimums_values(loc, lambda x: self.calculate_destination_score(travel_distances,x,monster))

    def best_location_to_attack_focus(self, focus: int, travel_distances: list[int],  monster : Monster, trap_counts: list[int])->set[int]:
        locations_characters=[loc_chars[0] for loc_chars in self.map.get_all_attackable_char_by_location(self.RULE_VERTEX_LOS) if focus in loc_chars[1]]
        return set(self.find_minimums_values(locations_characters, partial(self.calculate_location_score, travel_distances, trap_counts, focus,monster)))
  
    def find_all_locations_to_attack_best_target_group(self, travel_distances: list[int], focus_ranks: dict[int, int], locations: set[int],number_of_character:int,focus:int)-> list[tuple[frozenset[int], set[int]]]:
        targets_prop2=[ x for x in self.map.get_all_attackable_char_combination_for_a_location2(locations, self.RULE_VERTEX_LOS).items() if focus in x[0]]
        return self.find_minimums_values(targets_prop2,lambda x: self.calculate_aoe_score(travel_distances, x, focus_ranks, number_of_character))
        
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
                action_debug_tags = list(map_debug_tags)
                self.print_single_solution_summary(active_monster, action[1], list(action[3]))                
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

    def calculate_destination_score(self, travel_distances:list[int], dest:tuple[frozenset[int],int], monster : Monster):

        this_destination = (
                sum((monster.is_susceptible_to_disavantage() and self.map.is_adjacent(dest[1], target) for target in dest[0])),
                travel_distances[dest[1]])

        return this_destination

    def calculate_aoe_score(self, travel_distances:list[int], dest: tuple[frozenset[int], set[int]], focus_ranks:dict[int,int], number_of_character:int):
        targets_of_rank = [0] * number_of_character
        for target in dest[0]:
            targets_of_rank[focus_ranks[target]] -= 1
        # best_groupss = (
        #     MAX_VALUE - 1,  # path length to the attack location
        # ) + tuple([0] * num_focus_ranks)  # target count for each focus rank
        this_group = (
                -len(dest[0]),
                min([travel_distances[loc] for loc in dest[1]]),
                tuple(targets_of_rank))

        return this_group
    
    def find_focus(self,travel_distances: list[int], trap_counts: list[int],characters: list[int], proximity_distances: list[int],character_location: list[tuple[int, int]]) -> tuple[set[int], dict[int, int]]:

        focuses:set[int]={focus[0]
                for focus in self.find_minimums_values(character_location,lambda x: self.calculate_focus_score(travel_distances, trap_counts, proximity_distances, x[0], x[1]))} if len(character_location)>0 else set()

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