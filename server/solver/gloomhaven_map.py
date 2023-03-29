import collections
from solver.rule import Rule
from typing import Deque
from solver.hexagonal_grid import hexagonal_grid
from solver.monster import Monster
from solver.settings import MAX_VALUE
from solver.utils import apply_offset, get_offset, pin_offset, rotate_offset
from solver.print_map import format_aoe, format_content, format_initiative, format_numerical_label, print_map, format_los, format_axial_coordinate
import itertools

class GloomhavenMap(hexagonal_grid):
    figures: list[str] 
    contents: list[str] 
    initiatives: list[int] 
    walls: list[list[bool]]
    rule: Rule
    Has_Icy_Terrain:bool
    #difficult terrain effects the last hex of a jump move
    Does_difficult_Terrain_Affect_Last_Hex_On_Jump:bool
    Valid_active_monster_attack_location:dict[int,set[tuple[frozenset[int], frozenset[int], frozenset[int]]]]
    Valid_active_monster_attack_target_for_location:dict[int,dict[frozenset[int], list[frozenset[int]]]] 
    def __init__(self, width: int, height: int, monster:Monster,figures: list[str],contents: list[str], initiatives: list[int],walls:list[list[bool]],rule:Rule):
        self.monster=monster
        self.figures = figures
        self.contents = contents
        self.initiatives = initiatives
        self.walls=walls
        self.rule = rule
        self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump = rule == Rule.Gloom
        self.Valid_active_monster_attack_location=dict()
        self.Valid_active_monster_attack_target_for_location = dict()
        self.Has_Icy_Terrain = 'I' in contents
        #LOS is only checked between vertices
        self.RULE_VERTEX_LOS = rule == Rule.Gloom
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
        if self.monster.flying | self.monster.jumping:
            return self.contents[location] in [' ', 'T', 'H', 'D', 'O', 'I']
        return self.contents[location] in [' ', 'T', 'H', 'D', 'I'] and self.figures[location] != 'C'    

    def is_trap(self, location: int) -> bool:
        if self.monster.flying:
            return False
        return self.contents[location] in ['T', 'H']
    
    def is_icy(self, location: int) -> bool:
        if self.monster.flying | self.monster.jumping | self.monster.teleport:
            return False
        return self.contents[location] == 'I'

    def get_active_monster(self) -> Monster:
        return self.monster

    def get_active_monster_location(self) -> int:
        return self.figures.index('A')

    def get_characters(self) -> list[int]:
        return  [_ for _, figure in enumerate(self.figures) if figure == 'C']

    def get_character_initiative(self, character:int) -> int:
        return self.initiatives[character]
    
    def get_traversal_graph(self,start:int, isReversed:bool) -> list[list[tuple[int, tuple[int, int]]]]:
        frontier: collections.deque[int] = collections.deque()
        frontier.append(start)

        scores = list(zip([MAX_VALUE] * self.map_size,[MAX_VALUE] * self.map_size))
        scores[start] = (0,0)

        visited:set[int] = set()

        best_parents:list[list[tuple[int,tuple[int,int]]]] =  [[] for _ in range(self.map_size)]

        while len(frontier) != 0:
            current = frontier.popleft()
            for neighbor, score in self.find_neighbors_and_movement_cost(current):                
                best_parents[neighbor].append((current,score)) if isReversed else best_parents[current].append((neighbor,score))                 
                if(neighbor not in visited and neighbor not in frontier):
                    frontier.append(neighbor)
            visited.add(current)
        return best_parents
    
    def find_active_monster_traversal_cost(self, start: int) -> tuple[list[int], list[int]]:
        best_parents = self.get_traversal_graph(start,False)
        frontier: collections.deque[int] = collections.deque()
        frontier.append(start)
        scores = list(zip([MAX_VALUE] * self.map_size,[MAX_VALUE] * self.map_size))
        scores[start] = (0,0)

        while len(frontier) != 0:
            current = frontier.popleft()            
            for neighbor, score in best_parents[current]:
                total_score = self.add_score(scores[current], current, score)
                if total_score < scores[neighbor]:
                    frontier.append(neighbor)
                    scores[neighbor] = total_score
        return [x[1] for x in scores], [x[0] for x in scores]

    def find_neighbors_and_movement_cost(self, location :int):
        neighbor_cost:list[tuple[int,tuple[int,int]]]=[]
        for edge, neighbor in enumerate(self.neighbors[location]):
            if neighbor == -1 or not self.can_travel_through(neighbor) or self.walls[location][edge]:
                continue
            slide = False
            while self.is_icy(neighbor):
                slide = True
                next_neighbor = self.neighbors[neighbor][edge]
                if next_neighbor == -1 or not self.can_travel_through(next_neighbor) or self.figures[next_neighbor] == 'M' or self.walls[neighbor][edge]:
                    break
                neighbor = next_neighbor

            neighbor_distance = 1 if self.monster.flying or (self.monster.jumping and not self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump) or self.monster.teleport or slide else self.additional_path_cost( neighbor ) + 1
            neighbor_cost.append((neighbor,(int(self.is_trap(neighbor)),neighbor_distance)))
        return neighbor_cost
    
    def add_score(self, previous_score:tuple[int,int], current:int, score:tuple[int,int]):

        return ((0 if self.monster.jumping or self.monster.teleport else previous_score[0]) + score[0],
                (-1 if self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump and
                    self.monster.jumping and
                    not self.monster.teleport and
                    self.additional_path_cost(current) else 0) + previous_score[1] + score[1])
    
    def find_path_distances_to_destination( self, destination:int):
        start = self.get_active_monster_location()
        best_parents = self.get_traversal_graph(start, True)
        frontier: collections.deque[int] = collections.deque()
        frontier.append(destination)
        scores = list(zip([MAX_VALUE] * self.map_size,[MAX_VALUE] * self.map_size))
        scores[destination] = (0,0)
        while len(frontier) != 0:
            current = frontier.popleft()            
            for neighbor, score in best_parents[current]:
                total_score = self.add_score(score, current, scores[current])
                if total_score < scores[neighbor]:
                    frontier.append(neighbor)
                    scores[neighbor] = total_score
        return [x[1] for x in scores], [x[0] for x in scores]
 
    def process_aoe(self) -> list[list[tuple[int, int, int]]]:
        aoe: list[tuple[int, int, int]] = []

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
                aoe_pattern_set.add(tuple(aoe_hexes))

        return [[get_offset(PRECALC_GRID_CENTER, location, PRECALC_GRID_HEIGHT)
                                for location in aoe]
                            for aoe in aoe_pattern_set]

    def get_aoe_pattern_list_for_characters(self, characters:list[int])->set[frozenset[int]]:
                                        
        new_var = [[location_offset for aoe_offset in aoe_pattern_list if (location_offset:=self.apply_aoe_offset(character, aoe_offset))!=-1]
                                        for aoe_pattern_list in self.process_aoe()
                                        for character in characters]
                             
        return {frozenset(y) for y in new_var }

    def get_aoe_pattern_list_with_fixed_pattern(self, characters:list[int], monster:Monster)->list[tuple[int, frozenset[int]]]:

        self.monster.aoe[24]=True#center of aoe for fixed pattern
        index_of_center=sum(monster.aoe[:24])
                                        
        aoe_pattern_list = [[location_offset for aoe_offset in aoe_pattern_list if (location_offset:=self.apply_aoe_offset(character, aoe_offset))!=-1]
                                        for aoe_pattern_list in self.process_aoe()
                                        for character in characters]
        return [(aoe_pattern[index_of_center],frozenset(set(aoe_pattern)-{aoe_pattern[index_of_center]}) ) for aoe_pattern in aoe_pattern_list]

    def find_attackable_location_for_characters(self)-> dict[int,set[tuple[frozenset[int], frozenset[int], frozenset[int]]]]:
        if len(self.Valid_active_monster_attack_location)>0:
            return self.Valid_active_monster_attack_location
        char_in_reachdict:dict[int,set[int]] = collections.defaultdict(set)
        aoe_in_reachdict:dict[int,set[frozenset[int]]] = collections.defaultdict(set)
        result:dict[int,set[tuple[frozenset[int], frozenset[int], frozenset[int]]]]= collections.defaultdict(set)
        characters = self.get_characters()
        travel_distances,_, = self.find_active_monster_traversal_cost(self.get_active_monster_location())
        if (not self.monster.is_aoe() or self.monster.action_target > 1):
            [char_in_reachdict[location].add(character) for character in characters
                                                for location in self.find_proximity_distances_within_range(character,self.monster.attack_range())
                                                if  travel_distances[location] != MAX_VALUE
                                                    and self.can_end_move_on(location)
                                                    and self.test_los_between_locations(character, location, self.RULE_VERTEX_LOS)]
        if (not self.monster.is_aoe()):
            [result[location].add((frozenset(),frozenset(),frozenset(char_in_reachdict[location]))) for location in char_in_reachdict.keys()]
            return result

        if(self.monster.is_melee_aoe()):
            [aoe_in_reachdict[location].add(aoe_pattern) for location,aoe_pattern in self.get_aoe_pattern_list_with_fixed_pattern(characters, self.monster)]

        elif(self.monster.is_aoe()):
            [ aoe_in_reachdict[location].add(aoe_pattern)
                for aoe_pattern in self.get_aoe_pattern_list_for_characters(characters)
                for aoe_hex in aoe_pattern
                if self.can_target(aoe_hex)
                for location in self.find_proximity_distances_within_range(aoe_hex,self.monster.attack_range())]
        
        [result[location].add(self.get_attack_target(location, aoe_pattern,characters, char_in_reachdict))
                        for location in aoe_in_reachdict.keys()
                        for aoe_pattern in (aoe_in_reachdict[location])
                        if travel_distances[location] != MAX_VALUE and self.can_end_move_on(location)]
        self.Valid_active_monster_attack_location=result
        return result

    def get_attack_target(self, location:int, aoe_pattern: frozenset[int], characters:list[int],char_in_reachdict: collections.defaultdict[int, set[int]]):
        aoe_targets = { target for target in aoe_pattern if target in characters and self.test_los_between_locations(target, location, self.RULE_VERTEX_LOS)}
        return (frozenset(aoe_targets), frozenset(aoe_pattern), frozenset(char_in_reachdict[location]-aoe_targets))

    def get_all_location_attackable_char(self)->set[tuple[int, int]]:
        return {(y,key) for key,char_locs in self.find_attackable_location_for_characters().items() for char_loc in char_locs for y in char_loc[0].union(char_loc[2])}
    
    def get_locations_hitting(self, location:int):
        return {key for key,char_locs in self.find_attackable_location_for_characters().items() for char_loc in char_locs  if location in char_loc[0].union(char_loc[2])}
    
    def get_all_attackable_char_combination_for_a_location(self, loc:int):
        if loc in self.Valid_active_monster_attack_target_for_location:
            return self.Valid_active_monster_attack_target_for_location[loc]
        
        x:dict[frozenset[int],list[frozenset[int]]] = collections.defaultdict(list)

        max_non_aoe_target = self.monster.max_potential_non_aoe_targets()

        [x[frozenset(aoe_targets.union(tup))].append(aoe_hexes)
                    for aoe_targets, aoe_hexes, non_aoe_targets in self.find_attackable_location_for_characters()[loc]
                    for tup in itertools.combinations(non_aoe_targets, min(max_non_aoe_target, len(non_aoe_targets)))]
        
        self.Valid_active_monster_attack_target_for_location[loc]=x
        return x
    
    def get_all_attackable_char_combination(self, locations: list[int]):
        locations_for_groups :dict[frozenset[int],set[int]] = collections.defaultdict(set)

        [locations_for_groups[group].add(loc)
          for loc in locations
          for group in self.get_all_attackable_char_combination_for_a_location(loc).keys()]

        return locations_for_groups

    def are_location_at_disadvantage(self, locationA:int, locationB:int)-> bool:
        return self.monster.is_susceptible_to_disavantage() and self.is_adjacent(locationB, locationA)

    def can_monster_reach(self, travel_distances:list[int], dest:int):
        return travel_distances[dest] <= self.monster.action_move

    def does_monster_attack(self):
        return self.monster.has_attack()
    
    def find_shortest_sightline(self, location_a: int, location_b: int) -> tuple[tuple[float, float], tuple[float, float]]:
        return super().find_shortest_sightline(location_a,location_b,self.RULE_VERTEX_LOS)
    
    def solve_sight(self, monster: int,upper_bound:int) -> list[tuple[int, int]]:
        return super().solve_sight(monster,upper_bound, self.RULE_VERTEX_LOS)

    def print(self):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_numerical_label( _ ) for _ in range( self.map_size ) ] )

    def print_initiative_map(self):
        print_map(self.map_width, self.map_height, self.effective_walls, [ format_content( *_ ) for _ in zip( self.figures, self.contents ) ], [ format_initiative( _ ) for _ in self.initiatives ] )
    
    def print_custom_map(self, top_label:list[int]=[], bottom_label:list[int]=[]):
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
                [ format_axial_coordinate( self.to_axial_coordinate(_,7,7 ) ) for _ in range( self.map_size ) ] )

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
            out += f', AOE REACH {self.monster.aoe_reach()}'
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

 