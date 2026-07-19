import random

from core.constants import VIEWPORT_TILES_X, VIEWPORT_TILES_Y


class Camera:
    def __init__(self, map_width, map_height):
        self.map_w = map_width
        self.map_h = map_height
        self.x = 0
        self.y = 0
        # ── 동적 흔들림(지진) ──────────────────────────────────────────
        self.offset_x = 0.0            # 렌더 합성 시 더해지는 미세 오프셋(px)
        self.offset_y = 0.0
        self._ambient = 0.0            # 상시 미세 진동 강도(px)
        self._quake_ms = 0.0           # 일시적 지진 잔여 시간
        self._quake_dur = 1.0
        self._quake_int = 0.0

    def center_on(self, px, py):
        self.x = px - VIEWPORT_TILES_X // 2
        self.y = py - VIEWPORT_TILES_Y // 2
        self.x = max(0, min(self.x, self.map_w - VIEWPORT_TILES_X))
        self.y = max(0, min(self.y, self.map_h - VIEWPORT_TILES_Y))

    # ── 지진/진동 ──────────────────────────────────────────────────────
    def set_ambient_shake(self, intensity: float):
        """층 진입 시 상시 미세 진동 강도 설정 (0이면 정적)."""
        self._ambient = max(0.0, float(intensity))

    def trigger_earthquake(self, intensity: float, duration_ms: float):
        """일시적 강한 지진 — intensity에서 시작해 duration 동안 감쇠."""
        self._quake_int = max(self._quake_int, float(intensity))
        self._quake_ms = max(self._quake_ms, float(duration_ms))
        self._quake_dur = max(1.0, self._quake_ms)

    def update(self, dt_ms: float):
        """매 프레임 호출 — offset_x/y에 무작위 노이즈를 넣어 화면을 떤다."""
        amp = self._ambient
        if self._quake_ms > 0:
            self._quake_ms = max(0.0, self._quake_ms - dt_ms)
            amp += self._quake_int * (self._quake_ms / self._quake_dur)
        if amp > 0.05:
            self.offset_x = random.uniform(-amp, amp)
            self.offset_y = random.uniform(-amp, amp)
        else:
            self.offset_x = 0.0
            self.offset_y = 0.0
