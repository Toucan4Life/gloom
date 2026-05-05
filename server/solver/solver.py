import textwrap
from typing import Any
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from solver.utils import dedup, invert_key_values, minima

SightLine = tuple[tuple[float, float], tuple[float, float]]
TargetSelection = tuple[frozenset[int], int, int, list[int]]
MonsterMove = tuple[int, int, list[int], list[int], list[frozenset[int]], set[SightLine]]
PreindexedTargetGroup = tuple[frozenset[int], frozenset[int]]
ChoiceExplainStage = dict[str, object]
ChoiceExplainAction = dict[str, object]
ExplainedTargetSelection = tuple[TargetSelection, list[ChoiceExplainStage]]

class Solver:
    logging: bool
    debug_visuals: bool
    show_each_action_separately: bool
    debug_lines: set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]
    debug_toggle: bool
    explain_choice: bool
    choice_explain_shared: list[ChoiceExplainStage]
    choice_explain_actions: list[ChoiceExplainAction]
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
        self.explain_choice = False
        self.choice_explain_shared = []
        self.choice_explain_actions = []
        self.rule=rule
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl
        self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE = rule != Rule.Frost
        self.RULE_MAXIMIZE_FUTURE_MULTIATTACK = rule != Rule.Frost
        #rank secondary targets' priority using focus rules
        self.RULE_RANK_SECONDARY_TARGETS = rule != Rule.Frost
    def calculate_monster_move(self) -> list[MonsterMove]:
        self.choice_explain_shared = []
        self.choice_explain_actions = []

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
            for tar_loc, explain_stages in focus_solution:
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

                if self.explain_choice:
                    self.choice_explain_actions.append(
                        {
                            'label': self._selection_label(tar_loc[2], tar_loc[1], tar_loc[0]),
                            'focus': tar_loc[2],
                            'attack_location': tar_loc[1],
                            'targets': sorted(tar_loc[0]),
                            'move_options': list(tar_loc[3]),
                            'stages': list(explain_stages),
                        }
                    )
        
        if self.logging:
            self.print_solution(solution)

        if solution:
            return solution

        if self.explain_choice:
            self._append_choice_info_stage(
                self.choice_explain_shared,
                'no-action',
                'No action is available',
                'No focus or attack position was found, so the monster takes no action.',
                [],
            )
            self.choice_explain_actions.append(
                {
                    'label': 'No action',
                    'focus': -1,
                    'attack_location': -1,
                    'targets': [],
                    'move_options': [self.map.get_active_monster_location()],
                    'stages': [],
                }
            )

        return [(self.map.get_active_monster_location(), -1, [], [], [], set())]

    def solve(
        self,
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        trap_counts: list[int],
        proximity_distances: list[int],
    ) -> list[list[ExplainedTargetSelection]]:
        focus_candidates = list(self.map.get_all_location_attackable_char())
        narrowed_focus_candidates = minima(focus_candidates, lambda char_loc: trap_counts[char_loc[1]])
        self._append_choice_stage(
            self.choice_explain_shared,
            'focus-trap-cost',
            'Avoid trap and hazardous paths',
            'The AI first prefers attack paths that cross the fewest trap or hazardous hexes.',
            focus_candidates,
            narrowed_focus_candidates,
            self._format_focus_path_candidate,
            lambda char_loc: trap_counts[char_loc[1]],
            'trap_steps',
        )
        focus_candidates = narrowed_focus_candidates
        narrowed_focus_candidates = minima(focus_candidates, lambda char_loc: travel_distances[char_loc[1]])
        self._append_choice_stage(
            self.choice_explain_shared,
            'focus-travel-distance',
            'Prefer the shortest travel distance',
            'If several focus candidates are equally safe, the AI keeps the ones that need the least movement to reach an attack hex.',
            focus_candidates,
            narrowed_focus_candidates,
            self._format_focus_path_candidate,
            lambda char_loc: travel_distances[char_loc[1]],
            'travel_distance',
        )
        focus_candidates = narrowed_focus_candidates
        narrowed_focus_candidates = minima(
            focus_candidates,
            lambda char_loc: 0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[char_loc[0]],
        )
        self._append_choice_stage(
            self.choice_explain_shared,
            'focus-proximity',
            'Break ties with proximity',
            'If travel distance still ties, the AI checks proximity. Jaws of the Lion keeps this as a no-op tie confirmation.',
            focus_candidates,
            narrowed_focus_candidates,
            self._format_focus_path_candidate,
            lambda char_loc: 0 if self.RULE_PROXIMITY_FOCUS else proximity_distances[char_loc[0]],
            'proximity',
        )
        focus_candidates = narrowed_focus_candidates
        narrowed_focus_candidates = minima(
            focus_candidates,
            lambda char_loc: self.map.get_character_initiative(char_loc[0]),
        )
        self._append_choice_stage(
            self.choice_explain_shared,
            'focus-initiative',
            'Break ties with initiative',
            'If safety, travel distance, and proximity still tie, the AI prefers the lower initiative.',
            focus_candidates,
            narrowed_focus_candidates,
            self._format_focus_path_candidate,
            lambda char_loc: self.map.get_character_initiative(char_loc[0]),
            'initiative',
        )
        focus_candidates = narrowed_focus_candidates
        focuses = dedup([char_loc[0] for char_loc in focus_candidates])
        self._append_choice_info_stage(
            self.choice_explain_shared,
            'focus-survivors',
            'Remaining focuses',
            'The surviving focuses advance to the attack-position checks.',
            [self._format_focus_candidate(focus) for focus in focuses],
        )

        attack_trace_by_focus: dict[int, list[ChoiceExplainStage]] = {}
        attack_locations_by_focus: dict[int, list[int]] = {}
        for focus in focuses:
            attack_locations, attack_trace = self.candidate_attack_locations_for_focus(
                focus,
                travel_distances,
                trap_counts,
            )
            attack_locations_by_focus[focus] = attack_locations
            attack_trace_by_focus[focus] = attack_trace
        grouped_target_index = self.build_grouped_target_index(attack_locations_by_focus)

        return [
            self.solve_for_focus(
                focus,
                attack_locations_by_focus[focus],
                attack_trace_by_focus[focus],
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
    ) -> tuple[list[int], list[ChoiceExplainStage]]:
        trace: list[ChoiceExplainStage] = []
        attack_locations = [
            char_loc[1]
            for char_loc in self.map.get_all_location_attackable_char()
            if char_loc[0] == focus
        ]
        narrowed_locations = minima(attack_locations, lambda loc: trap_counts[loc])
        self._append_choice_stage(
            trace,
            f'focus-{focus}-attack-trap-cost',
            'Avoid trap and hazardous paths',
            'Among the hexes that can attack the current focus, prefer the routes with the fewest trap or hazardous steps.',
            attack_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda loc: trap_counts[loc],
            'trap_steps',
        )
        attack_locations = narrowed_locations
        narrowed_locations = minima(
            attack_locations,
            lambda loc: -int(self.map.can_monster_reach(travel_distances, loc)),
        )
        self._append_choice_stage(
            trace,
            f'focus-{focus}-attack-reachability',
            'Prefer reachable attack hexes',
            'If possible, keep the attack hexes that the monster can reach this turn.',
            attack_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda loc: int(not self.map.can_monster_reach(travel_distances, loc)),
            'unreachable_penalty',
        )
        attack_locations = narrowed_locations
        narrowed_locations = minima(
            attack_locations,
            lambda loc: int(self.map.are_location_at_disadvantage(focus, loc)) if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE else 0,
        )
        self._append_choice_stage(
            trace,
            f'focus-{focus}-attack-focus-disadvantage',
            'Avoid disadvantage on the focus',
            'The AI keeps attack hexes that avoid disadvantage on the focus when that rule applies. Frosthaven keeps this stage as a no-op tie confirmation.',
            attack_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda loc: int(self.map.are_location_at_disadvantage(focus, loc)) if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE else 0,
            'focus_disadvantage',
        )
        return narrowed_locations, trace

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
        trace: list[ChoiceExplainStage],
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

        narrowed_groups = minima(grouped_targets, lambda tar_locs: -len(tar_locs[0]))
        self._append_choice_stage(
            trace,
            f'focus-{focus}-target-count',
                'Maximize the number of targets',
                'From the candidate attack patterns for the current focus, keep the groups that hit the most targets.',
            grouped_targets,
            narrowed_groups,
            self._format_group_candidate,
            lambda tar_locs: -len(tar_locs[0]),
            'negative_target_count',
        )
        grouped_targets = narrowed_groups
        narrowed_groups = minima(
            grouped_targets,
            lambda tar_locs: min(travel_distances[loc] for loc in tar_locs[1]),
        )
        self._append_choice_stage(
            trace,
            f'focus-{focus}-target-distance',
            'Break target-group ties by distance',
            'If multiple target groups hit the same number of targets, keep the ones that can be reached with the least travel.',
            grouped_targets,
            narrowed_groups,
            self._format_group_candidate,
            lambda tar_locs: min(travel_distances[loc] for loc in tar_locs[1]),
            'best_travel_distance',
        )
        grouped_targets = narrowed_groups
        if self.RULE_RANK_SECONDARY_TARGETS:
            narrowed_groups = minima(
                grouped_targets,
                lambda tar_locs: self.target_count_for_each_focus_rank(focus_ranks, tar_locs[0]),
            )
            self._append_choice_stage(
                trace,
                f'focus-{focus}-secondary-ranks',
                'Rank secondary targets',
                'With the focus fixed, secondary targets are ranked using the same focus rules and better ranked groups survive.',
                grouped_targets,
                narrowed_groups,
                self._format_group_candidate,
                lambda tar_locs: self.target_count_for_each_focus_rank(focus_ranks, tar_locs[0]),
                'secondary_target_ranks',
            )
            grouped_targets = narrowed_groups
        else:
            self._append_choice_info_stage(
                trace,
                f'focus-{focus}-secondary-ranks-skipped',
                'Frosthaven skips secondary-target ranking',
                'Frosthaven does not use the secondary-target ranking tie-break here.',
                [self._format_group_candidate(grouped_target) for grouped_target in grouped_targets],
            )

        targets_with_attack_locations = [
            (target_group, location)
            for target_group, locations in grouped_targets
            for location in locations
        ]
        narrowed_targets = minima(
            targets_with_attack_locations,
            lambda tar_loc: sum(
                self.map.are_location_at_disadvantage(target, tar_loc[1])
                for target in tar_loc[0]
            ),
        )
        self._append_choice_stage(
            trace,
            f'focus-{focus}-target-disadvantage',
            'Minimize disadvantage across attacked targets',
            'Finally, keep the attack hexes that create the least total disadvantage across the attacked targets.',
            targets_with_attack_locations,
            narrowed_targets,
            self._format_target_location_candidate,
            lambda tar_loc: sum(
                self.map.are_location_at_disadvantage(target, tar_loc[1])
                for target in tar_loc[0]
            ),
            'total_disadvantage',
        )
        return narrowed_targets
    
    def solve_for_focus(
        self,
        focus: int,
        attack_locations_for_focus: list[int],
        attack_trace: list[ChoiceExplainStage],
        indexed_target_groups: list[PreindexedTargetGroup],
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        trap_counts: list[int],
    ) -> list[ExplainedTargetSelection]:
        if not attack_locations_for_focus:
            return []

        trace = list(attack_trace)
        
        targets_with_attack_locations: list[tuple[frozenset[int], int]]
        if (
            not self.RULE_MAXIMIZE_FUTURE_MULTIATTACK
            and not self.map.can_monster_reach(travel_distances, attack_locations_for_focus[0])
        ):
            targets_with_attack_locations = [(frozenset({focus}), loc) for loc in attack_locations_for_focus]
            self._append_choice_info_stage(
                trace,
                f'focus-{focus}-future-multiattack-skipped',
                'Frosthaven ignores future multi-target potential',
                'Because the monster cannot reach an attack hex this turn, Frosthaven keeps only direct attacks on the current focus.',
                [self._format_target_location_candidate(candidate) for candidate in targets_with_attack_locations],
            )
        else:
            targets_with_attack_locations = self.grouped_targets_with_locations(
                focus,
                attack_locations_for_focus,
                travel_distances,
                focus_ranks,
                trace,
                indexed_target_groups,
            )
        
        narrowed_targets = minima(
            targets_with_attack_locations,
            lambda tar_loc: travel_distances[tar_loc[1]],
        )
        self._append_choice_stage(
            trace,
            f'focus-{focus}-attack-distance',
            'Keep the nearest tied attack hexes',
            'Among the remaining attack patterns, keep the nearest attack hexes.',
            targets_with_attack_locations,
            narrowed_targets,
            self._format_target_location_candidate,
            lambda tar_loc: travel_distances[tar_loc[1]],
            'travel_distance',
        )
        targets_with_attack_locations = narrowed_targets

        results: list[ExplainedTargetSelection] = []
        for tar_loc in targets_with_attack_locations:
            move_options, move_stages = self.reachable_locations_this_turn(travel_distances, trap_counts, tar_loc[1])
            results.append(
                (
                    (
                        tar_loc[0],
                        tar_loc[1],
                        focus,
                        move_options,
                    ),
                    list(trace) + move_stages,
                )
            )
        return results

    def reachable_locations_this_turn(self, travel_distances: list[int], trap_counts: list[int], destination: int)->tuple[list[int], list[ChoiceExplainStage]]:
        trace: list[ChoiceExplainStage] = []
        if self.map.can_monster_reach(travel_distances, destination) :
            self._append_choice_info_stage(
                trace,
                f'destination-{destination}-reachable',
                'End on the attack hex',
                'The monster can already reach the chosen attack hex this turn, so it can end there immediately.',
                [self._format_location_candidate(destination)],
            )
            return [destination], trace
        
        distance_to_destination, traps_to_destination = self.map.find_active_monster_traversal_cost(destination)

        reachable_locations = [
            location
            for location in range(self.map.map_size)
            if self.map.can_monster_reach(travel_distances, location) and self.map.can_end_move_on(location)
        ]
        narrowed_locations = minima(
            reachable_locations,
            lambda location: traps_to_destination[location] + trap_counts[location],
        )
        self._append_choice_stage(
            trace,
            f'destination-{destination}-safest-route',
            'Keep the safest end hexes',
            'Among all reachable end hexes, keep the ones that add the fewest trap or hazardous steps on the route to the chosen attack hex.',
            reachable_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda location: traps_to_destination[location] + trap_counts[location],
            'combined_trap_steps',
        )
        reachable_locations = narrowed_locations
        narrowed_locations = minima(reachable_locations, lambda location: distance_to_destination[location])
        self._append_choice_stage(
            trace,
            f'destination-{destination}-remaining-distance',
            'Shorten the remaining path',
            'If several safe end hexes remain, keep the ones that leave the shortest remaining path to the chosen attack hex.',
            reachable_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda location: distance_to_destination[location],
            'remaining_distance',
        )
        reachable_locations = narrowed_locations
        narrowed_locations = minima(reachable_locations, lambda location: travel_distances[location])
        self._append_choice_stage(
            trace,
            f'destination-{destination}-movement-spent',
            'Break end-hex ties by movement spent',
            'If the end hexes are still tied, keep the ones that use the least movement this turn.',
            reachable_locations,
            narrowed_locations,
            self._format_location_candidate,
            lambda location: travel_distances[location],
            'movement_spent',
        )
        return narrowed_locations, trace

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

    def get_choice_explain(self) -> dict[str, object] | None:
        if not self.explain_choice:
            return None
        return {
            'shared_stages': self.choice_explain_shared,
            'actions': self.choice_explain_actions,
        }

    def _append_choice_stage(
        self,
        bucket: list[ChoiceExplainStage],
        stage_id: str,
        title: str,
        description: str,
        before_values: list[Any],
        after_values: list[Any],
        formatter,
        score_getter=None,
        score_label: str | None = None,
    ) -> None:
        if not self.explain_choice:
            return

        survivor_keys = {formatter(value)['key'] for value in after_values}
        candidates = []
        for value in before_values:
            candidate = dict(formatter(value))
            candidate['selected'] = candidate['key'] in survivor_keys
            if score_getter is not None:
                candidate['score'] = self._normalize_choice_value(score_getter(value))
            candidates.append(candidate)

        stage: ChoiceExplainStage = {
            'id': stage_id,
            'title': title,
            'description': description,
            'summary': self._build_choice_stage_summary(description, len(before_values), len(after_values)),
            'before_count': len(before_values),
            'after_count': len(after_values),
            'candidates': candidates,
        }
        if score_label is not None:
            stage['score_label'] = score_label
        bucket.append(stage)

    def _append_choice_info_stage(
        self,
        bucket: list[ChoiceExplainStage],
        stage_id: str,
        title: str,
        description: str,
        candidates: list[dict[str, object]],
    ) -> None:
        if not self.explain_choice:
            return

        normalized_candidates = []
        for candidate in candidates:
            normalized_candidate = dict(candidate)
            normalized_candidate.setdefault('selected', True)
            normalized_candidates.append(normalized_candidate)

        bucket.append(
            {
                'id': stage_id,
                'title': title,
                'description': description,
                'summary': description,
                'before_count': len(normalized_candidates),
                'after_count': len([candidate for candidate in normalized_candidates if candidate['selected']]),
                'candidates': normalized_candidates,
            }
        )

    def _build_choice_stage_summary(self, description: str, before_count: int, after_count: int) -> str:
        if before_count == 0:
            return description
        if before_count == after_count:
            return f'{description} No candidates were eliminated at this stage.'
        if after_count == 1:
            return f'{description} 1 of {before_count} candidates remains.'
        return f'{description} {after_count} of {before_count} candidates remain.'

    def _normalize_choice_value(self, value: Any) -> object:
        if isinstance(value, frozenset):
            return [self._normalize_choice_value(item) for item in sorted(value)]
        if isinstance(value, set):
            return [self._normalize_choice_value(item) for item in sorted(value)]
        if isinstance(value, tuple):
            return [self._normalize_choice_value(item) for item in value]
        return value

    def _selection_label(self, focus: int, attack_location: int, targets: frozenset[int]) -> str:
        target_label = ', '.join(str(target) for target in sorted(targets))
        return f'Focus {focus}, attack {target_label} from hex {attack_location}'

    def _format_focus_path_candidate(self, char_loc: tuple[int, int]) -> dict[str, object]:
        focus, location = char_loc
        return {
            'key': f'focus-path:{focus}:{location}',
            'label': f'Focus {focus} via attack hex {location}',
            'focus': focus,
            'location': location,
        }

    def _format_focus_candidate(self, focus: int) -> dict[str, object]:
        return {
            'key': f'focus:{focus}',
            'label': f'Focus {focus}',
            'focus': focus,
        }

    def _format_location_candidate(self, location: int) -> dict[str, object]:
        return {
            'key': f'location:{location}',
            'label': f'Hex {location}',
            'location': location,
        }

    def _format_group_candidate(self, grouped_target: tuple[frozenset[int], set[int] | frozenset[int]]) -> dict[str, object]:
        targets = sorted(grouped_target[0])
        locations = sorted(grouped_target[1])
        target_label = ', '.join(str(target) for target in targets)
        location_label = ', '.join(str(location) for location in locations)
        return {
            'key': f'group:{"-".join(str(target) for target in targets)}:{"-".join(str(location) for location in locations)}',
            'label': f'Targets {target_label} from hexes {location_label}',
            'targets': targets,
            'locations': locations,
        }

    def _format_target_location_candidate(self, target_location: tuple[frozenset[int], int]) -> dict[str, object]:
        targets = sorted(target_location[0])
        target_label = ', '.join(str(target) for target in targets)
        return {
            'key': f'target-location:{"-".join(str(target) for target in targets)}:{target_location[1]}',
            'label': f'Attack {target_label} from hex {target_location[1]}',
            'targets': targets,
            'location': target_location[1],
        }