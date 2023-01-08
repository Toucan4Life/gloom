import collections
from solver.rule import Rule
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
    #difficult terrain effects the last hex of a jump move
    Does_difficult_Terrain_Affect_Last_Hex_On_Jump:bool
    Valid_active_monster_attack_location:list[tuple[int, frozenset[int], frozenset[int], frozenset[int]]]
    Valid_active_monster_attack_target_for_location:dict[int,list[tuple[frozenset[int], frozenset[int], int]]] 
    def __init__(self, width: int, height: int, monster:Monster,figures: list[str],contents: list[str], initiatives: list[int],walls:list[list[bool]],rule:Rule):
        self.monster=monster
        self.figures = figures
        self.contents = contents
        self.initiatives = initiatives
        self.walls=walls
        self.rule = rule
        self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump = rule == Rule.Gloom
        self.Valid_active_monster_attack_location=list()
        self.Valid_active_monster_attack_target_for_location = dict()
        super().__init__(width, height)
        self.prepare_map(self.walls, self.contents)

    def can_end_move_on(self, location: int) -> bool:
        if self.monster.flying:
            return self.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']
        return self.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']
    def can_target(self, location: int) -> bool:
        return self.contents[location] not in ['X','O']

    def can_travel_through(self, location: int) -> bool:
        if self.monster.flying | self.monster.jumping:
            return self.contents[location] in [' ', 'T', 'H', 'D', 'O']
        return self.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] != 'C'    

    def is_trap(self, location: int) -> bool:
        if self.monster.flying:
            return False
        return self.contents[location] in ['T', 'H']

    def get_active_monster(self) -> Monster:
        return self.monster

    def get_active_monster_location(self) -> int:
        return self.figures.index('A')

    def get_characters(self) -> list[int]:
        return  [_ for _, figure in enumerate(self.figures) if figure == 'C']

    def get_character_initiative(self, character:int) -> int:
        return self.initiatives[character]

    def find_path_distances(self, start: int) -> tuple[list[int], list[int]]:

        distances = [MAX_VALUE] * self.map_size
        traps = [MAX_VALUE] * self.map_size

        frontier: collections.deque[int] = collections.deque()
        frontier.append(start)
        distances[start] = 0
        traps[start] = 0

        while len(frontier) != 0:
            current = frontier.popleft()
            distance = distances[current]
            trap = traps[current]
            for edge, neighbor in enumerate(self.neighbors[current]):
                if neighbor == -1:
                    continue
                if not self.can_travel_through(neighbor):
                    continue
                if self.walls[current][edge]:
                    continue
                neighbor_distance = distance + 1 + \
                    int(not self.monster.flying and not self.monster.jumping and self.additional_path_cost(
                        neighbor))
                neighbor_trap = int(not self.monster.jumping) * \
                    trap + int(self.is_trap(neighbor))
                if (neighbor_trap, neighbor_distance) < (traps[neighbor], distances[neighbor]):
                    frontier.append(neighbor)
                    distances[neighbor] = neighbor_distance
                    traps[neighbor] = neighbor_trap

        if self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump and self.monster.jumping:
            for location in range(self.map_size):
                distances[location] += self.additional_path_cost(
                    location)
            distances[start] -= self.additional_path_cost(start)

        return distances, traps

    def find_path_distances_reverse(self, destination: int) -> tuple[list[int], list[int]]:
        # reverse in that we find the path distance to the destination from every location
        # path distance is symetric except for difficult terrain and traps
        # we correct for the asymetry of starting vs ending on difficult terrain
        # we correct for the asymetry of starting vs ending on traps

        distances, traps = self.find_path_distances(
            destination)
        distances = list(distances)
        traps = list(traps)
        if not self.monster.flying:
            if not self.monster.jumping or self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump:
                destination_additional_path_cost = self.additional_path_cost(
                    destination)
                if destination_additional_path_cost > 0:
                    distances = [
                        _ + destination_additional_path_cost if _ != MAX_VALUE else _ for _ in distances]
                for location in range(self.map_size):
                    distances[location] -= self.additional_path_cost(
                        location)

            if self.is_trap(destination):
                traps = [_ + 1 if _ != MAX_VALUE else _ for _ in traps]
            for location in range(self.map_size):
                traps[location] -= int(self.is_trap(location))

        return distances, traps
    
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

    def find_attackable_location_for_focus(self, travel_distances: list[int], characters: list[int], monster:Monster, RULE_VERTEX_LOS: bool):
        return [ (character,location) for character in characters
                        for location in self.find_proximity_distances_within_range(character,monster.attack_range() + monster.aoe_reach()-monster.is_melee_aoe())                      
                        if  travel_distances[location] != MAX_VALUE and
                            self.can_end_move_on(location) and
                            self.test_los_between_locations(character, location, RULE_VERTEX_LOS)]

    def find_attackable_location_for_characters(self, RULE_VERTEX_LOS: bool)-> list[tuple[int, frozenset[int], frozenset[int], frozenset[int]]]:
        if len(self.Valid_active_monster_attack_location)>0:
            return self.Valid_active_monster_attack_location
        char_in_reachdict:dict[int,set[int]] = collections.defaultdict(set)
        aoe_in_reachdict:dict[int,set[frozenset[int]]] = collections.defaultdict(set)
        characters = self.get_characters()
        travel_distances,_ = self.find_path_distances(self.get_active_monster_location())
        if (not self.monster.is_aoe() or self.monster.action_target > 1):
            [char_in_reachdict[location].add(character) for character in characters
                                                for location in self.find_proximity_distances_within_range(character,self.monster.attack_range())
                                                if  travel_distances[location] != MAX_VALUE
                                                    and self.can_end_move_on(location)
                                                    and self.test_los_between_locations(character, location, RULE_VERTEX_LOS)]
        if (not self.monster.is_aoe()):
            return list({(location,frozenset(),frozenset(),frozenset(char_in_reachdict[location])) for location in char_in_reachdict.keys()})        

        if(self.monster.is_melee_aoe()):
            [aoe_in_reachdict[location].add(aoe_pattern) for location,aoe_pattern in self.get_aoe_pattern_list_with_fixed_pattern(characters, self.monster)]

        elif(self.monster.is_aoe()):
            [ aoe_in_reachdict[location].add(aoe_pattern)
                for aoe_pattern in self.get_aoe_pattern_list_for_characters(characters)
                for aoe_hex in aoe_pattern
                if self.can_target(aoe_hex)
                for location in self.find_proximity_distances_within_range(aoe_hex,self.monster.attack_range())]
        
        result = list({self.get_attack_target(location, aoe_pattern,characters,RULE_VERTEX_LOS, char_in_reachdict)
                        for location in aoe_in_reachdict.keys()
                        for aoe_pattern in (aoe_in_reachdict[location])
                        if travel_distances[location] != MAX_VALUE and self.can_end_move_on(location)})
        self.Valid_active_monster_attack_location=result
        return result

    def get_attack_target(self, location:int, aoe_pattern: frozenset[int], characters:list[int],RULE_VERTEX_LOS:bool,char_in_reachdict: collections.defaultdict[int, set[int]]):
        aoe_targets = { target for target in aoe_pattern if target in characters and self.test_los_between_locations(target, location, RULE_VERTEX_LOS)}
        return (location, frozenset(aoe_targets), frozenset(aoe_pattern), frozenset(char_in_reachdict[location]-aoe_targets))

    def get_all_location_attackable_char(self, RULE_VERTEX_LOS:bool)->set[tuple[int, int]]:
        character_location=self.find_attackable_location_for_characters(RULE_VERTEX_LOS)
        return {(y,char_loc[0]) for char_loc in character_location for y in char_loc[1].union(char_loc[3])}
    
    def get_all_attackable_char_by_location(self,RULE_VERTEX_LOS:bool):
        return {(char_loc[0],char_loc[1].union(char_loc[3]))for char_loc in self.find_attackable_location_for_characters(RULE_VERTEX_LOS)}

    def get_all_attackable_char_combination_for_a_location(self, loc: int,RULE_VERTEX_LOS:bool):
        if loc in self.Valid_active_monster_attack_target_for_location:
            return self.Valid_active_monster_attack_target_for_location[loc]

        max_non_aoe_target = self.monster.max_potential_non_aoe_targets()

        p = [(aoe_hexes,
                    frozenset(aoe_targets.union(tup)),
                    location)
                    for location,aoe_targets, aoe_hexes, non_aoe_targets in self.find_attackable_location_for_characters(RULE_VERTEX_LOS)
                    if location == loc
                    for tup in itertools.combinations(non_aoe_targets, min(max_non_aoe_target, len(non_aoe_targets)))]

        self.Valid_active_monster_attack_target_for_location[loc]=p
        
        return p

    def get_all_attackable_char_combination_for_a_location2(self, locations: set[int],RULE_VERTEX_LOS:bool):
        locations_for_groups :dict[frozenset[int],set[int]] = collections.defaultdict(set)

        max_non_aoe_target = self.monster.max_potential_non_aoe_targets()

        [locations_for_groups[frozenset(aoe_targets.union(tup))].add(location)
                    for location,aoe_targets, _, non_aoe_targets in self.find_attackable_location_for_characters(RULE_VERTEX_LOS)
                    if location in locations
                    for tup in itertools.combinations(non_aoe_targets, min(max_non_aoe_target, len(non_aoe_targets)))]
                            
        return locations_for_groups

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
        if self.monster.flying:
            out += ', FLYING'
        elif self.monster.jumping:
            out += ', JUMPING'
        if self.monster.muddled:
            out += ', MUDDLED'
        out += f', DEBUG_TOGGLE = {debug_toggle}'
        if out == '':
            out = 'NO ACTION'
        else:
            out = out[2:]
        print(out)

 