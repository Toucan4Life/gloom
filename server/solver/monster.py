from dataclasses import dataclass, field
from solver.utils import  get_offset
import sys
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

    def is_susceptible_to_disavantage(self) -> bool:
        return self.action_range != 0 and not self.muddled

    def has_attack(self) -> bool:
        return self.action_target > 0

    def max_potential_non_aoe_targets(self) -> int:
        if (self.is_max_targets()):
            return 999
        return self.attack_range() - (1 if self.is_aoe() else 0)
    
    def extra_target(self) -> int:
        if (self.has_attack()):
            return self.action_target - 1
        return 0
    
    def is_max_targets(self) -> bool:
        return self.action_target == 6

    def is_aoe(self) -> bool:
        return self.has_attack() and True in self.aoe
    
    def aoe_pattern(self) -> list[tuple[int, int, int]]:        
        return [get_offset(self.aoe.index(True), location, self.aoe_height) for location in range(self.aoe_size) if self.aoe[location]]

    def is_melee_aoe(self) -> bool:
        return self.is_aoe() and self.action_range == 0