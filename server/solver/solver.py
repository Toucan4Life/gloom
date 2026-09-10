import textwrap
from typing import TypedDict
from solver.rule import Rule
from solver.gloomhaven_map import GloomhavenMap
from solver.settings import MAX_VALUE
from solver.utils import dedup, invert_key_values, minima

SightLine = tuple[tuple[float, float], tuple[float, float]]
TargetSelection = tuple[frozenset[int], int, int, list[int]]
MonsterMove = tuple[int, int, list[int], list[int], list[frozenset[int]], set[SightLine]]
PreindexedTargetGroup = tuple[frozenset[int], frozenset[int]]


class ExplanationStep(TypedDict):
    """A single, human-readable step of the monster AI's reasoning process.

    `focus` ties the step to the character (by location) the step was made
    while deciding for, or is None for steps that apply globally (e.g. while
    determining which character to focus on in the first place). `locations`
    lists the hexes relevant to the step (candidates remaining, chosen hex,
    etc.) so the UI can highlight/reference them.
    """
    phase: str
    title: str
    detail: str
    focus: int | None
    locations: list[int]


class Solver:
    logging: bool
    debug_visuals: bool
    show_each_action_separately: bool
    debug_lines: set[tuple[int, tuple[tuple[float, float], tuple[float, float]]]]
    debug_toggle: bool
    message: str
    rule:Rule
    explanation: list[ExplanationStep]
    def __init__(self, rule:Rule, gmap: GloomhavenMap ):
        self.map = gmap
        self.logging = False
        self.debug_visuals = False
        self.show_each_action_separately = True
        self.debug_lines = set()
        self.message = ''
        self.debug_toggle = False
        self.rule=rule
        self.explanation = []
        #proximity is ignored when determining monster focus
        self.RULE_PROXIMITY_FOCUS = rule == Rule.Jotl
        self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE = rule != Rule.Frost
        self.RULE_MAXIMIZE_FUTURE_MULTIATTACK = rule != Rule.Frost
        #rank secondary targets' priority using focus rules
        self.RULE_RANK_SECONDARY_TARGETS = rule != Rule.Frost

    def _explain(
        self,
        phase: str,
        title: str,
        detail: str,
        locations: list[int] | set[int] | frozenset[int] = (),
        focus: int | None = None,
    ) -> None:
        """Record a step of the AI's decision-making process for the UI."""
        self.explanation.append(
            {
                'phase': phase,
                'title': title,
                'detail': detail,
                'focus': focus,
                'locations': sorted(set(locations)),
            }
        )
    def calculate_monster_move(self) -> list[MonsterMove]:
        self.explanation = []

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

        if not solution:
            self._explain(
                'result',
                'Monster does not move',
                'No character can be attacked by the monster this turn (it may be stunned, '
                'have no valid movement, or every character is out of reach and out of sight), '
                'so the monster stays in place and takes no action.',
                [self.map.get_active_monster_location()],
            )
            return [(self.map.get_active_monster_location(), -1, [], [], [], set())]

        return solution

    def solve(
        self,
        travel_distances: list[int],
        focus_ranks: dict[int, int],
        trap_counts: list[int],
        proximity_distances: list[int],
    ) -> list[list[TargetSelection]]:
        focus_candidates = list(self.map.get_all_location_attackable_char())
        self._explain(
            'focus',
            'Find focus \u2013 list attackable characters',
            f'{len({c for c, _ in focus_candidates})} character(s) can be attacked by the monster from at least '
            f'one hex: {sorted({c for c, _ in focus_candidates})}.',
            {c for c, _ in focus_candidates},
        )
        focus_candidates = minima(focus_candidates, lambda char_loc: trap_counts[char_loc[1]])
        self._explain(
            'focus',
            'Find focus \u2013 fewest traps hit',
            'Of those characters, keep only the ones that can be attacked while triggering the '
            f'fewest traps: {sorted({c for c, _ in focus_candidates})}.',
            {c for c, _ in focus_candidates},
        )
        focus_candidates = minima(focus_candidates, lambda char_loc: travel_distances[char_loc[1]])
        self._explain(
            'focus',
            'Find focus \u2013 fewest hexes travelled',
            'Of those, keep only the ones that can be attacked after travelling the fewest hexes: '
            f'{sorted({c for c, _ in focus_candidates})}.',
            {c for c, _ in focus_candidates},
        )
        if self.RULE_PROXIMITY_FOCUS:
            self._explain(
                'focus',
                'Find focus \u2013 closest to the attacker (skipped)',
                'This ruleset ignores proximity when picking a focus, so this tie-breaker is not applied.',
                {c for c, _ in focus_candidates},
            )
        else:
            focus_candidates = minima(focus_candidates, lambda char_loc: proximity_distances[char_loc[0]])
            self._explain(
                'focus',
                'Find focus \u2013 closest to the attacker',
                'Of those, keep only the character(s) physically closest to the attacking monster: '
                f'{sorted({c for c, _ in focus_candidates})}.',
                {c for c, _ in focus_candidates},
            )
        focus_candidates = minima(
            focus_candidates,
            lambda char_loc: self.map.get_character_initiative(char_loc[0]),
        )
        self._explain(
            'focus',
            'Find focus \u2013 lowest initiative',
            'Of those, keep only the character(s) with the lowest initiative: '
            f'{sorted({c for c, _ in focus_candidates})}.',
            {c for c, _ in focus_candidates},
        )
        focuses = dedup([char_loc[0] for char_loc in focus_candidates])
        if not focuses:
            self._explain(
                'focus',
                'No focus found',
                'No character can be attacked by the monster from any reachable hex, so it has no focus.',
                [],
            )
        elif len(focuses) > 1:
            self._explain(
                'focus',
                'Find focus \u2013 tie',
                f'{len(focuses)} characters are tied on every criterion ({sorted(focuses)}), so every one of '
                'them is considered a valid focus (in the physical game, the player would choose).',
                focuses,
            )
        else:
            self._explain(
                'focus',
                'Focus chosen',
                f'The monster\u2019s focus is the character at hex {focuses[0]}.',
                focuses,
            )

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
        self._explain(
            'attack_location',
            'Optimize location to attack focus \u2013 list candidate hexes',
            f'There are {len(attack_locations)} hex(es) from which the monster could attack the '
            f'focus at hex {focus}: {sorted(attack_locations)}.',
            attack_locations,
            focus,
        )
        attack_locations = minima(attack_locations, lambda loc: trap_counts[loc])
        self._explain(
            'attack_location',
            'Optimize location to attack focus \u2013 fewest traps hit',
            f'Of those, keep only the hex(es) reachable while triggering the fewest traps: '
            f'{sorted(attack_locations)}.',
            attack_locations,
            focus,
        )
        attack_locations = minima(
            attack_locations,
            lambda loc: -int(self.map.can_monster_reach(travel_distances, loc)),
        )
        self._explain(
            'attack_location',
            'Optimize location to attack focus \u2013 reachable this turn',
            f'Of those, prefer hex(es) the monster can actually reach this turn (falling back to hexes it '
            f'cannot yet reach only if none can be reached): {sorted(attack_locations)}.',
            attack_locations,
            focus,
        )
        result = minima(
            attack_locations,
            lambda loc: int(self.map.are_location_at_disadvantage(focus, loc)) if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE else 0,
        )
        if self.RULE_PRIORITIZE_FOCUS_DISADVANTAGE:
            self._explain(
                'attack_location',
                'Optimize location to attack focus \u2013 avoid disadvantage',
                f'Of those, prefer hex(es) that do not put the monster at disadvantage, if possible: '
                f'{sorted(result)}.',
                result,
                focus,
            )
        else:
            self._explain(
                'attack_location',
                'Optimize location to attack focus \u2013 avoid disadvantage (skipped)',
                'This ruleset does not prioritize avoiding disadvantage when choosing where to attack from, '
                'so this tie-breaker is not applied.',
                result,
                focus,
            )
        return result

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
        self._explain(
            'group',
            'Find best group \u2013 maximize characters hit',
            'Of all the character combinations attackable from a valid hex, keep only the group(s) that hit '
            f'the most characters at once: {sorted(tuple(sorted(g)) for g, _ in grouped_targets)}.',
            {member for g, _ in grouped_targets for member in g},
            focus,
        )
        grouped_targets = minima(
            grouped_targets,
            lambda tar_locs: min(travel_distances[loc] for loc in tar_locs[1]),
        )
        self._explain(
            'group',
            'Find best group \u2013 least distance travelled',
            'Of those, keep only the group(s) reachable with the least travel: '
            f'{sorted(tuple(sorted(g)) for g, _ in grouped_targets)}.',
            {member for g, _ in grouped_targets for member in g},
            focus,
        )
        if self.RULE_RANK_SECONDARY_TARGETS:
            grouped_targets = minima(
                grouped_targets,
                lambda tar_locs: self.target_count_for_each_focus_rank(focus_ranks, tar_locs[0]),
            )
            self._explain(
                'group',
                'Find best group \u2013 highest ranked secondary targets',
                'Of those, keep only the group(s) that include the highest-priority secondary target(s) '
                f'(ranked the same way the focus was chosen): {sorted(tuple(sorted(g)) for g, _ in grouped_targets)}.',
                {member for g, _ in grouped_targets for member in g},
                focus,
            )
        else:
            self._explain(
                'group',
                'Find best group \u2013 rank secondary targets (skipped)',
                'This ruleset does not rank secondary targets by focus priority, so this tie-breaker is not '
                'applied.',
                {member for g, _ in grouped_targets for member in g},
                focus,
            )

        targets_with_attack_locations = [
            (target_group, location)
            for target_group, locations in grouped_targets
            for location in locations
        ]
        result = minima(
            targets_with_attack_locations,
            lambda tar_loc: sum(
                self.map.are_location_at_disadvantage(target, tar_loc[1])
                for target in tar_loc[0]
            ),
        )
        self._explain(
            'group',
            'Optimize location to attack best group \u2013 minimize disadvantage',
            'Of all the hexes from which the best group can be attacked, keep only the one(s) that minimize '
            f'the number of targets at disadvantage: {sorted({loc for _, loc in result})}.',
            {loc for _, loc in result},
            focus,
        )
        return result
    
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
            self._explain(
                'group',
                'Single target attack',
                'The monster cannot reach an attack hex this turn, and this ruleset does not optimize '
                'movement for a future multi-target attack, so only a single-target attack against the '
                f'focus at hex {focus} is considered.',
                attack_locations_for_focus,
                focus,
            )
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
        self._explain(
            'group',
            'Choose the closest attack hex',
            'Of all the remaining candidate hexes, keep only the one(s) requiring the fewest hexes '
            f'travelled: {sorted({loc for _, loc in targets_with_attack_locations})}.',
            {loc for _, loc in targets_with_attack_locations},
            focus,
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
            self._explain(
                'movement',
                'Monster reaches its destination',
                f'The monster can reach hex {destination} this turn, so it moves there directly.',
                [destination],
            )
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
        result = minima(reachable_locations, lambda location: travel_distances[location])
        self._explain(
            'movement',
            'Get closer',
            f'The monster cannot reach hex {destination} this turn, so instead it moves to the reachable '
            'hex that: minimizes the number of traps triggered on the path to the ideal destination, then '
            'minimizes the remaining distance to that destination, then minimizes the distance travelled '
            f'this turn: {sorted(result)}.',
            result,
        )
        return result

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