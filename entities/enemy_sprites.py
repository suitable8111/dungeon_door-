import pygame, math
_PI = math.pi

def _c(s, col, x, y, r):
    pygame.draw.circle(s, col, (round(x), round(y)), max(1, r))

def _L(col, v=50):  return tuple(min(255, c + v) for c in col)
def _D(col, v=50):  return tuple(max(0, c - v) for c in col)
def _LL(col):       return tuple(min(255, c + 90) for c in col)
def _A(col, a=180): return col + (a,)

def _glow(s, col, x, y, r):
    _c(s, _D(col, 30), x, y, r + 2)
    _c(s, col,         x, y, r)
    _c(s, _L(col, 70), x, y, max(1, r - 1))

def _orbit(cx, cy, r, angle):
    return cx + math.cos(angle) * r, cy + math.sin(angle) * r

def _eye(s, cx, cy, t, off=3):
    _c(s, (255, 255, 255), cx - off, cy - 1, 2)
    _c(s, (255, 255, 255), cx + off, cy - 1, 2)
    _c(s, (0, 0, 0),       cx - off, cy - 1, 1)
    _c(s, (0, 0, 0),       cx + off, cy - 1, 1)

def _humanoid(s, col, cx, cy, t, head_r=4, body_r=5, arm_r=2, leg_r=2,
              head_dy=-8, body_dy=1, arm_dx=7, arm_dy=-1,
              leg_dx=4, leg_dy=8, breathe=0.8):
    T = t * 0.001
    bob = math.sin(T * 2.5) * breathe
    lc, dc = _L(col, 40), _D(col, 40)
    bx, by = cx, cy + bob
    _c(s, col, bx, by + body_dy, body_r)
    _c(s, lc,  bx, by + head_dy, head_r)
    _c(s, _L(col, 20), bx, by + head_dy - 1, max(1, head_r - 1))
    _c(s, dc, bx - arm_dx, by + arm_dy, arm_r)
    _c(s, dc, bx + arm_dx, by + arm_dy, arm_r)
    _c(s, dc, bx - leg_dx, by + leg_dy, leg_r)
    _c(s, dc, bx + leg_dx, by + leg_dy, leg_r)

def _skeleton_base(s, col, cx, cy, t, breathe=0.5):
    T = t * 0.001
    bob = math.sin(T * 2.0) * breathe
    wh = (230, 230, 230)
    bx, by = cx, cy + bob
    _c(s, wh, bx, by - 8, 4)
    _c(s, _D(wh, 40), bx, by + 1, 4)
    _c(s, _D(wh, 60), bx, by + 8, 3)
    _c(s, _D(wh, 30), bx - 6, by,     2)
    _c(s, _D(wh, 30), bx + 6, by,     2)
    _c(s, _D(wh, 50), bx - 3, by + 10, 2)
    _c(s, _D(wh, 50), bx + 3, by + 10, 2)
    if col != (255, 255, 255):
        _c(s, col, bx, by - 8, 2)


