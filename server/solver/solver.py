import textwrap
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from solver.utils import dedup, invert_key_values, minima

SightLine = tuple[tuple[float, float], tuple[float, float]]
TargetSelection = tuple[frozenset[int], int, int, list[int]]
MonsterMove = tuple[int, int, list[int], list[int], list[frozenset[int]], set[SightLine]]
PreindexedTargetGroup = tuple[frozenset[int], frozenset[int]]

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
        self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE = rule != Rule.Frost
        self.RULE_MAXIMIZE_FUTURE_MULTIATTACK = rule != Rule.Frost
        #rank secondary targets' priority using focus rules
        self.RULE_RANK_SECONDARY_TARGETS = rule != Rule.Frost
    def calculate_monster_move(self) -> list[MonsterMove]:

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

        solution: list[MonsterMove] = []

        for focus_solution in self.solve(travel_distances, focus_ranks, trap_counts, proximity_distances):
            for tar_loc in focus_solution:
                if [tar_loc[1]] == tar_loc[3] and self.map.does_monster_attack():
                    attack_patterns = self.map.get_all_attackable_char_combination_for_a_location(tar_loc[1])[tar_loc[0]]
                    aoe_patterns = [aoe_pattern for _, pattern_group, _ in attack_patterns for aoe_pattern in pattern_group]
                    solution.append(
                        (
                            tar_loc[2],
                            tar_loc[1],
                            tar_loc[3],
                            list(tar_loc[0]),
                            aoe_patterns,
                            {self.map.find_shortest_sightline(tar_loc[1], attack) for attack in tar_loc[0]},
                        )
                    )
                else:
                    solution.append((tar_loc[2], tar_loc[1], tar_loc[3], [], [], set()))
        
        if self.logging:
            self.print_solution(solution)

        return solution if solution else [(self.map.get_active_monster_location(), -1, [], [], [], set())]

    def solve(
        self,
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        trap_counts: list[int],
        proximity_distances: list[int],
    ) -> list[list[TargetSelection]]:
        focus_candidates = list(self.map.get_all_location_attackable_char())
        focus_candidates = minima(focus_candidates, lambda char_loc: trap_counts[char_loc[1]])
        focus_candidates = minima(focus_candidates, lambda char_loc: travel_distances[char_loc[1]])
        focus_candidates = minima(
            focus_candidates,
            lambda char_loc: 0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[char_loc[0]],
        )
        focus_candidates = minima(
            focus_candidates,
            lambda char_loc: self.map.get_character_initiative(char_loc[0]),
        )
        focuses = dedup([char_loc[0] for char_loc in focus_candidates])

        attack_locations_by_focus = {
            focus: self.candidate_attack_locations_for_focus(focus, travel_distances, trap_counts)
            for focus in focuses
        }
        grouped_target_index = self.build_grouped_target_index(attack_locations_by_focus)

        return [
            self.solve_for_focus(
                focus,
                attack_locations_by_focus[focus],
                grouped_target_index.get(focus, []),
                travel_distances,
                focus_ranks,
                trap_counts,
            )
            for focus in focuses
        ]

    def target_count_for_each_focus_rank(self, focus_ranks: dict[int, int], group: frozenset[int]) -> tuple[int, ...]:
        targets_of_rank = [0] * len(focus_ranks)
        for target in group:
            targets_of_rank[focus_ranks[target]] -= 1
        return tuple(targets_of_rank)

    def get_attackable_groups(self, location: int) -> list[frozenset[int]]:
        attackable_combinations = self.map.get_all_attackable_char_combination_for_a_location(location)
        return list(attackable_combinations.keys())

    def candidate_attack_locations_for_focus(
        self,
        focus: int,
        travel_distances: list[int],
        trap_counts: list[int],
    ) -> list[int]:
        attack_locations = [
            char_loc[1]
            for char_loc in self.map.get_all_location_attackable_char()
            if char_loc[0] == focus
        ]
        attack_locations = minima(attack_locations, lambda loc: trap_counts[loc])
        attack_locations = minima(
            attack_locations,
            lambda loc: -int(self.map.can_monster_reach(travel_distances, loc)),
        )
        return minima(
            attack_locations,
            lambda loc: int(self.map.are_location_at_disadvantage(focus, loc)) if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE else 0,
        )

    def build_grouped_target_index(
        self,
        attack_locations_by_focus: dict[int, list[int]],
    ) -> dict[int, list[PreindexedTargetGroup]]:
        unique_attack_locations = {
            location
            for attack_locations in attack_locations_by_focus.values()
            for location in attack_locations
        }
        locations_by_group: dict[frozenset[int], set[int]] = {}
        for location in unique_attack_locations:
            for target_group in self.get_attackable_groups(location):
                locations_by_group.setdefault(target_group, set()).add(location)

        grouped_targets_by_focus: dict[int, list[PreindexedTargetGroup]] = {}
        for target_group, locations in locations_by_group.items():
            indexed_group = (target_group, frozenset(locations))
            for focus in target_group:
                grouped_targets_by_focus.setdefault(focus, []).append(indexed_group)

        return grouped_targets_by_focus

    def grouped_targets_with_locations(
        self,
        focus: int,
        attack_locations_for_focus: list[int],
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        indexed_target_groups: list[PreindexedTargetGroup] | None = None,
    ) -> list[tuple[frozenset[int], int]]:
        if indexed_target_groups is None:
            grouped_targets = invert_key_values(attack_locations_for_focus, self.get_attackable_groups)
            grouped_targets = [tar_locs for tar_locs in grouped_targets if focus in tar_locs[0]]
        else:
            attack_locations = set(attack_locations_for_focus)
            grouped_targets = []
            for target_group, locations in indexed_target_groups:
                matching_locations = attack_locations.intersection(locations)
                if matching_locations:
                    grouped_targets.append((target_group, matching_locations))

        grouped_targets = minima(grouped_targets, lambda tar_locs: -len(tar_locs[0]))
        grouped_targets = minima(
            grouped_targets,
            lambda tar_locs: min(travel_distances[loc] for loc in tar_locs[1]),
        )
        if self.RULE_RANK_SECONDARY_TARGETS:
            grouped_targets = minima(
                grouped_targets,
                lambda tar_locs: self.target_count_for_each_focus_rank(focus_ranks, tar_locs[0]),
            )

        targets_with_attack_locations = [
            (target_group, location)
            for target_group, locations in grouped_targets
            for location in locations
        ]
        return minima(
            targets_with_attack_locations,
            lambda tar_loc: sum(
                self.map.are_location_at_disadvantage(target, tar_loc[1])
                for target in tar_loc[0]
            ),
        )
    
    def solve_for_focus(
        self,
        focus: int,
        attack_locations_for_focus: list[int],
        indexed_target_groups: list[PreindexedTargetGroup],
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        trap_counts: list[int],
    ) -> list[TargetSelection]:
        if not attack_locations_for_focus:
            return []
        
        targets_with_attack_locations: list[tuple[frozenset[int], int]]
        if (
            not self.RULE_MAXIMIZE_FUTURE_MULTIATTACK
            and not self.map.can_monster_reach(travel_distances, attack_locations_for_focus[0])
        ):
            targets_with_attack_locations = [(frozenset({focus}), loc) for loc in attack_locations_for_focus]
        else:
            targets_with_attack_locations = self.grouped_targets_with_locations(
                focus,
                attack_locations_for_focus,
                travel_distances,
                focus_ranks,
                indexed_target_groups,
            )
        
        targets_with_attack_locations = minima(
            targets_with_attack_locations,
            lambda tar_loc: travel_distances[tar_loc[1]],
        )

        return [
            (
                tar_loc[0],
                tar_loc[1],
                focus,
                self.reachable_locations_this_turn(travel_distances, trap_counts, tar_loc[1]),
            )
            for tar_loc in targets_with_attack_locations
        ]

    def reachable_locations_this_turn(self, travel_distances: list[int], trap_counts: list[int], destination: int)->list[int]:
        if self.map.can_monster_reach(travel_distances, destination) :
            return [destination]
        
        distance_to_destination, traps_to_destination = self.map.find_active_monster_traversal_cost(destination)

        reachable_locations = [
            location
            for location in range(self.map.map_size)
            if self.map.can_monster_reach(travel_distances, location) and self.map.can_end_move_on(location)
        ]
        reachable_locations = minima(
            reachable_locations,
            lambda location: traps_to_destination[location] + trap_counts[location],
        )
        reachable_locations = minima(reachable_locations, lambda location: distance_to_destination[location])
        return minima(reachable_locations, lambda location: travel_distances[location])

    def find_secondary_focus(self, proximity_distances: list[int]):
        secondary_scores = [self.calculate_secondary_focus_score(proximity_distances, character) for character in self.map.get_characters()]
        rank_for_score = {score: rank for rank, score in enumerate(sorted({score for score, _ in secondary_scores}))}
        return {character: rank_for_score[score] for score, character in secondary_scores}

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
                
    def print_solution(self, solution: list[MonsterMove]):
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