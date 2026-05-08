"""
강화술 (Fortify) 스킬 파티클 이펙트.
SkillEffect 인스턴스를 생성한 후 매 프레임 update() / draw_below() / draw_above() 를 호출한다.
draw_below : 플레이어 스프라이트 아래에 그릴 요소 (아우라 링)
draw_above : 플레이어 스프라이트 위에 그릴 요소 (상승 파티클)
squeeze_scale : _draw_player_sprite 에서 읽어 스프라이트 스케일에 적용
"""
import math
import random
import pygame

_PI = math.pi


class SkillEffect:
    def __init__(self, color: tuple, duration_ms: int):
        self.alive          = True
        self.color          = color                # (R, G, B)
        self.duration_ms    = duration_ms
        self._elapsed       = 0
        self._particles: list[dict] = []
        self._spawn_timer   = 0
        self.squeeze_scale  = 1.0                  # _draw_player_sprite 가 읽음

    # ── 업데이트 ──────────────────────────────────────────────────────────
    def update(self, dt_ms: int):
        if not self.alive:
            return

        self._elapsed += dt_ms
        if self._elapsed >= self.duration_ms:
            self.alive         = False
            self.squeeze_scale = 1.0
            return

        # Squeeze & Stretch — 첫 500ms 동안 살짝 커졌다 돌아옴
        if self._elapsed < 500:
            t = self._elapsed / 500.0
            self.squeeze_scale = 1.0 + math.sin(t * _PI) * 0.13
        else:
            self.squeeze_scale = 1.0

        # 파티클 스폰 (70ms 마다)
        self._spawn_timer += dt_ms
        while self._spawn_timer >= 70:
            self._spawn_timer -= 70
            self._spawn_particle()

        # 파티클 이동 & 수명 갱신
        for p in self._particles:
            p['life'] += dt_ms
            p['ox']   += p['vx'] * dt_ms
            p['oy']   += p['vy'] * dt_ms
        self._particles = [p for p in self._particles
                           if p['life'] < p['max_life']]

    def _spawn_particle(self):
        angle = random.uniform(0, 2 * _PI)
        radius = random.uniform(4, 13)
        self._particles.append({
            'ox':       math.cos(angle) * radius,
            'oy':       math.sin(angle) * radius + 10,  # 발 근처에서 시작
            'vx':       random.uniform(-0.006, 0.006),  # px/ms
            'vy':       random.uniform(-0.042, -0.018), # 위로 상승
            'life':     0,
            'max_life': random.randint(550, 1100),
            'r':        random.uniform(1.4, 2.8),
            # 색상 변형 (조금씩 다른 색조)
            'tint':     tuple(
                            max(0, min(255, c + random.randint(-30, 50)))
                            for c in self.color
                        ),
        })

    # ── 드로우 헬퍼 ──────────────────────────────────────────────────────
    @staticmethod
    def _alpha_surface(w: int, h: int) -> pygame.Surface:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        return s

    def _fade(self) -> float:
        """전체 알파 배율. 마지막 20% 에서 서서히 사라짐."""
        progress = self._elapsed / self.duration_ms
        if progress > 0.80:
            return max(0.0, (1.0 - progress) / 0.20)
        return 1.0

    # ── 아우라 링 (플레이어 아래) ─────────────────────────────────────────
    def draw_below(self, surf: pygame.Surface, tile_x: int, tile_y: int):
        if not self.alive:
            return

        T    = self._elapsed * 0.001
        fade = self._fade()
        if fade <= 0:
            return

        # 링 중심: 발 위치
        cx = tile_x + 16
        cy = tile_y + 27

        # 외부 희미한 헤일로
        for i in range(4):
            r      = round(16 + math.sin(T * 2.4 + i * 0.4) * 3 + i * 2)
            alpha  = int((55 - i * 12) * fade)
            if alpha <= 0:
                continue
            size = r * 2 + 4
            s = self._alpha_surface(size, size)
            pygame.draw.circle(s, (*self.color, alpha),
                               (size // 2, size // 2), r, 2)
            surf.blit(s, (cx - size // 2, cy - size // 2))

        # 메인 링 (두 겹)
        for thick, r_base, a_base in [(2, 13, 160), (1, 11, 100)]:
            r     = round(r_base + math.sin(T * 2.8) * 2.5)
            alpha = int(a_base * fade)
            if alpha <= 0:
                continue
            size = r * 2 + 6
            s = self._alpha_surface(size, size)
            pygame.draw.circle(s, (*self.color, alpha),
                               (size // 2, size // 2), r, thick)
            surf.blit(s, (cx - size // 2, cy - size // 2))

        # 회전하는 내부 십자 점 (4개 점이 링 위를 공전)
        for i in range(4):
            orbit_r   = round(11 + math.sin(T * 2.8) * 2.5)
            angle     = T * 1.8 + i * _PI * 0.5
            dot_x     = round(cx + math.cos(angle) * orbit_r)
            dot_y     = round(cy + math.sin(angle) * orbit_r * 0.45)  # 타원 (바닥 원근)
            dot_alpha = int(220 * fade)
            if dot_alpha <= 0:
                continue
            dot_s = self._alpha_surface(7, 7)
            pygame.draw.circle(dot_s, (*self.color, dot_alpha), (3, 3), 3)
            lc = tuple(min(255, c + 80) for c in self.color)
            pygame.draw.circle(dot_s, (*lc, dot_alpha), (3, 3), 1)
            surf.blit(dot_s, (dot_x - 3, dot_y - 3))

    # ── 상승 파티클 (플레이어 위) ────────────────────────────────────────
    def draw_above(self, surf: pygame.Surface, tile_x: int, tile_y: int):
        if not self.alive:
            return

        fade = self._fade()
        if fade <= 0:
            return

        cx = tile_x + 16
        cy = tile_y + 16

        for p in self._particles:
            life_frac   = p['life'] / p['max_life']
            alpha       = int(255 * (1.0 - life_frac) * fade)
            if alpha < 5:
                continue
            r = max(1, round(p['r'] * (1.0 - life_frac * 0.6)))
            px_ = round(cx + p['ox'])
            py_ = round(cy + p['oy'])

            size = r * 2 + 2
            ps = self._alpha_surface(size, size)
            # 외곽 원
            pygame.draw.circle(ps, (*p['tint'], alpha),
                               (r, r), r)
            # 밝은 중심
            if r >= 2:
                lc = tuple(min(255, c + 90) for c in p['tint'])
                pygame.draw.circle(ps, (*lc, min(255, alpha + 60)),
                                   (r, r), max(1, r - 1))
            surf.blit(ps, (px_ - r, py_ - r))