# ── rat ─────────────────────────────────────────────────────────────────────
def draw_rat(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 20
    bob = math.sin(T * 4) * 1
    _c(s, col, cx, cy + bob, 6)
    _c(s, col, cx + 7, cy - 2 + bob, 4)
    _c(s, _L(col, 40), cx + 7, cy - 4 + bob, 2)
    _c(s, (255, 80, 80), cx + 9, cy - 5 + bob, 1)
    _c(s, (255, 80, 80), cx + 11, cy - 4 + bob, 1)
    for i in range(4):
        lx = cx - 2 + i * 2 - 2
        _c(s, _D(col, 30), lx, cy + 6 + bob, 1)
    tail_a = math.sin(T * 3) * 0.3
    for i in range(5):
        tx, ty = _orbit(cx - 8, cy + 2, i * 2, _PI + tail_a + i * 0.3)
        _c(s, _D(col, 20), tx, ty + bob, 1)


# ── bat ─────────────────────────────────────────────────────────────────────
def draw_bat(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    flap = math.sin(T * 6) * 5
    lc = _L(col, 30); dc = _D(col, 30)
    for i in range(6):
        a = _PI + flap * 0.08 + i * 0.18
        wx, wy = cx - 4 - i * 2, cy - 2 + flap * 0.4 * (i / 5)
        _c(s, dc if i > 2 else col, wx, wy, 3 - i // 3)
    for i in range(6):
        a = flap * 0.08 + i * 0.18
        wx, wy = cx + 4 + i * 2, cy - 2 + flap * 0.4 * (i / 5)
        _c(s, dc if i > 2 else col, wx, wy, 3 - i // 3)
    _c(s, col, cx, cy, 4)
    _c(s, lc, cx, cy - 4, 3)
    _c(s, (200, 50, 50), cx - 2, cy - 5, 1)
    _c(s, (200, 50, 50), cx + 2, cy - 5, 1)


# ── centipede ────────────────────────────────────────────────────────────────
def draw_centipede(s, x, y, col, t):
    T = t * 0.001; cy = y + 18
    for i in range(8):
        wave = math.sin(T * 4 + i * 0.7) * 3
        seg_x = x + 4 + i * 3.5
        seg_y = cy + wave
        r = 4 if i == 0 else 3
        _c(s, col, seg_x, seg_y, r)
        if i > 0:
            _c(s, _D(col, 30), seg_x - 2, seg_y - 3, 1)
            _c(s, _D(col, 30), seg_x - 2, seg_y + 3, 1)
    _c(s, (255, 220, 50), x + 4, cy + math.sin(T * 4) * 3, 2)
    _c(s, (200, 50, 50), x + 2, cy + math.sin(T * 4) * 3 - 1, 1)
    _c(s, (200, 50, 50), x + 6, cy + math.sin(T * 4) * 3 - 1, 1)


# ── spider ────────────────────────────────────────────────────────────────────
def draw_spider(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 3) * 1
    _c(s, col, cx, cy + bob, 5)
    _c(s, _L(col, 30), cx, cy - 4 + bob, 4)
    for i in range(4):
        a = _PI * 0.25 + i * _PI * 0.5
        leg_r = math.sin(T * 4 + i) * 1.5 + 9
        lx, ly = _orbit(cx, cy + bob, leg_r, a - 0.3)
        _c(s, _D(col, 20), lx, ly, 2)
        lx2, ly2 = _orbit(cx, cy + bob, leg_r + 3, a)
        _c(s, _D(col, 40), lx2, ly2, 1)
        lx3, ly3 = _orbit(cx, cy + bob, leg_r, -a - 0.3)
        _c(s, _D(col, 20), lx3, ly3, 2)
        lx4, ly4 = _orbit(cx, cy + bob, leg_r + 3, -a)
        _c(s, _D(col, 40), lx4, ly4, 1)
    _c(s, (200, 50, 50), cx - 2, cy - 5 + bob, 1)
    _c(s, (200, 50, 50), cx + 2, cy - 5 + bob, 1)


# ── slime ─────────────────────────────────────────────────────────────────────
def draw_slime(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 20
    pulse = 1 + math.sin(T * 2) * 0.15
    squish_y = math.sin(T * 2) * 2
    _c(s, _D(col, 40), cx, cy + 1 + squish_y, round(8 * pulse))
    _c(s, col, cx, cy - 1 + squish_y * 0.5, round(7 * pulse))
    _c(s, _L(col, 60), cx, cy - 3, round(4 * pulse))
    _c(s, (255, 255, 255, 120), cx - 2, cy - 5, 2)
    for i in range(3):
        bx, by = cx - 5 + i * 5, cy - 4 + math.sin(T * 3 + i) * 2
        _c(s, _L(col, 80), bx, by, 1)


# ── goblin ────────────────────────────────────────────────────────────────────
def draw_goblin(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 18, t, head_r=4, body_r=4,
              head_dy=-7, body_dy=1, arm_dx=6, leg_dx=3, leg_dy=7)
    T = t * 0.001; cx, cy = x + 16, y + 10 + math.sin(T * 2.5) * 0.8
    _c(s, (255, 200, 50), cx - 2, cy - 1, 1)
    _c(s, (255, 200, 50), cx + 2, cy - 1, 1)


# ── blade_skeleton ────────────────────────────────────────────────────────────
def draw_blade_skeleton(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 0.5
    blade_a = math.sin(T * 3) * 0.4
    bx, by = cx + 6, cy + bob
    _c(s, (180, 180, 220), bx + math.cos(blade_a) * 3, by - 6 + math.sin(blade_a) * 3, 2)
    _c(s, (220, 220, 255), bx + math.cos(blade_a) * 2, by - 4 + math.sin(blade_a) * 2, 1)


# ── shield_skeleton ───────────────────────────────────────────────────────────
def draw_shield_skeleton(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 0.5
    _c(s, (100, 100, 180), cx - 7, cy + bob + 1, 4)
    _c(s, (140, 140, 220), cx - 7, cy + bob, 3)
    _c(s, (200, 200, 255), cx - 7, cy + bob - 1, 1)


# ── archer_skeleton ────────────────────────────────────────────────────────────
def draw_archer_skeleton(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 0.5
    draw_a = math.sin(T * 1.5) * 0.5
    for i in range(4):
        ax = cx + 7 - i
        ay = cy - 3 + bob + i * 1.5 + math.sin(draw_a) * i
        _c(s, (180, 130, 80), ax, ay, 1)
    _c(s, (220, 180, 100), cx + 7, cy - 3 + bob, 2)


# ── spear_skeleton ─────────────────────────────────────────────────────────────
def draw_spear_skeleton(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 0.5
    thrust = math.sin(T * 3) * 2
    for i in range(6):
        _c(s, (160, 120, 60), cx + 6 + thrust, cy - 8 + i * 2.5 + bob, 1)
    _c(s, (200, 200, 200), cx + 6 + thrust, cy - 8 + bob, 2)


# ── skeleton ───────────────────────────────────────────────────────────────────
def draw_skeleton(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 8
    bob = math.sin(T * 2) * 0.5
    _c(s, (50, 50, 50), cx - 1, cy + bob, 1)
    _c(s, (50, 50, 50), cx + 1, cy + bob, 1)


# ── prisoner ────────────────────────────────────────────────────────────────────
def draw_prisoner(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 17, t, head_r=3, body_r=4,
              head_dy=-7, arm_dx=5, leg_dx=3, leg_dy=7, breathe=1.2)
    T = t * 0.001; cx, cy = x + 16, y + 24
    for i in range(3):
        cx2 = cx - 4 + i * 4
        _c(s, (180, 140, 60), cx2, cy + math.sin(T + i) * 1, 1)


# ── zombie ──────────────────────────────────────────────────────────────────────
def draw_zombie(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 17
    lurch = math.sin(T * 1.5) * 3
    _humanoid(s, col, cx + lurch * 0.3, cy, t, head_r=4, body_r=5,
              head_dy=-8, arm_dx=8, arm_dy=0, leg_dx=4, leg_dy=8, breathe=2)
    _c(s, (80, 160, 80), cx + lurch * 0.3, cy - 5, 2)


# ── ghost ────────────────────────────────────────────────────────────────────────
def draw_ghost(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    drift = math.sin(T * 1.5) * 3
    pulse = 1 + math.sin(T * 2) * 0.2
    lc = _L(col, 60)
    _c(s, _D(col, 20), cx, cy + drift, round(8 * pulse))
    _c(s, col, cx, cy - 1 + drift, round(7 * pulse))
    _c(s, lc, cx, cy - 3 + drift, round(5 * pulse))
    _c(s, (240, 240, 255), cx - 2, cy - 5 + drift, 2)
    _c(s, (240, 240, 255), cx + 2, cy - 5 + drift, 2)
    for i in range(3):
        ox = cx - 6 + i * 6
        oy = cy + 7 + math.sin(T * 3 + i * 1.2) * 2
        _c(s, _D(col, 30), ox + drift * 0.3, oy, 2)


# ── ghoul ─────────────────────────────────────────────────────────────────────
def draw_ghoul(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    crouch = math.sin(T * 2) * 1.5
    _humanoid(s, col, cx, cy + crouch, t, head_r=4, body_r=5,
              head_dy=-7, body_dy=2, arm_dx=7, arm_dy=2, leg_dx=3, leg_dy=7, breathe=1.5)
    claw_a = math.sin(T * 4) * 0.5
    for i in range(3):
        lx, ly = cx - 8 + i * 1.5, cy + 4 + crouch + math.sin(claw_a + i) * 2
        _c(s, _D(col, 50), lx, ly, 1)


# ── corpse_flower ──────────────────────────────────────────────────────────────
def draw_corpse_flower(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 20
    sway = math.sin(T * 1.5) * 2
    _c(s, (60, 120, 40), cx + sway * 0.3, cy, 3)
    _c(s, (60, 120, 40), cx + sway * 0.5, cy - 4, 2)
    _c(s, (60, 120, 40), cx + sway, cy - 8, 2)
    for i in range(6):
        a = i * _PI / 3 + T
        px, py = _orbit(cx + sway, cy - 10, 5, a)
        _c(s, col, px, py, 3)
    _c(s, _L(col, 80), cx + sway, cy - 10, 3)
    _c(s, (255, 220, 50), cx + sway, cy - 10, 1)


# ── jar_crawler ────────────────────────────────────────────────────────────────
def draw_jar_crawler(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 19
    roll = math.sin(T * 3) * 2
    _c(s, (180, 160, 100), cx + roll, cy, 8)
    _c(s, (220, 200, 140), cx + roll, cy - 3, 6)
    _c(s, (140, 120, 80),  cx + roll, cy + 5, 5)
    _c(s, col, cx + roll, cy - 4, 3)
    _c(s, (200, 50, 50), cx - 1 + roll, cy - 5, 1)
    _c(s, (200, 50, 50), cx + 1 + roll, cy - 5, 1)
    for i in range(4):
        lx = cx - 10 + roll + i * 2
        _c(s, _D(col, 20), lx, cy + 5, 1)
        lx2 = cx + 4 + roll + i * 2
        _c(s, _D(col, 20), lx2, cy + 5, 1)


# ── chest_mimic ────────────────────────────────────────────────────────────────
def draw_chest_mimic(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    chomp = abs(math.sin(T * 2)) * 3
    _c(s, (140, 100, 60), cx, cy + 2, 9)
    _c(s, (180, 130, 80), cx, cy - 2 - chomp, 8)
    _c(s, (200, 160, 100), cx, cy - 2 - chomp, 6)
    _c(s, (220, 50, 50), cx, cy + chomp * 0.3, 1)
    _c(s, (220, 50, 50), cx - 5, cy + chomp * 0.3, 1)
    _c(s, (220, 50, 50), cx + 5, cy + chomp * 0.3, 1)
    _c(s, (255, 215, 0), cx, cy - 2 - chomp, 2)
    _c(s, (200, 50, 50), cx - 3, cy + 1, 2)
    _c(s, (200, 50, 50), cx + 3, cy + 1, 2)
    _c(s, (0, 0, 0), cx - 3, cy + 1, 1)
    _c(s, (0, 0, 0), cx + 3, cy + 1, 1)


# ── chain_beast ────────────────────────────────────────────────────────────────
def draw_chain_beast(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    struggle = math.sin(T * 4) * 2
    _humanoid(s, col, cx + struggle, cy, t, head_r=5, body_r=5,
              arm_dx=7, leg_dx=4, breathe=2)
    for i in range(5):
        a = T * 3 + i * _PI * 0.4
        lx, ly = cx + struggle + math.cos(a) * (5 + i * 1.5), cy + math.sin(a) * (4 + i)
        _c(s, (150, 150, 170), lx, ly, 1)


# ── iron_cage ──────────────────────────────────────────────────────────────────
def draw_iron_cage(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    shake = math.sin(T * 5) * 1
    for dx in [-7, 0, 7]:
        for i in range(5):
            _c(s, (120, 120, 140), cx + dx + shake, cy - 8 + i * 4, 1)
    for dy in [-8, 8]:
        for i in range(4):
            _c(s, (100, 100, 120), cx - 7 + i * 5 + shake, cy + dy, 1)
    _c(s, col, cx + shake, cy, 4)
    _c(s, (200, 50, 50), cx - 2 + shake, cy - 1, 1)
    _c(s, (200, 50, 50), cx + 2 + shake, cy - 1, 1)


# ── rock_golem ─────────────────────────────────────────────────────────────────
def draw_rock_golem(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    stomp = abs(math.sin(T * 1.5)) * 2
    lc, dc = _L(col, 30), _D(col, 40)
    _c(s, dc,  cx, cy + stomp, 9)
    _c(s, col, cx, cy - 3 + stomp, 7)
    _c(s, lc,  cx, cy - 6 + stomp, 5)
    _c(s, dc,  cx - 9, cy + stomp, 4)
    _c(s, dc,  cx + 9, cy + stomp, 4)
    _c(s, dc,  cx - 5, cy + 10 + stomp, 4)
    _c(s, dc,  cx + 5, cy + 10 + stomp, 4)
    _c(s, (255, 180, 30), cx - 2, cy - 4 + stomp, 1)
    _c(s, (255, 180, 30), cx + 2, cy - 4 + stomp, 1)


# ── torturer ───────────────────────────────────────────────────────────────────
def draw_torturer(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=4, body_r=6,
              arm_dx=8, leg_dx=4, breathe=0.8)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.8
    raise_a = math.sin(T * 3) * 0.8
    for i in range(4):
        _c(s, (180, 100, 60), cx + 8, cy - 4 + bob + i * 1.5 * raise_a, 1)


# ── whip_master ────────────────────────────────────────────────────────────────
def draw_whip_master(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.8
    for i in range(8):
        a = T * 5 + i * 0.4
        wx = cx + 8 + math.cos(a) * i * 1.5
        wy = cy + bob - 4 + math.sin(a + i * 0.5) * i * 0.8
        _c(s, (160, 100, 60), wx, wy, max(1, 2 - i // 4))


# ── brand_man ─────────────────────────────────────────────────────────────────
def draw_brand_man(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.8
    glow_pulse = 1 + math.sin(T * 4) * 0.3
    _glow(s, (255, 100, 30), cx + 8, cy - 2 + bob, round(3 * glow_pulse))
    _c(s, (255, 200, 100), cx + 8, cy - 2 + bob, round(2 * glow_pulse))


# ── executioner_nov ────────────────────────────────────────────────────────────
def draw_executioner_nov(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    _humanoid(s, col, cx, cy, t, head_r=5, body_r=7,
              arm_dx=9, leg_dx=5, leg_dy=9, breathe=0.6)
    bob = math.sin(T * 1.5) * 0.6
    axe_a = math.sin(T * 2) * 0.5
    for i in range(5):
        ax = cx + 9 + math.cos(axe_a) * i * 0.5
        ay = cy - 6 + bob - i * 2 + math.sin(axe_a) * i * 0.5
        _c(s, (180, 180, 200), ax, ay, 2)
    _c(s, (220, 220, 240), cx + 9, cy - 12 + bob, 3)


# ── poison_sprite ──────────────────────────────────────────────────────────────
def draw_poison_sprite(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    drift = math.sin(T * 2) * 3
    pulse = 1 + math.sin(T * 3) * 0.2
    _glow(s, col, cx, cy + drift, round(6 * pulse))
    _c(s, _L(col, 80), cx, cy - 2 + drift, round(3 * pulse))
    for i in range(5):
        a = T * 2 + i * _PI * 0.4
        px, py = _orbit(cx, cy + drift, 6, a)
        _c(s, _L(col, 40), px, py, 1)


# ── bone_wizard ────────────────────────────────────────────────────────────────
def draw_bone_wizard(s, x, y, col, t):
    _skeleton_base(s, col, x + 16, y + 16, t)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 0.5
    orb_pulse = 1 + math.sin(T * 4) * 0.3
    _glow(s, (150, 80, 200), cx + 7, cy - 4 + bob, round(3 * orb_pulse))
    for i in range(6):
        a = T * 3 + i * _PI / 3
        px, py = _orbit(cx + 7, cy - 4 + bob, 4, a)
        _c(s, (200, 150, 255), px, py, 1)


# ── curse_mage ─────────────────────────────────────────────────────────────────
def draw_curse_mage(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=4, body_r=5, breathe=0.5)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.5
    for i in range(8):
        a = T * 2 + i * _PI / 4
        px, py = _orbit(cx, cy - 8 + bob, 7, a)
        _c(s, (180, 50, 220), px, py, 1)
    _c(s, (220, 100, 255), cx, cy - 8 + bob, 2)


# ── illusionist ────────────────────────────────────────────────────────────────
def draw_illusionist(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, breathe=0.5)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.5
    for i in range(12):
        a = T * 1.5 + i * _PI / 6
        r = 8 + math.sin(T * 3 + i) * 2
        px, py = _orbit(cx, cy + bob, r, a)
        _c(s, _L(col, 60 + i * 5), px, py, 1)


# ── specter ────────────────────────────────────────────────────────────────────
def draw_specter(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    drift = math.sin(T * 1.2) * 4
    pulse = 1 + math.sin(T * 2.5) * 0.25
    dc = _D(col, 40); lc = _L(col, 80)
    _c(s, dc, cx, cy + drift, round(9 * pulse))
    _c(s, col, cx, cy - 2 + drift, round(7 * pulse))
    _c(s, lc, cx, cy - 5 + drift, round(4 * pulse))
    for i in range(4):
        ox = cx - 9 + i * 6
        oy = cy + 8 + math.sin(T * 2.5 + i) * 3 + drift
        _c(s, dc, ox, oy, 2)
    _c(s, (255, 255, 255), cx - 2, cy - 4 + drift, 1)
    _c(s, (255, 255, 255), cx + 2, cy - 4 + drift, 1)


# ── shadow_stalker ─────────────────────────────────────────────────────────────
def draw_shadow_stalker(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    flicker = math.sin(T * 7) * 1
    dc = _D(col, 30)
    _humanoid(s, dc, cx + flicker, cy, t, head_r=4, body_r=4,
              arm_dx=6, leg_dx=3, breathe=0.3)
    for i in range(6):
        a = T * 4 + i * _PI / 3
        px, py = _orbit(cx + flicker, cy, 9 + math.sin(T * 3 + i) * 2, a)
        _c(s, _D(col, 50 + i * 5), px, py, 1)


# ── ambusher ───────────────────────────────────────────────────────────────────
def draw_ambusher(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    crouch = math.sin(T * 2) * 1
    _humanoid(s, col, cx, cy + crouch, t, head_r=3, body_r=4,
              head_dy=-6, body_dy=2, arm_dx=6, arm_dy=2, leg_dx=3, leg_dy=6, breathe=0.5)
    _c(s, _D(col, 20), cx + 6, cy + crouch - 1, 2)
    _c(s, (200, 200, 220), cx + 6, cy + crouch - 1, 1)


# ── assassin ───────────────────────────────────────────────────────────────────
def draw_assassin(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=3, body_r=4, breathe=0.4)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.4
    _c(s, (200, 200, 220), cx + 6, cy - 2 + bob, 1)
    _c(s, (200, 200, 220), cx + 7, cy - 1 + bob, 1)
    _c(s, (200, 200, 220), cx + 8, cy + bob,     1)


# ── thief ──────────────────────────────────────────────────────────────────────
def draw_thief(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=3, body_r=4, breathe=1)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 1
    _c(s, (255, 215, 0), cx + 5, cy - 4 + bob, 2)
    _c(s, (200, 170, 30), cx + 5, cy - 4 + bob, 1)


# ── bandit ─────────────────────────────────────────────────────────────────────
def draw_bandit(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=4, body_r=5, breathe=0.8)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.8
    _c(s, (160, 80, 40), cx + 7, cy + bob, 3)
    _c(s, (200, 120, 60), cx + 7, cy + bob, 2)


# ── giant_spider ───────────────────────────────────────────────────────────────
def draw_giant_spider(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2) * 1.5
    _c(s, col, cx, cy + bob, 7)
    _c(s, _L(col, 30), cx, cy - 4 + bob, 5)
    for i in range(4):
        a = _PI * 0.2 + i * _PI * 0.5
        lr = math.sin(T * 3 + i) * 2 + 11
        lx, ly = _orbit(cx, cy + bob, lr, a - 0.3)
        _c(s, _D(col, 20), lx, ly, 2)
        lx2, ly2 = _orbit(cx, cy + bob, lr + 4, a)
        _c(s, _D(col, 40), lx2, ly2, 2)
        lx3, ly3 = _orbit(cx, cy + bob, lr, -a - 0.3)
        _c(s, _D(col, 20), lx3, ly3, 2)
        lx4, ly4 = _orbit(cx, cy + bob, lr + 4, -a)
        _c(s, _D(col, 40), lx4, ly4, 2)
    _c(s, (220, 50, 50), cx - 2, cy - 5 + bob, 2)
    _c(s, (220, 50, 50), cx + 2, cy - 5 + bob, 2)


# ── giant_zombie ───────────────────────────────────────────────────────────────
def draw_giant_zombie(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 14
    lurch = math.sin(T * 1.2) * 4
    _humanoid(s, col, cx + lurch * 0.3, cy, t, head_r=5, body_r=7,
              head_dy=-10, arm_dx=10, arm_dy=1, leg_dx=5, leg_dy=10, breathe=3)
    _c(s, (80, 160, 80), cx + lurch * 0.3, cy - 5, 3)


# ── steel_knight ────────────────────────────────────────────────────────────────
def draw_steel_knight(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    _humanoid(s, (180, 180, 200), cx, cy, t, head_r=5, body_r=6,
              arm_dx=8, leg_dx=4, leg_dy=9, breathe=0.4)
    bob = math.sin(T * 2.5) * 0.4
    _c(s, (200, 200, 220), cx, cy - 8 + bob, 5)
    _c(s, (220, 220, 240), cx, cy - 9 + bob, 3)
    _c(s, col, cx - 1, cy - 10 + bob, 1)
    _c(s, col, cx + 1, cy - 10 + bob, 1)


# ── death_mage ─────────────────────────────────────────────────────────────────
def draw_death_mage(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=4, body_r=5, breathe=0.5)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.5
    for i in range(8):
        a = T * 3 + i * _PI / 4
        r = 8 + math.sin(T * 2 + i * 0.5) * 2
        px, py = _orbit(cx, cy + bob, r, a)
        _c(s, (100 + i * 15, 0, 150 + i * 10), px, py, 1)
    _glow(s, (100, 0, 150), cx, cy - 8 + bob, 3)


# ── orc ─────────────────────────────────────────────────────────────────────────
def draw_orc(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=5, body_r=7,
              arm_dx=9, leg_dx=5, breathe=1)
    T = t * 0.001; cx, cy = x + 16, y + 8
    bob = math.sin(T * 2.5) * 1
    _c(s, _L(col, 20), cx - 2, cy + bob + 2, 2)
    _c(s, _L(col, 20), cx + 2, cy + bob + 2, 2)


# ── mimic ─────────────────────────────────────────────────────────────────────
def draw_mimic(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    chomp = abs(math.sin(T * 3)) * 4
    _c(s, (120, 80, 50), cx, cy + 2, 10)
    _c(s, (160, 110, 70), cx, cy - 2 - chomp, 9)
    _c(s, (200, 150, 100), cx, cy - 3 - chomp, 7)
    for i in range(5):
        _c(s, (220, 220, 220), cx - 8 + i * 4, cy + chomp * 0.2, 1)
        _c(s, (220, 220, 220), cx - 8 + i * 4, cy - 1 - chomp, 1)
    _c(s, (200, 50, 50), cx - 3, cy + 1, 2)
    _c(s, (200, 50, 50), cx + 3, cy + 1, 2)
    _c(s, (0, 0, 0), cx - 3, cy + 1, 1)
    _c(s, (0, 0, 0), cx + 3, cy + 1, 1)
    _c(s, (255, 215, 0), cx, cy - 4 - chomp, 2)


# ── blood_bat ─────────────────────────────────────────────────────────────────
def draw_blood_bat(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 18
    flap = math.sin(T * 8) * 7
    dc = _D(col, 20)
    for i in range(7):
        wx = cx - 5 - i * 2
        wy = cy - 2 + flap * 0.35 * (i / 6)
        _c(s, dc if i > 3 else col, wx, wy, 3 - i // 4)
    for i in range(7):
        wx = cx + 5 + i * 2
        wy = cy - 2 + flap * 0.35 * (i / 6)
        _c(s, dc if i > 3 else col, wx, wy, 3 - i // 4)
    _c(s, col, cx, cy, 5)
    _c(s, _L(col, 30), cx, cy - 4, 4)
    _c(s, (255, 100, 100), cx - 2, cy - 5, 1)
    _c(s, (255, 100, 100), cx + 2, cy - 5, 1)


# ── soul_absorber ─────────────────────────────────────────────────────────────
def draw_soul_absorber(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    drift = math.sin(T * 1.8) * 3
    pulse = 1 + math.sin(T * 3) * 0.2
    _glow(s, _D(col, 20), cx, cy + drift, round(9 * pulse))
    _glow(s, col,         cx, cy + drift, round(7 * pulse))
    _c(s, _L(col, 80), cx, cy + drift, round(4 * pulse))
    for i in range(8):
        a = T * 1.5 + i * _PI / 4
        r = 10 + math.sin(T * 2 + i) * 2
        sx, sy = _orbit(cx, cy + drift, r, a)
        _c(s, _L(col, 40 + i * 10), sx, sy, 1)


# ── troll ─────────────────────────────────────────────────────────────────────
def draw_troll(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 14
    stomp = abs(math.sin(T * 1.5)) * 2
    _humanoid(s, col, cx, cy + stomp, t, head_r=5, body_r=8,
              head_dy=-11, arm_dx=11, arm_dy=0, leg_dx=5, leg_dy=11, breathe=1.5)
    bob = math.sin(T * 2.5) * 1.5
    _c(s, _L(col, 30), cx, cy - 11 + stomp + bob, 3)


# ── grave_titan ────────────────────────────────────────────────────────────────
def draw_grave_titan(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 13
    stomp = abs(math.sin(T * 1.2)) * 3
    wh = (230, 230, 230)
    _c(s, (160, 160, 160), cx, cy + stomp, 10)
    _c(s, wh, cx, cy - 3 + stomp, 7)
    _c(s, wh, cx, cy - 10 + stomp, 6)
    _c(s, (180, 180, 180), cx, cy - 14 + stomp, 5)
    _c(s, (200, 200, 200), cx - 11, cy - 1 + stomp, 5)
    _c(s, (200, 200, 200), cx + 11, cy - 1 + stomp, 5)
    _c(s, (180, 180, 180), cx - 6, cy + 12 + stomp, 4)
    _c(s, (180, 180, 180), cx + 6, cy + 12 + stomp, 4)
    _c(s, (255, 80, 30), cx - 2, cy - 11 + stomp, 2)
    _c(s, (255, 80, 30), cx + 2, cy - 11 + stomp, 2)


# ── wizard ─────────────────────────────────────────────────────────────────────
def draw_wizard(s, x, y, col, t):
    _humanoid(s, col, x + 16, y + 16, t, head_r=4, body_r=5, breathe=0.5)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.5
    hat_pulse = 1 + math.sin(T * 3) * 0.1
    _c(s, _D(col, 60), cx, cy - 9 + bob, round(5 * hat_pulse))
    _c(s, _D(col, 40), cx, cy - 12 + bob, round(3 * hat_pulse))
    _c(s, _D(col, 20), cx, cy - 14 + bob, round(2 * hat_pulse))
    for i in range(6):
        a = T * 2 + i * _PI / 3
        px, py = _orbit(cx + 8, cy - 2 + bob, 5, a)
        _c(s, _L(col, 60), px, py, 1)
    _glow(s, _L(col, 80), cx + 8, cy - 2 + bob, 2)


# ── jail_captain ────────────────────────────────────────────────────────────────
def draw_jail_captain(s, x, y, col, t):
    _humanoid(s, (160, 140, 100), x + 16, y + 16, t, head_r=4, body_r=6,
              arm_dx=8, leg_dx=4, breathe=0.5)
    T = t * 0.001; cx, cy = x + 16, y + 16
    bob = math.sin(T * 2.5) * 0.5
    _c(s, (180, 160, 120), cx, cy - 8 + bob, 5)
    _c(s, col, cx, cy - 10 + bob, 2)
    _c(s, (200, 180, 140), cx + 8, cy + bob, 3)
    _c(s, (220, 200, 160), cx + 8, cy + bob, 2)


# ── mace_knight ───────────────────────────────────────────────────────────────
def draw_mace_knight(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    _humanoid(s, (170, 170, 190), cx, cy, t, head_r=5, body_r=6,
              arm_dx=8, leg_dx=4, breathe=0.5)
    bob = math.sin(T * 2.5) * 0.5
    swing = math.sin(T * 3) * 4
    _c(s, (140, 140, 160), cx + 8, cy - 2 + bob + swing, 3)
    _c(s, (100, 80, 60),   cx + 8, cy + 2 + bob + swing * 0.5, 2)
    _c(s, (180, 180, 200), cx + 8, cy - 3 + bob + swing, 4)
    for i in range(4):
        a = i * _PI / 2 + T * 3
        sx, sy = _orbit(cx + 8, cy - 3 + bob + swing, 4, a)
        _c(s, (200, 200, 220), sx, sy, 1)


# ── stomp_exec ─────────────────────────────────────────────────────────────────
def draw_stomp_exec(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 14
    stomp = abs(math.sin(T * 2)) * 3
    _humanoid(s, col, cx, cy + stomp, t, head_r=5, body_r=7,
              head_dy=-11, arm_dx=10, leg_dx=5, leg_dy=10, breathe=1)
    bob = math.sin(T * 2.5) * 1
    for i in range(5):
        ax = cx + 10
        ay = cy - 6 + bob + stomp - i * 2
        _c(s, (180, 180, 200), ax, ay, 2)
    _c(s, (220, 220, 240), cx + 10, cy - 14 + bob + stomp, 4)


# ── dragon ─────────────────────────────────────────────────────────────────────
def draw_dragon(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    breathe = math.sin(T * 1.5) * 2
    lc, dc = _L(col, 40), _D(col, 40)
    _c(s, dc,  cx, cy + breathe, 11)
    _c(s, col, cx, cy - 2 + breathe, 9)
    _c(s, lc,  cx, cy - 6 + breathe, 6)
    _c(s, dc,  cx - 10, cy - 1 + breathe, 4)
    _c(s, dc,  cx + 10, cy - 1 + breathe, 4)
    _c(s, lc,  cx, cy - 8 + breathe, 4)
    for i in range(3):
        a = T * 2 + i * 1.2
        wx, wy = cx - 10 - i * 3, cy - 4 + breathe + math.sin(a) * 4
        _c(s, dc, wx, wy, 3 - i)
        wx2, wy2 = cx + 10 + i * 3, cy - 4 + breathe + math.sin(a + _PI) * 4
        _c(s, dc, wx2, wy2, 3 - i)
    fire_pulse = 1 + math.sin(T * 8) * 0.4
    _glow(s, (255, 120, 30), cx + 10 + breathe, cy - 7 + breathe, round(3 * fire_pulse))
    _c(s, (255, 220, 0), cx - 3, cy - 7 + breathe, 2)
    _c(s, (255, 220, 0), cx + 3, cy - 7 + breathe, 2)


# ── dark_knight ───────────────────────────────────────────────────────────────
def draw_dark_knight(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    _humanoid(s, col, cx, cy, t, head_r=5, body_r=7,
              arm_dx=9, leg_dx=5, breathe=0.5)
    bob = math.sin(T * 2.5) * 0.5
    _c(s, _D(col, 30), cx, cy - 8 + bob, 6)
    _c(s, _D(col, 10), cx, cy - 10 + bob, 4)
    for i in range(3):
        a = T * 4 + i * _PI * 2 / 3
        sx, sy = _orbit(cx, cy + bob, 9, a)
        _c(s, _D(col, 60), sx, sy, 2)
    _c(s, (180, 50, 220), cx, cy - 8 + bob, 2)


# ── lich ──────────────────────────────────────────────────────────────────────
def draw_lich(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 14
    drift = math.sin(T * 1.5) * 3
    wh = (230, 230, 230)
    _c(s, (80, 80, 100),  cx, cy + 6 + drift, 5)
    _c(s, (100, 100, 120), cx, cy + 1 + drift, 5)
    _c(s, (120, 120, 140), cx, cy - 4 + drift, 4)
    _c(s, wh, cx, cy - 9 + drift, 5)
    _c(s, (200, 200, 210), cx, cy - 9 + drift, 3)
    for i in range(3):
        _c(s, (60, 60, 80), cx - 6 - i, cy - 8 + i + drift, 1)
        _c(s, (60, 60, 80), cx + 6 + i, cy - 8 + i + drift, 1)
    orb_pulse = 1 + math.sin(T * 5) * 0.4
    _glow(s, col, cx, cy - 15 + drift, round(4 * orb_pulse))
    _c(s, _LL(col), cx, cy - 15 + drift, round(2 * orb_pulse))
    for i in range(10):
        a = T * 2 + i * _PI / 5
        r = 10 + math.sin(T * 3 + i * 0.5) * 2
        px, py = _orbit(cx, cy + drift, r, a)
        _c(s, col, px, py, 1)
    _c(s, (200, 50, 50), cx - 2, cy - 9 + drift, 1)
    _c(s, (200, 50, 50), cx + 2, cy - 9 + drift, 1)


# ── generic fallback ──────────────────────────────────────────────────────────
def draw_generic(s, x, y, col, t):
    T = t * 0.001; cx, cy = x + 16, y + 16
    pulse = 1 + math.sin(T * 3) * 0.2
    _glow(s, _D(col), cx, cy, round(9 * pulse))
    _glow(s, col,     cx, cy, round(7 * pulse))
    _c(s, _L(col, 60), cx, cy, round(4 * pulse))
    _c(s, (255, 255, 255), cx - 2, cy - 2, 2)
    _c(s, (0, 0, 0),       cx - 2, cy - 2, 1)
    _c(s, (255, 255, 255), cx + 2, cy - 2, 2)
    _c(s, (0, 0, 0),       cx + 2, cy - 2, 1)


# ── registry ──────────────────────────────────────────────────────────────────
ENEMY_SPRITE_FNS = {
    'rat':              draw_rat,
    'bat':              draw_bat,
    'centipede':        draw_centipede,
    'spider':           draw_spider,
    'slime':            draw_slime,
    'goblin':           draw_goblin,
    'blade_skeleton':   draw_blade_skeleton,
    'shield_skeleton':  draw_shield_skeleton,
    'archer_skeleton':  draw_archer_skeleton,
    'spear_skeleton':   draw_spear_skeleton,
    'skeleton':         draw_skeleton,
    'prisoner':         draw_prisoner,
    'zombie':           draw_zombie,
    'ghost':            draw_ghost,
    'ghoul':            draw_ghoul,
    'corpse_flower':    draw_corpse_flower,
    'jar_crawler':      draw_jar_crawler,
    'chest_mimic':      draw_chest_mimic,
    'chain_beast':      draw_chain_beast,
    'iron_cage':        draw_iron_cage,
    'rock_golem':       draw_rock_golem,
    'torturer':         draw_torturer,
    'whip_master':      draw_whip_master,
    'brand_man':        draw_brand_man,
    'executioner_nov':  draw_executioner_nov,
    'poison_sprite':    draw_poison_sprite,
    'bone_wizard':      draw_bone_wizard,
    'curse_mage':       draw_curse_mage,
    'illusionist':      draw_illusionist,
    'specter':          draw_specter,
    'shadow_stalker':   draw_shadow_stalker,
    'ambusher':         draw_ambusher,
    'assassin':         draw_assassin,
    'thief':            draw_thief,
    'bandit':           draw_bandit,
    'giant_spider':     draw_giant_spider,
    'giant_zombie':     draw_giant_zombie,
    'steel_knight':     draw_steel_knight,
    'death_mage':       draw_death_mage,
    'orc':              draw_orc,
    'mimic':            draw_mimic,
    'blood_bat':        draw_blood_bat,
    'soul_absorber':    draw_soul_absorber,
    'troll':            draw_troll,
    'grave_titan':      draw_grave_titan,
    'wizard':           draw_wizard,
    'jail_captain':     draw_jail_captain,
    'mace_knight':      draw_mace_knight,
    'stomp_exec':       draw_stomp_exec,
    'dragon':           draw_dragon,
    'dark_knight':      draw_dark_knight,
    'lich':             draw_lich,
}
