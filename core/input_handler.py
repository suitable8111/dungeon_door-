import pygame

# 첫 입력 후 연속 이동 시작까지 대기 시간 (ms) — move_speed=1.0 기준
MOVE_INITIAL_DELAY = 300
# 연속 이동 간격 (ms) — move_speed=1.0 기준 (Player.BASE_MOVE_REPEAT_MS 와 동기)
MOVE_REPEAT_RATE   = 220


class InputHandler:
    # 이동: 방향키 + 숫자패드만 사용
    _MOVE = {
        pygame.K_UP:    (0, -1),
        pygame.K_DOWN:  (0,  1),
        pygame.K_LEFT:  (-1, 0),
        pygame.K_RIGHT: (1,  0),
        pygame.K_KP8: (0, -1),  pygame.K_KP2: (0,  1),
        pygame.K_KP4: (-1, 0),  pygame.K_KP6: (1,  0),
        pygame.K_KP7: (-1, -1), pygame.K_KP9: (1, -1),
        pygame.K_KP1: (-1,  1), pygame.K_KP3: (1,  1),
    }
    _ITEM = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
    _SINGLE_KEYS = {
        pygame.K_SPACE, pygame.K_PERIOD, pygame.K_KP5,
        pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
        pygame.K_r, pygame.K_ESCAPE, pygame.K_RETURN,
        pygame.K_l, pygame.K_i, pygame.K_o,
    }
    # WASD → 스킬 키 문자
    _WASD = {
        pygame.K_w: 'W', pygame.K_a: 'A',
        pygame.K_s: 'S', pygame.K_d: 'D',
    }
    # Ctrl + WASD → 강화 스킬 (Ctrl+W=WA, Ctrl+A=AD, Ctrl+S=WS, Ctrl+D=WD)
    _CTRL_COMBO = {
        pygame.K_w: 'WA',
        pygame.K_a: 'AD',
        pygame.K_s: 'WS',
        pygame.K_d: 'WD',
    }

    def __init__(self):
        self._prev_single  = set()
        self._held_key     = None
        self._move_timer   = 0.0
        self._move_speed   = 1.0
        self._wasd_prev    = set()
        self._wasd_fired   = set()
        self._ctrl_prev    = set()  # Ctrl 조합 중복 방지

    def set_move_speed(self, speed: float):
        self._move_speed = max(0.5, float(speed))

    def update(self, dt_ms):
        """매 프레임 호출. 발생한 액션 리스트를 반환."""
        keys    = pygame.key.get_pressed()
        actions = []
        ctrl    = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # ── 단일 입력 감지 ────────────────────────────────────────────
        curr_single  = {k for k in self._SINGLE_KEYS if keys[k]}
        just_pressed = curr_single - self._prev_single
        self._prev_single = curr_single

        for k in just_pressed:
            if k == pygame.K_SPACE:
                actions.append({'type': 'attack'})
            elif k in (pygame.K_PERIOD, pygame.K_KP5):
                actions.append({'type': 'wait'})
            elif k == pygame.K_RETURN:
                actions.append({'type': 'confirm'})
            elif k in self._ITEM:
                actions.append({'type': 'use_item', 'slot': self._ITEM[k]})
            elif k == pygame.K_r:
                if ctrl:
                    actions.append({'type': 'ultimate', 'key': 'Ctrl_R'})
                else:
                    actions.append({'type': 'ultimate', 'key': 'R'})
            elif k == pygame.K_l:
                actions.append({'type': 'load'})
            elif k == pygame.K_i:
                actions.append({'type': 'inventory'})
            elif k == pygame.K_o:
                actions.append({'type': 'equipment'})
            elif k == pygame.K_ESCAPE:
                actions.append({'type': 'escape'})

        # ── Ctrl+WASD → 조합 스킬 ────────────────────────────────────
        ctrl_curr = {k for k in self._CTRL_COMBO if keys[k]} if ctrl else set()
        ctrl_just = ctrl_curr - self._ctrl_prev
        self._ctrl_prev = ctrl_curr
        for k in ctrl_just:
            actions.append({'type': 'combo_skill', 'combo': self._CTRL_COMBO[k]})

        # ── WASD 단일 스킬 (Ctrl 없을 때만) ──────────────────────────
        wasd_curr          = {char for k, char in self._WASD.items() if keys[k]}
        wasd_just_pressed  = wasd_curr - self._wasd_prev
        wasd_just_released = self._wasd_prev - wasd_curr

        if not ctrl:
            for char in wasd_just_pressed:
                if char not in self._wasd_fired:
                    actions.append({'type': 'skill', 'skill': char})
                    self._wasd_fired.add(char)

        for char in wasd_just_released:
            self._wasd_fired.discard(char)

        self._wasd_prev = wasd_curr

        # ── 이동 (방향키 꾹 누름 지원, 속도 연동) ────────────────────
        repeat_rate   = max(60, int(MOVE_REPEAT_RATE / self._move_speed))
        initial_delay = max(80, int(MOVE_INITIAL_DELAY / self._move_speed))

        active = None
        for k, vec in self._MOVE.items():
            if keys[k]:
                active = (k, vec)
                break

        if active:
            k, (dx, dy) = active
            if self._held_key != k:
                self._held_key   = k
                self._move_timer = initial_delay
                actions.append({'type': 'move', 'dx': dx, 'dy': dy})
            else:
                self._move_timer -= dt_ms
                if self._move_timer <= 0:
                    self._move_timer += repeat_rate
                    actions.append({'type': 'move', 'dx': dx, 'dy': dy})
        else:
            self._held_key   = None
            self._move_timer = 0.0

        return actions
