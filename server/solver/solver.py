import textwrap
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from pipe import select, chain, filter
from solver.utils import minima, inverse_list

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
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl
        #Prioritize focus disadvantage
        self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE = rule != Rule.Frost

    def calculate_monster_move(self) -> list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]]:

        if self.logging:
            self.map.print()
            if self.map.monster.is_aoe():
                self.map.print_aoe_map()
            self.map.print_initiative_map()
            self.map.print_summary(self.debug_toggle)
            if self.message:
                print(textwrap.fill(self.message, 82))
        
        proximity_distances = self.map.find_proximity_distances(self.map.get_active_monster_location())

        travel_distances, trap_counts = self.map.find_active_monster_traversal_cost()

        focus_ranks = self.find_secondary_focus(proximity_distances)        
        
        solution = list(self.map.get_all_location_attackable_char()|
                        minima(lambda char_loc : trap_counts[char_loc[1]]) |
                        minima(lambda char_loc : travel_distances[char_loc[1]]) |
                        minima(lambda char_loc : 0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[char_loc[0]]) |
                        minima(lambda char_loc : self.map.get_character_initiative(char_loc[0])) |
                        select(lambda char_loc : char_loc[0])| 
                                select(lambda focus : (self.solve_for_focus(focus, travel_distances, focus_ranks, trap_counts) | 
                                    select(lambda tar_loc : (focus, tar_loc[1], [tar_loc[1]], list(tar_loc[0]), list(self.map.get_all_attackable_char_combination_for_a_location(tar_loc[1])[frozenset(tar_loc[0])] | select(lambda x : x[1])),{self.map.find_shortest_sightline(tar_loc[1], attack) for attack in tar_loc[0]})
                                                if self.map.can_monster_reach(travel_distances, tar_loc[1]) and self.map.does_monster_attack()
                                                else (focus,tar_loc[1], self.move_closer_to_destinations(travel_distances, trap_counts, tar_loc[1]),[],frozenset(),set()))))|chain)
        
        if self.logging:
            self.print_solution(solution)

        return solution if len(solution)>0 else [(self.map.get_active_monster_location(), -1, [], [], frozenset(), set())]

    def solve_for_focus(self, focus: int, travel_distances: list[int], focus_ranks :dict[int,int],trap_counts: list[int]) -> list[tuple[frozenset[int], int]]:
        def target_count_for_each_focus_rank(focus_ranks:dict[int,int], group:frozenset[int]) -> tuple[int]:
            targets_of_rank = [0] * len(focus_ranks)
            for target in group:
                targets_of_rank[focus_ranks[target]] -= 1
            return tuple(targets_of_rank)
        
        return (self.map.get_locations_hitting(focus) |
                minima(lambda loc : trap_counts[loc]) |
                minima(lambda loc : -int(self.map.can_monster_reach(travel_distances, loc))) |
                minima(lambda loc : int(self.map.are_location_at_disadvantage(focus, loc)) if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE else 0) |
                inverse_list(lambda loc:self.map.get_all_attackable_char_combination_for_a_location(loc).keys()) |
                filter(lambda group : focus in group[0]) |
                minima(lambda group :-len(group[0])) |
                minima(lambda group : min((travel_distances[loc] for loc in group[1]))) |
                minima(lambda group : target_count_for_each_focus_rank(focus_ranks, group[0])) |
                select(lambda group : group[1] | select (lambda grp : (group[0],grp))) | chain |
                minima(lambda loc : sum(((self.map.are_location_at_disadvantage(target, loc[1])) for target in loc[0]))) |
                minima(lambda loc : travel_distances[loc[1]]) )

    def move_closer_to_destinations(self, travel_distances: list[int], trap_counts: list[int], destination: int)->list[int]:
        distance_to_destination, traps_to_destination = self.map.find_active_monster_traversal_cost(destination)

        return (range(self.map.map_size) |
                filter(lambda location : self.map.can_monster_reach(travel_distances,location) and self.map.can_end_move_on(location)) |
                minima(lambda location : traps_to_destination[location] + trap_counts[location]) |
                minima(lambda location : distance_to_destination[location]) |
                minima(lambda location : travel_distances[location]))

    def find_secondary_focus(self, proximity_distances: list[int]):
        secondary_score = [self.calculate_secondary_focus_score(proximity_distances, character) for character in self.map.get_characters()]
        sorted_score = sorted({_[0] for _ in secondary_score})
        focus_ranks = {y[1]: sorted_score.index(y[0]) for y in secondary_score}
        return focus_ranks

    def calculate_secondary_focus_score(self,proximity_distances:list[int], character:int):
        return (0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[character], self.map.get_character_initiative(character)),character

    def solve_reaches(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        monster = self.map.get_active_monster()
        return [self.map.solve_sight(_,1 if monster.action_range == 0 else monster.action_range) for _ in viewpoints] if  monster.action_target != 0 else []

    def solve_sights(self, viewpoints: list[int]) -> list[list[tuple[int, int]]]:
        sights = [self.map.solve_sight(_,MAX_VALUE) for _ in viewpoints]

        if self.logging:
            for sight in sights:
                visible_locations = [False] * self.map.map_size
                visible_locations[self.map.get_active_monster_location()] = True
                for visible_range in sight:
                    for location in range(*visible_range):
                        visible_locations[location] = True
                self.map.print_los_map(visible_locations)

        return sights
                
    def print_solution(self, solution: list[tuple[int, int,list[int], list[int], frozenset[frozenset[int]], set[tuple[tuple[float, float], tuple[float, float]]]]]):
        active_monster = self.map.get_active_monster_location()
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