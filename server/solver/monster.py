from dataclasses import dataclass, field
import sys
import itertools
@dataclass
class Monster:
    aoe_width = 7
    aoe_height = 7
    aoe_size = aoe_width * aoe_height
    action_move: int = 0
    action_range: int = 0
    action_target: int = 1
    flying: bool = False
    jumping: bool = False
    muddled: bool = False
    aoe: list[bool] = field(default_factory=lambda: [False]*49)
    teleport : bool = False
    
    def aoe_center(self) -> int:
        center = (self.aoe_size - 1) // 2

        if int(center) - center != 0:
            sys.exit('aoe has no center')

        return center

    def attack_range(self) -> int:
        return 1 if self.action_range == 0 or self.action_target == 0 else self.action_range

    def aoe_reach(self) -> int:
        aoe_tile = [self.to_axial_coordinate(i,self.aoe_height,self.aoe_width) for i,t in enumerate(self.aoe) if t is True]
        if not self.is_aoe():
            return 0
        if self.is_melee_aoe():
            monster_location = self.to_axial_coordinate(24,self.aoe_height,self.aoe_width)
            dist = [self.axial_distance(monster_location,tup) for tup in aoe_tile]
        else :
            dist = [self.axial_distance(tup[0],tup[1]) for tup in itertools.combinations(aoe_tile, 2)]
            #print(dist)
        return max(dist)

    def axial_distance(self,a:tuple[int,int],b:tuple[int,int]) -> int:
        return (abs(a[0] - b[0]) + abs(a[0] + a[1] - b[0] - b[1]) + abs(a[1] - b[1])) // 2

    def is_susceptible_to_disavantage(self) -> bool:
        return self.action_range != 0 and self.action_target != 0 and not self.muddled

    def has_attack(self) -> bool:
        return self.action_target > 0

    def max_potential_non_aoe_targets(self) -> int:
        if (self.is_max_targets()):
            return 999
        return self.action_target - 1 if self.is_aoe() else max(1, self.action_target)
    
    def extra_target(self) -> int:
        if (self.has_attack()):
            return self.action_target - 1 
        return 0
    
    def is_max_targets(self) -> bool:
        return self.action_target == 6

    def is_aoe(self) -> bool:
        return self.has_attack() and True in self.aoe

    def is_melee_aoe(self) -> bool:
        return self.is_aoe() and self.action_range == 0

    def to_axial_coordinate(self, location:int, height:int, width:int) -> tuple[int,int]:
        column = location % height
        row = location // height
        return (column - row // 2, row)
        
    def from_axial_coordinate(self, coordinate:tuple[int,int], height:int, width:int)->int:
       
        column = coordinate[1]
        if not (0 <= column < width):
            return -1
        row = coordinate[0]
        if not (0 - column // 2 <= row < height - column // 2):
            return -1
        return row + column // 2 + column * height
