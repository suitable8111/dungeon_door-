from enum import Enum, auto
from dataclasses import dataclass, field


class TileType(Enum):
    WALL = auto()
    FLOOR = auto()
    STAIRS_DOWN = auto()
    SHOP = auto()
    DOOR = auto()
    BURNING_DOOR = auto()


@dataclass
class Tile:
    tile_type: TileType
    blocked: bool = True
    block_sight: bool = True
    explored: bool = False
    visible: bool = False

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
