from core.constants import VIEWPORT_TILES_X, VIEWPORT_TILES_Y


class Camera:
    def __init__(self, map_width, map_height):
        self.map_w = map_width
        self.map_h = map_height
        self.x = 0
        self.y = 0

    def center_on(self, px, py):
        self.x = px - VIEWPORT_TILES_X // 2
        self.y = py - VIEWPORT_TILES_Y // 2
        self.x = max(0, min(self.x, self.map_w - VIEWPORT_TILES_X))
        self.y = max(0, min(self.y, self.map_h - VIEWPORT_TILES_Y))
