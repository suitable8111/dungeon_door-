"""고해상도 주인공 (스팀 캡슐·마케팅용).

인게임 16×16 아바타를 크게 확대하면 블록이 커서 조잡하다.
여기서는 '같은 캐릭터'(빨간 체커 튜닉·갈색 단발·강철 검)를 더 높은 논리 해상도로
다시 그려, 크게 확대해도 깔끔하게 읽히도록 한다. 픽셀(블록) 느낌은 유지.

색은 인게임 아바타(entities.avatar)의 전사 팔레트와 동일하게 맞춘다.
draw_hero_hd(surf, x, y, target_h) — (x,y) 좌상단, 높이 target_h로 그린다.
"""
import pygame

LW, LH = 68, 90          # 논리 캔버스

# ── 인게임 전사와 동일 팔레트 ───────────────────────────────────────────
SKIN   = (241, 194, 155); SKIN_H = (252, 214, 178); SKIN_L = (210, 164, 126)
HAIR   = (92, 56, 30);    HAIR_H = (124, 82, 46);   HAIR_L = (64, 36, 16)
TUNIC  = (170, 60, 55);   TUNIC_H = (198, 86, 80);  TUNIC_D = (138, 40, 36)
TRIM   = (210, 200, 205); TRIM_D = (150, 142, 150)
PANTS  = (78, 80, 98);    PANTS_H = (100, 102, 122); PANTS_L = (56, 58, 74)
BOOT   = (96, 70, 50);    BOOT_L = (66, 46, 32)
EYE    = (44, 38, 46);    EYEW = (248, 248, 250)
STEEL  = (208, 214, 228); STEEL_H = (240, 244, 252); STEEL_L = (150, 156, 176)
GOLD   = (232, 202, 92);  GOLD_H = (255, 226, 130);  GOLD_L = (176, 140, 48)
GRIP   = (120, 86, 50)
OL     = (40, 30, 36)     # 은은한 외곽선(픽셀 느낌 유지, 가독성용)


