import textwrap
from typing import Callable
from typing import Any
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE

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

    def calculate_monster_move(self) -> list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]]:

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
            return [(active_monster, -1, [], [], frozenset(), set())]

        character_location = list(self.map.get_all_location_attackable_char(self.RULE_VERTEX_LOS))

        # if we find no actions, stand still
        if not character_location:
            return [(active_monster, -1, [], [], frozenset(), set())]
        
        proximity_distances = self.map.find_proximity_distances(active_monster)

        travel_distances, trap_counts = self.map.find_path_distances(active_monster)
        
        focuses = self.find_focus(travel_distances, trap_counts,proximity_distances,character_location)

        focus_ranks = self.find_secondary_focus(characters, proximity_distances)

        solution: list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]] = []

        solution = [(focus, location, [location], list(target), frozenset(y[0] for y in self.map.get_all_attackable_char_combination_for_a_location(location, self.RULE_VERTEX_LOS) if y[1]==target),{self.map.find_shortest_sightline(location, attack, self.RULE_VERTEX_LOS) for attack in target})
                    if self.map.can_monster_reach(travel_distances, location) and self.map.does_monster_attack()
                    else (focus,location, self.move_closer_to_destinations(travel_distances, trap_counts, location),[],frozenset(),set())
                    for focus in focuses for target,location in self.solve_for_focus(focus, travel_distances, focus_ranks, trap_counts,len(characters))]
                    # players choose among focus ties

        if self.logging:
            self.print_solution(active_monster, solution)

        return solution

    def solve_for_focus(self, focus: int, travel_distances: list[int], focus_ranks :dict[int,int],trap_counts: list[int],number_of_character:int) -> list[tuple[frozenset[int], int]]:
        locations = self.best_location_to_attack_focus(focus,travel_distances,trap_counts)

        groups = self.find_all_locations_to_attack_best_target_group(travel_distances, focus_ranks, locations,number_of_character,focus)

        return self.find_best_locations_to_attack_best_target_group(travel_distances, groups)
        
    def find_best_locations_to_attack_best_target_group(self, travel_distances: list[int], groups: list[tuple[frozenset[int], set[int]]])-> list[tuple[frozenset[int], int]]:
        loc = [(dest[0],d) for dest in groups for d in dest[1]]
        
        location_criteria : list[Callable[[tuple[frozenset[int], int]], int]] = [
                            lambda loc: sum(((self.map.are_location_at_disadvantage(target, loc[1])) for target in loc[0])),#total_targets_at_disadvantage
                            lambda loc: travel_distances[loc[1]]] #travel_distance_to_location

        return self.find_minimums_values(loc, location_criteria)

    def best_location_to_attack_focus(self, focus: int, travel_distances: list[int], trap_counts: list[int])->set[int]:
        locations_characters=[loc_chars[0] for loc_chars in self.map.get_all_attackable_char_by_location(self.RULE_VERTEX_LOS) if focus in loc_chars[1]]

        location_criteria : list[Callable[[int], int]] = [
                            lambda loc : trap_counts[loc], #trap_to_attack_location
                            lambda loc : -int(self.map.can_monster_reach(travel_distances, loc)), #can_reach_attack_location
                            lambda loc : int(self.map.are_location_at_disadvantage(focus, loc))] #is_disadvantage_against_focus

        return set(self.find_minimums_values(locations_characters, location_criteria))
  
    def find_all_locations_to_attack_best_target_group(self, travel_distances: list[int], focus_ranks: dict[int, int], locations: set[int],number_of_character:int,focus:int)-> list[tuple[frozenset[int], set[int]]]:
        def target_count_for_each_focus_rank(number_of_character:int, focus_ranks:dict[int,int], dest:tuple[frozenset[int], set[int]]) -> tuple[int]:
            targets_of_rank = [0] * number_of_character
            for target in dest[0]:
                targets_of_rank[focus_ranks[target]] -= 1
            return tuple(targets_of_rank)
         
        group = [x for x in self.map.get_all_attackable_char_combination_for_a_location2(locations, self.RULE_VERTEX_LOS).items() if focus in x[0]]

        group_criteria : list[Callable[[tuple[frozenset[int], set[int]]], int | tuple[int]]] = [
                        lambda group : -len(group[0]), #total_number_of_target
                        lambda group : min((travel_distances[loc] for loc in group[1])), #path_length_to_the_attack_location
                        lambda group : target_count_for_each_focus_rank(number_of_character, focus_ranks, group)]

        return self.find_minimums_values(group,group_criteria)

    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int)->list[int]:
        distance_to_destination, traps_to_destination = self.map.find_path_distances_reverse(destination)

        locations = [location for location in range(self.map.map_size)
                            if self.map.can_monster_reach(travel_distances,location) and
                            self.map.can_end_move_on(location)]

        location_criteria: list[Callable[[int], int | tuple[int]]] = [
                            lambda location : traps_to_destination[location] + trap_counts[location], #traps_along_path
                            lambda location : distance_to_destination[location], #distance_to_destination
                            lambda location : travel_distances[location]] #ravel_distances

        return self.find_minimums_values(locations,location_criteria)

    def find_focus(self,travel_distances: list[int], trap_counts: list[int], proximity_distances: list[int], character_location: list[tuple[int, int]]) -> set[int]:
        focus_criteria : list[Callable[[tuple[int, int]], int | tuple[int]]] = [
                        lambda char_loc : trap_counts[char_loc[1]], #trap_count_to_location
                        lambda char_loc : travel_distances[char_loc[1]], #travel_distances_to_location
                        lambda char_loc : 0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[char_loc[0]], #proximity_distance_to_location
                        lambda char_loc : self.map.get_character_initiative(char_loc[0])] #char_initiative

        return {focus[0] for focus in self.find_minimums_values(character_location,focus_criteria)}

    def find_secondary_focus(self, characters: list[int], proximity_distances: list[int]):
        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in characters]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}
        return focus_ranks

    def calculate_secondary_focus_score(self,proximity_distances:list[int], character:int):
        return (proximity_distances[character], self.map.get_character_initiative(character)),character

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
                
    def print_solution(self, active_monster:int, solution: list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]]):
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

    def find_minimums_values(self,iterable:list[Any],score_functions:list[Callable[[Any],Any]]):
        num_function = len(score_functions)
        current_score=[MAX_VALUE]*num_function
        best_iterable:list[Any]=[]

        for _,candidate in enumerate(iterable):
            for j,func in enumerate(score_functions):
                evaluation = func(candidate)
                if (current_score[j]<evaluation):
                    break
                if(current_score[j]==evaluation):
                    if(j==num_function-1):
                        best_iterable.append(candidate)
                else:
                    current_score[j]=evaluation
                    if(j<num_function-1):
                        current_score[j+1:num_function]=[score_functions[z](candidate) for z in range(j+1,num_function)]
                    best_iterable=[candidate]
                    break

        return best_iterable