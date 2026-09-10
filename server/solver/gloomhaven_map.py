"""Gloomhaven-specific traversal, targeting, and display helpers."""

# pylint: disable=line-too-long, trailing-whitespace, missing-function-docstring, missing-class-docstring, invalid-name, consider-using-dict-items, superfluous-parens

import collections
from collections.abc import Iterable
from itertools import combinations
from typing import cast

from solver.hexagonal_grid import hexagonal_grid
from solver.monster import Monster
from solver.print_map import format_aoe, format_axial_coordinate, format_content, format_initiative, format_los, format_numerical_label, print_map
from solver.rule import Rule
from solver.settings import MAX_VALUE
from solver.utils import dijkstra_algorithm, invert_key_values

AttackPattern = frozenset[int]
AttackPatternGroup = frozenset[AttackPattern]
VisibleCharacterPatterns = dict[frozenset[int], AttackPatternGroup]
AttackPatternMap = dict[int, VisibleCharacterPatterns]
SecondaryAttackMap = collections.defaultdict[int, set[int]]
AttackCombination = tuple[frozenset[int], AttackPatternGroup, frozenset[int]]
EMPTY_ATTACK_PATTERN_GROUP = cast(AttackPatternGroup, frozenset())

class GloomhavenMap(hexagonal_grid):
    """Map rules and helpers for Gloomhaven-family monster solving."""

    figures: list[str] 
    contents: list[str] 
    initiatives: list[int] 
    walls: list[list[bool]]
    rule: Rule
    Has_Icy_Terrain:bool
    Does_difficult_Terrain_Affect_Last_Hex_On_Jump:bool
    def __init__(self, width: int, height: int, monster:Monster,figures: list[str],contents: list[str], initiatives: list[int],walls:list[list[bool]],rule:Rule):
        self.monster=monster
        self.figures = figures
        self.contents = contents
        self.initiatives = initiatives
        self.walls=walls
        self.rule = rule
        self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump = rule == Rule.Gloom
        self.Has_Icy_Terrain = 'I' in contents
        self.RULE_VERTEX_LOS = rule == Rule.Gloom
        self._traversal_cost_cache: dict[int, tuple[list[int], list[int]]] = {}
        self._main_attack_char_cache: AttackPatternMap | None = None
        self._secondary_attack_char_cache: SecondaryAttackMap | None = None
        self._attackable_char_combination_cache: dict[int, dict[frozenset[int], set[AttackCombination]]] = {}
        super().__init__(width, height)
        self.prepare_map(self.walls, self.contents)

    def can_end_move_on(self, location: int) -> bool:
        if self.monster.flying:
            return self.contents[location] in [' ', 'T', 'O', 'H', 'D', 'I'] and self.figures[location] in [' ', 'A']
        return self.contents[location] in [' ', 'T', 'H', 'D', 'I'] and self.figures[location] in [' ', 'A']
    
    def can_target(self, location: int) -> bool:
        return self.contents[location] not in ['X','O']

    def can_travel_through(self, location: int) -> bool:
        if self.monster.teleport:
            return self.contents[location] in [ ' ', 'X', 'T', 'H', 'D', 'O', 'I' ]
        if self.monster.flying or self.monster.jumping:
            return self.contents[location] in [' ', 'T', 'H', 'D', 'O', 'I']
        return self.contents[location] in [' ', 'T', 'H', 'D', 'I'] and self.figures[location] != 'C'    

    def is_damaging_location(self, location: int) -> bool:
        if self.monster.flying:
            return False
        return self.contents[location] in ['T', 'H']
    
    def is_icy(self, location: int) -> bool:
        return self.contents[location] == 'I'

    def is_difficult_terrain(self, location: int) -> int:
        return int(self.contents[location] == 'D')
    
    def get_active_monster(self) -> Monster:
        return self.monster

    def get_active_monster_location(self) -> int:
        return self.figures.index('A')

    def get_characters(self) -> list[int]:
        return  [_ for _, figure in enumerate(self.figures) if figure == 'C']

    def get_character_initiative(self, character:int) -> int:
        return self.initiatives[character]
    
    def get_traversal_graph(self, isReversed:bool) -> list[list[tuple[int, tuple[int, int]]]]:
        if isReversed:
            best_parents:list[list[tuple[int,tuple[int,int]]]] = [[] for _ in range(self.map_size)]
            for current in range(self.map_size):
                for neighbor, score in self.find_neighbors_and_movement_cost(current):                
                    best_parents[neighbor].append((current,score)) 
            return best_parents 
        
        return [self.find_neighbors_and_movement_cost(current) for current in range(self.map_size)]
    
    def find_active_monster_traversal_cost(self,destination :int =-1) -> tuple[list[int], list[int]]:
        if destination in self._traversal_cost_cache:
            return self._traversal_cost_cache[destination]

        start = self.get_active_monster_location() if destination ==-1 else destination          
        scores = dijkstra_algorithm(start, self.get_traversal_graph(destination!=-1))              
        cached_costs = (
            [x[1] + (1 if self.is_difficult_terrain(i) and self.monster.jumping and self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump  else 0) for i,x in enumerate(scores)],
            [x[0] + (1 if self.is_damaging_location(i) and (self.monster.jumping or self.monster.teleport) else 0) for i,x in enumerate(scores)],
        )
        self._traversal_cost_cache[destination] = cached_costs
        return cached_costs

    def slide_destination(self, neighbor: int, edge: int) -> tuple[int, bool]:
        slide = False
        if self.monster.flying or self.monster.jumping or self.monster.teleport:
            return neighbor, slide

        while self.is_icy(neighbor):
            slide = True
            next_neighbor = self.neighbors[neighbor][edge]
            if next_neighbor == -1 or not self.can_travel_through(next_neighbor) or self.figures[next_neighbor] == 'M' or self.walls[neighbor][edge]:
                break
            neighbor = next_neighbor

        return neighbor, slide

    def movement_cost_for_neighbor(self, neighbor: int, slide: bool) -> tuple[int, int]:
        neighbor_distance = 1 if not self.is_difficult_terrain(neighbor) or self.monster.flying or self.monster.teleport or slide or self.monster.jumping else 2
        return (0 if self.monster.jumping or self.monster.teleport or not self.is_damaging_location(neighbor) else 1, neighbor_distance)

    def find_neighbors_and_movement_cost(self, location :int):
        neighbor_cost:list[tuple[int,tuple[int,int]]]=[]
        for edge, neighbor in enumerate(self.neighbors[location]):
            if neighbor == -1 or not self.can_travel_through(neighbor) or (self.walls[location][edge]):
                continue

            neighbor, slide = self.slide_destination(neighbor, edge)
            neighbor_cost.append((neighbor, self.movement_cost_for_neighbor(neighbor, slide)))
        return neighbor_cost
 
    def get_aoe_pattern_list_with_fixed_pattern(self, characters:list[int], monster:Monster) -> dict[int, set[AttackPattern]]:
        aoe_with_center = list(monster.aoe)
        center_index = monster.aoe_center()
        aoe_with_center[center_index] = True
        index_of_center = sum(aoe_with_center[:center_index])
        aoe_in_reachdict: dict[int, set[AttackPattern]] = collections.defaultdict(set)
        for aoe_pattern in self.get_all_patterns_hitting_hexes(characters, monster.aoe_pattern(aoe_with_center)):
            center_location = aoe_pattern[index_of_center]
            aoe_in_reachdict[center_location].add(frozenset(set(aoe_pattern) - {center_location}))
        return aoe_in_reachdict
    
    def get_main_attack_char(self) -> AttackPatternMap:
        if self._main_attack_char_cache is not None:
            return self._main_attack_char_cache

        characters = self.get_characters()
        travel_distances, _ = self.find_active_monster_traversal_cost()
        aoe_in_reachdict: dict[int, set[AttackPattern]] = collections.defaultdict(set)
        if not self.monster.is_aoe():
            self._main_attack_char_cache = {
                location: {
                    frozenset({char}): EMPTY_ATTACK_PATTERN_GROUP
                    for char in chars
                }
                for location, chars in self.get_secondary_attack_char().items()
            }
            return self._main_attack_char_cache
        if self.monster.is_melee_aoe():
            aoe_in_reachdict = self.get_aoe_pattern_list_with_fixed_pattern(characters, self.monster)
        elif self.monster.is_aoe():
            aoe_patterns = [frozenset(pattern) for pattern in self.get_all_patterns_hitting_hexes(characters, self.monster.aoe_pattern())]
            aoe_in_reachdict = dict(
                invert_key_values(
                    aoe_patterns,
                    lambda aoe_pattern: [
                        location
                        for aoe_hex in aoe_pattern
                        if self.can_target(aoe_hex)
                        for location in self.find_locations_within_range(aoe_hex, self.monster.attack_range())
                        if self.test_los_between_locations(aoe_hex, location, self.RULE_VERTEX_LOS)
                    ],
                )
            )

        self._main_attack_char_cache = {
            location: self.retrieve_char_for_aoe_patterns(aoe_in_reachdict[location], characters, location)
            for location in aoe_in_reachdict.keys()
            if travel_distances[location] != MAX_VALUE and self.can_end_move_on(location)
        }
        return self._main_attack_char_cache

    def retrieve_char_for_aoe_patterns(
        self,
        aoe_patterns: Iterable[AttackPattern],
        characters: list[int],
        location: int,
    ) -> VisibleCharacterPatterns:
        aoe_in_reachdict: collections.defaultdict[frozenset[int], set[AttackPattern]] = collections.defaultdict(set)
        for aoe_hex_pattern in aoe_patterns:
            visible_characters = frozenset(
                char
                for char in aoe_hex_pattern.intersection(characters)
                if self.test_los_between_locations(char, location, self.RULE_VERTEX_LOS)
            )
            aoe_in_reachdict[visible_characters].add(aoe_hex_pattern)
        return {
            visible_characters: frozenset(patterns)
            for visible_characters, patterns in aoe_in_reachdict.items()
        }
    
    def get_secondary_attack_char(self) -> SecondaryAttackMap:
        if self._secondary_attack_char_cache is not None:
            return self._secondary_attack_char_cache

        characters = self.get_characters()
        travel_distances, _ = self.find_active_monster_traversal_cost()

        secondary_attacks: SecondaryAttackMap = collections.defaultdict(set)
        secondary_attacks.update(
            dict(
                invert_key_values(
                    characters,
                    lambda character: [
                        location
                        for location in self.find_locations_within_range(character, self.monster.attack_range())
                        if travel_distances[location] != MAX_VALUE
                        and self.can_end_move_on(location)
                        and self.test_los_between_locations(character, location, self.RULE_VERTEX_LOS)
                    ],
                )
            )
        )
        self._secondary_attack_char_cache = secondary_attacks
        return self._secondary_attack_char_cache

    def get_all_location_attackable_char(self)->set[tuple[int, int]]:
        return {(c,loc) for loc, charset in self.get_main_attack_char().items() for char in charset.keys() for c in char}
    
    def get_all_attackable_char_combination_for_a_location(self, loc:int) -> dict[frozenset[int], set[AttackCombination]]:
        if loc in self._attackable_char_combination_cache:
            return self._attackable_char_combination_cache[loc]

        secondary_attack: set[int]
        if self.monster.extra_target() > 0:
            secondary_attack = self.get_secondary_attack_char()[loc]
        else:
            secondary_attack = set()

        attack_patterns: list[AttackCombination] = [
            (chars, pattern, frozenset(secondary_attack))
            for chars, pattern in self.get_main_attack_char()[loc].items()
        ]
        attackable_combinations = dict(
            invert_key_values(
                attack_patterns,
                lambda attack_pattern: [
                    frozenset(set(combination).union(attack_pattern[0]))
                    for combination in combinations(secondary_attack, min(self.monster.extra_target(), len(secondary_attack)))
                ],
            )
        )
        self._attackable_char_combination_cache[loc] = attackable_combinations
        return attackable_combinations
    
    def are_location_at_disadvantage(self, locationA:int, locationB:int)-> bool:
        return self.monster.is_susceptible_to_disavantage() and self.is_adjacent(locationB, locationA)

    def can_monster_reach(self, travel_distances:list[int], dest:int):
        return travel_distances[dest] <= self.monster.action_move

    def does_monster_attack(self):
        return self.monster.has_attack()
    
    def find_shortest_sightline(self, location_a: int, location_b: int, rule_vertex_los: bool | None = None) -> tuple[tuple[float, float], tuple[float, float]]:
        return super().find_shortest_sightline(location_a, location_b, self.RULE_VERTEX_LOS if rule_vertex_los is None else rule_vertex_los)
    
    def solve_sight(self, monster: int,upper_bound:int, rule_vertex_los: bool | None = None) -> list[tuple[int, int]]:
        return super().solve_sight(monster, upper_bound, self.RULE_VERTEX_LOS if rule_vertex_los is None else rule_vertex_los)

    def print(self):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in range( self.map_size ) ] )

    def print_initiative_map(self):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ] )
    
    def print_custom_map(self, top_label: list[int] | None = None, bottom_label: list[int] | None = None):
        print_map(self.map_width,
                self.map_height,
                self.effective_walls,
                [ format_numerical_label( _ ) for _ in top_label ] if top_label else [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ],
                [ format_numerical_label( _ ) for _ in bottom_label ] if bottom_label else [ format_numerical_label( _ ) for _ in range( self.map_size ) ]  )

    def print_axial_map(self):
        print_map(self.map_width,
                self.map_height,
                self.effective_walls,
                [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ],
                [ format_axial_coordinate( self.to_axial_coordinate(_, self.map_height ) ) for _ in range( self.map_size ) ] )

    def print_los_map(self, visible_locations:list[bool]):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_los(_) for _ in visible_locations])
    
    def print_solution_map(self, debug_tag:list[str]):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ], debug_tag )
    
    def print_aoe_map(self):
        false_contents = ['   '] * self.monster.aoe_size
        if self.monster.is_melee_aoe():
            false_contents[self.monster.aoe_center()] = ' A '
        print_map(self.monster.aoe_width, self.monster.aoe_height, [ [ False ] * 6 ] * self.monster.aoe_size, false_contents, [ format_aoe( _ ) for _ in self.monster.aoe ] )

    def print_summary(self, debug_toggle:bool):
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
        if self.monster.max_potential_non_aoe_targets() > 1:
            if self.monster.is_max_targets():
                out += ', TARGET ALL'
            else:
                out += f',NON AOE TARGETS {self.monster.max_potential_non_aoe_targets()}'
        if self.monster.teleport:
            out += ', TELEPORT'               
        if self.monster.flying:
            out += ', FLYING'
        if self.monster.jumping:
            out += ', JUMPING'
        if self.monster.muddled:
            out += ', MUDDLED'
        out += f', DEBUG_TOGGLE = {debug_toggle}'
        if out == '':
            out = 'NO ACTION'
        else:
            out = out[2:]
        print(out)