def draw_hero_hd(surf, x, y, target_h, facing='down'):
    cv = pygame.Surface((LW, LH), pygame.SRCALPHA)

    def B(gx, gy, col, w=1, h=1):
        pygame.draw.rect(cv, col, (gx, gy, w, h))

    def block(gx, gy, w, h, base, hi=None, lo=None, ol=OL):
        pygame.draw.rect(cv, ol, (gx - 1, gy - 1, w + 2, h + 2))
        pygame.draw.rect(cv, base, (gx, gy, w, h))
        if hi:
            B(gx, gy, hi, w, 1); B(gx, gy, hi, 1, h)
        if lo:
            B(gx, gy + h - 1, lo, w, 1); B(gx + w - 1, gy, lo, 1, h)

    def checker(gx, gy, w, h, a, b, sq=3):
        for yy in range(0, h, sq):
            for xx in range(0, w, sq):
                c = a if ((xx // sq + yy // sq) % 2 == 0) else b
                B(gx + xx, gy + yy, c, min(sq, w - xx), min(sq, h - yy))

    CX = 30

    # ── 다리 (바지 + 부츠) ──────────────────────────────────────────────
    for lx in (CX - 9, CX + 2):
        block(lx, 58, 7, 14, PANTS, PANTS_H, PANTS_L)
        B(lx + 2, 60, PANTS_H, 1, 9)                      # 세로 광
        block(lx - 1, 72, 9, 7, BOOT, None, BOOT_L)       # 부츠
        B(lx - 1, 78, BOOT_L, 9, 1)
        B(lx, 73, (120, 92, 66), 5, 1)                    # 부츠 광

    # ── 튜닉 (빨간 체커) ────────────────────────────────────────────────
    block(CX - 12, 30, 24, 24, TUNIC, None, None)
    checker(CX - 12, 30, 24, 24, TUNIC, TUNIC_D, sq=3)
    B(CX - 12, 30, TUNIC_H, 24, 1)                        # 상단 광
    B(CX - 12, 53, TUNIC_D, 24, 1)                        # 하단 음영
    # 스커트 자락 (허리 아래로 살짝)
    block(CX - 11, 54, 22, 6, TUNIC, None, TUNIC_D)
    checker(CX - 11, 54, 22, 6, TUNIC, TUNIC_D, sq=3)

    # 옷깃(트림)
    block(CX - 6, 28, 12, 3, TRIM, None, TRIM_D)
    B(CX - 3, 31, TRIM, 6, 2)                             # 가슴 V

    # ── 벨트 ────────────────────────────────────────────────────────────
    block(CX - 12, 49, 24, 4, TRIM_D, TRIM, None)
    block(CX - 3, 48, 6, 6, GOLD, GOLD_H, GOLD_L)         # 버클
    B(CX - 1, 50, GOLD_L, 2, 2)

    # ── 어깨(트림 견장, 작게) ──────────────────────────────────────────
    for sx in (CX - 16, CX + 11):
        block(sx, 29, 5, 5, TRIM, None, TRIM_D)

    # ── 팔 (튜닉 소매 + 손) ────────────────────────────────────────────
    # 왼팔
    block(CX - 17, 33, 6, 13, TUNIC, TUNIC_H, TUNIC_D)
    block(CX - 16, 45, 5, 5, SKIN, SKIN_H, SKIN_L)        # 왼손
    # 오른팔 — 전완이 자루 쪽으로
    block(CX + 11, 33, 6, 11, TUNIC, TUNIC_H, TUNIC_D)
    block(CX + 13, 43, 7, 5, TUNIC, TUNIC_H, TUNIC_D)

    # ── 머리 ────────────────────────────────────────────────────────────
    HX, HY, HW, HH = CX - 8, 9, 16, 16
    block(HX, HY, HW, HH, SKIN, SKIN_H, SKIN_L)
    B(HX - 1, HY + 7, OL, 1, 4); B(HX - 1, HY + 7, SKIN_L, 1, 4)     # 귀
    B(HX + HW, HY + 7, OL, 1, 4); B(HX + HW - 1, HY + 7, SKIN_L, 1, 4)
    block(CX - 5, 25, 10, 4, SKIN_L, SKIN, None)          # 목

    # 눈 — 인게임과 동일: 흰 픽셀(위) / 어두운 픽셀(아래) 2단
    for ex in (HX + 3, HX + 10):
        B(ex, HY + 7, EYEW, 3, 2)
        B(ex, HY + 9, EYE, 3, 2)
    # 볼 홍조 + 입
    B(HX + 1, HY + 11, (250, 190, 170), 2, 1)
    B(HX + 13, HY + 11, (250, 190, 170), 2, 1)
    B(HX + 6, HY + 12, SKIN_L, 4, 1)

    # ── 머리카락 (갈색 단발) ────────────────────────────────────────────
    block(HX - 1, HY - 3, HW + 2, 6, HAIR, None, HAIR_L)  # 윗머리
    B(HX + 1, HY - 2, HAIR_H, HW - 2, 1)                  # 윗광
    B(HX - 1, HY + 3, HAIR, 2, 4); B(HX + HW - 1, HY + 3, HAIR, 2, 4)  # 옆머리
    for i, gx in enumerate((HX + 1, HX + 5, HX + 9, HX + 12)):        # 앞머리 삐침
        B(gx, HY + 3, HAIR, 2, 2)
    B(HX + 2, HY + 3, HAIR_L, 2, 1); B(HX + 10, HY + 3, HAIR_L, 2, 1)

    # ── 강철 검 (오른쪽, 세워 듦) — 손이 자루를 쥔다 ───────────────────
    SBX = CX + 18
    block(SBX, 4, 5, 40, STEEL, STEEL_H, STEEL_L)         # 칼날
    B(SBX + 2, 6, STEEL_H, 1, 34)                         # 풀러
    B(SBX + 4, 6, STEEL_L, 1, 34)                         # 우측 엣지
    pygame.draw.polygon(cv, STEEL_H, [(SBX, 4), (SBX + 4, 4), (SBX + 2, 0)])   # 칼끝
    block(SBX - 3, 44, 11, 3, GOLD, GOLD_H, GOLD_L)       # 코등이
    B(SBX - 3, 45, GOLD_L, 11, 1)
    block(SBX + 1, 47, 3, 9, GRIP, None, BOOT_L)          # 손잡이
    for gy in range(48, 56, 2):
        B(SBX + 1, gy, BOOT_L, 3, 1)
    block(SBX, 56, 5, 3, GOLD, GOLD_H, GOLD_L)            # 폼멜
    B(SBX + 1, 57, GOLD_H, 3, 1)
    block(SBX - 2, 47, 5, 6, SKIN, SKIN_H, SKIN_L)        # 자루 쥔 오른손
    B(SBX - 1, 48, SKIN_H, 3, 1)
    for gy in (49, 51):
        B(SBX - 2, gy, SKIN_L, 5, 1)

    # ── 크롭 후 최근접 확대 ─────────────────────────────────────────────
    bb = cv.get_bounding_rect()
    if bb.width == 0:
        bb = pygame.Rect(0, 0, LW, LH)
    crop = cv.subsurface(bb).copy()
    w = max(1, int(bb.width * target_h / bb.height))
    scaled = pygame.transform.scale(crop, (w, target_h))
    surf.blit(scaled, (x, y))
    return w, target_h
