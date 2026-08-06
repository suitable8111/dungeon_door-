"""원격 플레이어 — 다른 접속자를 이 클라 화면에 렌더하기 위한 경량 엔티티.

로컬 Player와 달리 게임 로직(전투/스탯/인벤토리)이 없다. 호스트 스냅샷으로 받은
상태(타일 좌표·방향·외형)만 들고, 화면에서는 타일 사이를 부드럽게 보간해 그린다.
직렬화/세이브 대상 아님 — 순수 런타임 뷰.
"""

from __future__ import annotations

from core.constants import TILE_SIZE


class RemotePlayer:
    def __init__(self, pid: int):
        self.pid = pid
        # 권위(목표) 타일 좌표
        self.x = 0
        self.y = 0
        # 렌더 좌표(픽셀) — 목표 타일을 향해 보간되는 값
        self.render_px = 0.0
        self.render_py = 0.0
        self.facing = "down"
        self.walk_frame = 0
        self.char_class = "warrior"
        self.char_name = "Hero"
        self.appearance: dict = {}
        self.hp = 30
        self.max_hp = 30
        self.floor = 0
        self._initialized = False

    # ── 상태 수신 ────────────────────────────────────────────────────
    def apply_state(self, st: dict) -> None:
        """스냅샷의 player_state dict를 반영."""
        self.x = st.get("x", self.x)
        self.y = st.get("y", self.y)
        self.facing = st.get("f", self.facing)
        self.walk_frame = st.get("w", self.walk_frame)
        self.char_class = st.get("c", self.char_class)
        self.char_name = st.get("n", self.char_name)
        self.appearance = st.get("a", self.appearance) or {}
        self.hp = st.get("hp", self.hp)
        self.max_hp = st.get("mhp", self.max_hp)
        self.floor = st.get("fl", self.floor)
        if not self._initialized:
            # 첫 상태 수신: 보간 없이 즉시 스냅
            self.render_px = self.x * TILE_SIZE
            self.render_py = self.y * TILE_SIZE
            self._initialized = True

    # ── 보간 ────────────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        """렌더 픽셀 좌표를 목표 타일로 부드럽게 이동 (지수 감쇠 lerp)."""
        tx = self.x * TILE_SIZE
        ty = self.y * TILE_SIZE
        # dt 기반 감쇠 계수 (프레임률 독립). 16ms 기준 약 0.28/프레임.
        factor = 1.0 - pow(0.0002, dt / 1000.0)
        factor = max(0.0, min(1.0, factor))
        self.render_px += (tx - self.render_px) * factor
        self.render_py += (ty - self.render_py) * factor
        if abs(tx - self.render_px) < 0.5:
            self.render_px = tx
        if abs(ty - self.render_py) < 0.5:
            self.render_py = ty

    # ── 렌더 ────────────────────────────────────────────────────────
    def draw(self, surf, cx: int, cy: int) -> None:
        """카메라 (cx,cy) 타일 오프셋 기준으로 원격 플레이어를 그린다.

        로컬 히어로와 동일한 draw_avatar_tile 경로를 사용해 외형을 일치시킨다.
        """
        from entities.avatar import draw_avatar_tile
        sx = int(round(self.render_px - cx * TILE_SIZE))
        sy = int(round(self.render_py - cy * TILE_SIZE))
        draw_avatar_tile(surf, sx, sy, self.facing, self.walk_frame, 0,
                         self.appearance, self.char_class)
        # 클라 이름표 (원격 플레이어 식별)
        self._draw_nameplate(surf, sx, sy)

    def _draw_nameplate(self, surf, sx: int, sy: int) -> None:
        try:
            from core.animator import _load_font
        except Exception:
            return
        if not getattr(RemotePlayer, "_font", None):
            RemotePlayer._font = _load_font(12)
        label = RemotePlayer._font.render(self.char_name, True, (235, 235, 245))
        lx = sx + (TILE_SIZE - label.get_width()) // 2
        surf.blit(label, (lx, sy - 12))
