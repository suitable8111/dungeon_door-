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
        self.atk_ms = 0.0          # >0이면 공격 포즈로 렌더 (이펙트 공유)
        self.atk_facing = "down"
        self.char_class = "warrior"
        self.char_name = "Hero"
        self.appearance: dict = {}
        self.hp = 30
        self.max_hp = 30
        self.floor = 0
        self.defense = 0
        self.evasion = 0
        self.status = 0            # 0 정상 / 1 다운 / 2 관전 (co-op 부활)
        self.revive_prog = 0.0     # 이 원격 파티원을 내가 부활 중인 진행도 [0,1]
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
        self.defense = st.get("de", self.defense)
        self.evasion = st.get("ev", self.evasion)
        new_status = st.get("st", self.status)
        if new_status != 1:        # 다운 해제/관전 전환 시 부활 진행도 리셋
            self.revive_prog = 0.0
        self.status = new_status
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
        if self.atk_ms > 0:
            self.atk_ms = max(0.0, self.atk_ms - dt)
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
        if self.status != 0:
            # 다운/관전: 쓰러진 아바타 + 상태 표식 (부활 대상 강조)
            self._draw_fallen(surf, sx, sy)
            self._draw_nameplate(surf, sx, sy)
            return
        # 공격 중이면 공격 포즈(phase 2) + 공격 방향으로 렌더
        atk = self.atk_ms > 0
        face = self.atk_facing if atk else self.facing
        phase = 2 if atk else 0
        draw_avatar_tile(surf, sx, sy, face, self.walk_frame, phase,
                         self.appearance, self.char_class)
        # 클라 이름표 (원격 플레이어 식별)
        self._draw_nameplate(surf, sx, sy)

    def _draw_fallen(self, surf, sx: int, sy: int) -> None:
        """다운/관전 상태 렌더 — 반투명 쓰러진 아바타 + 부활 링."""
        import pygame
        from entities.avatar import draw_avatar_tile
        tmp = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        draw_avatar_tile(tmp, 0, 0, 'down', 0, 0, self.appearance,
                         self.char_class)
        # 90° 회전으로 '쓰러진' 느낌 + 상태별 반투명
        prone = pygame.transform.rotate(tmp, 90)
        prone.set_alpha(110 if self.status == 2 else 175)
        surf.blit(prone, (sx + (TILE_SIZE - prone.get_width()) // 2,
                          sy + (TILE_SIZE - prone.get_height()) // 2))
        cx = sx + TILE_SIZE // 2
        cy = sy + TILE_SIZE // 2
        if self.status == 1:
            # 부활 진행 링 (초록) — 파티원이 옆에 있으면 채워짐
            r = TILE_SIZE // 2 + 3
            pygame.draw.circle(surf, (60, 30, 30), (cx, cy), r, 2)
            if self.revive_prog > 0:
                pts = [(cx, cy)]
                import math
                steps = max(2, int(self.revive_prog * 24))
                for i in range(steps + 1):
                    a = -math.pi / 2 + (i / 24.0) * 2 * math.pi
                    pts.append((cx + int(math.cos(a) * r),
                                cy + int(math.sin(a) * r)))
                if len(pts) >= 3:
                    pygame.draw.polygon(surf, (90, 230, 120), pts)
                    pygame.draw.circle(surf, (140, 255, 170), (cx, cy), r, 2)

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
