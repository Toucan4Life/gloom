from dataclasses import dataclass, field


@dataclass
class Monster:
    action_move: int = 0
    action_range: int = 0
    action_target: int = 0
    flying: bool = False
    jumping: bool = False
    muddled: bool = False
    aoe: list[bool] = field(default_factory=[False])

    def attack_range(self) -> int:
        return 1 if self.action_range == 0 or self.action_target == 0 else self.action_range

    def is_susceptible_to_disavantage(self) -> bool:
        return False if self.action_range == 0 or self.action_target == 0 else not self.muddled

    def plus_target(self) -> int:
        return self.action_target - 1

    def plus_target_for_movement(self) -> int:
        return max(0, self.plus_target())
    
    def is_max_targets(self) -> bool:
        return self.action_target == 6

    def is_aoe(self) -> bool:
        return self.action_target > 0 and True in self.aoe

    def is_melee_aoe(self) -> bool:
        return self.is_aoe() and self.action_range == 0
