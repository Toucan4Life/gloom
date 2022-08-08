import collections
from solver.rule import Rule
from solver.hexagonal_grid import hexagonal_grid
from solver.monster import Monster
from solver.settings import MAX_VALUE
from solver.utils import apply_offset, get_offset, pin_offset, rotate_offset

class GloomhavenMap(hexagonal_grid):
    figures: list[str] 
    contents: list[str] 
    initiatives: list[int] 
    walls: list[list[bool]]
    #difficult terrain effects the last hex of a jump move
    Does_difficult_Terrain_Affect_Last_Hex_On_Jump:bool
    def __init__(self, width: int, height: int, monster:Monster,figures: list[str],contents: list[str], initiatives: list[int],walls:list[list[bool]],rule:Rule):
        self.monster=monster
        self.figures = figures
        self.contents = contents
        self.initiatives = initiatives
        self.walls=walls
        self.Does_difficult_Terrain_Affect_Last_Hex_On_Jump = rule == Rule.Gloom
        super().__init__(width, height)
        self.prepare_map(self.walls, self.contents)

    def can_end_move_on(self, location: int) -> bool:
        if self.monster.flying:
            return self.contents[location] in [' ', 'T', 'O', 'H', 'D'] and self.figures[location] in [' ', 'A']
        return self.contents[location] in [' ', 'T', 'H', 'D'] and self.figures[location] in [' ', 'A']

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
    
    def process_aoe(self) -> tuple[list[tuple[int, int, int]], list[list[tuple[int, int, int]]]]:
        aoe_pattern_list: list[list[tuple[int, int, int]]] = []
        aoe: list[tuple[int, int, int]] = []

        if self. monster.is_melee_aoe():
            return [get_offset(self.monster.aoe_center(), location, self.monster.aoe_height) for location in range(self.monster.aoe_size) if self.monster.aoe[location]], []

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
                aoe_hexes.sort()
                aoe_pattern_set.add(tuple(aoe_hexes))

        aoe_pattern_list = [    [get_offset(PRECALC_GRID_CENTER, location, PRECALC_GRID_HEIGHT)
                                for location in aoe]
                            for aoe in aoe_pattern_set]

        return aoe, aoe_pattern_list
 