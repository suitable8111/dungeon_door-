from enum import Enum, auto
from dataclasses import dataclass, field


class TileType(Enum):
    WALL = auto()
    FLOOR = auto()
    STAIRS_DOWN = auto()
    SHOP = auto()
    DOOR = auto()
    BURNING_DOOR = auto()
    CONVEYOR_LEFT = auto()      # 흐르는 바닥 — 좌로 밀림
    CONVEYOR_RIGHT = auto()     # 흐르는 바닥 — 우로 밀림
    # ── 동적 위험(트랩) ──
    SPIKE_TRAP = auto()         # 밟으면 피해
    WEB_TRAP = auto()           # 밟으면 슬로우
    CURSE_TRAP = auto()         # 밟으면 공격력 저하
    BUTTON = auto()             # 압력판 — 보상 + 이동벽 개방
    SHIFT_WALL = auto()         # 실시간으로 열리고 닫히는 벽(팝업 기둥)


# 밟을 때 효과가 발동하는 트랩
TRAP_TYPES = (TileType.SPIKE_TRAP, TileType.WEB_TRAP, TileType.CURSE_TRAP)


@dataclass
class Tile:
    tile_type: TileType
    blocked: bool = True
    block_sight: bool = True
    explored: bool = False
    visible: bool = False
    phase: float = 0.0          # SHIFT_WALL / 주기 가시 위상(0~1) — 파도식 개폐용

    @classmethod
    def wall(cls):
        return cls(TileType.WALL, blocked=True, block_sight=True)

    @classmethod
    def floor(cls):
        return cls(TileType.FLOOR, blocked=False, block_sight=False)

    @classmethod
    def stairs_down(cls):
        return cls(TileType.STAIRS_DOWN, blocked=False, block_sight=False)

    @classmethod
    def shop(cls):
        return cls(TileType.SHOP, blocked=False, block_sight=False)

    @classmethod
    def door(cls):
        return cls(TileType.DOOR, blocked=False, block_sight=True)

    @classmethod
    def burning_door(cls):
        return cls(TileType.BURNING_DOOR, blocked=False, block_sight=True)

    @classmethod
    def conveyor(cls, direction: int):
        """흐르는 바닥. direction: -1=좌, +1=우."""
        tt = TileType.CONVEYOR_LEFT if direction < 0 else TileType.CONVEYOR_RIGHT
        return cls(tt, blocked=False, block_sight=False)

    @classmethod
    def trap(cls, tile_type, phase: float = 0.0):
        """트랩 타일(가시/거미줄/저주) — 통행 가능.
        가시는 phase로 주기적 발동(골목 패턴)."""
        return cls(tile_type, blocked=False, block_sight=False, phase=phase)

    @classmethod
    def button(cls):
        """압력판 — 밟으면 보상 + 이동벽 개방."""
        return cls(TileType.BUTTON, blocked=False, block_sight=False)

    @classmethod
    def shift_wall(cls, phase: int = 0):
        """실시간 팝업 기둥 — 시작은 열림(통행 가능), 주기적으로 닫힘."""
        return cls(TileType.SHIFT_WALL, blocked=False, block_sight=False, phase=phase)


# 컨베이어 타일 → 미는 방향(dx)
CONVEYOR_DIR = {
    TileType.CONVEYOR_LEFT: -1,
    TileType.CONVEYOR_RIGHT: 1,
}
