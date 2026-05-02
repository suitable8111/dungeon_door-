import pygame

# 첫 입력 후 연속 이동 시작까지 대기 시간 (ms)
MOVE_INITIAL_DELAY = 220
# 연속 이동 간격 (ms)
MOVE_REPEAT_RATE   = 90
# 두 WASD 키가 이 시간 이내에 눌리면 조합으로 처리 (ms)
_COMBO_WINDOW_MS = 150


class InputHandler:
    # 이동: 방향키 + 숫자패드만 사용 (WASD 제거)
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
        pygame.K_l, pygame.K_u,
    }
    # WASD → 스킬 키 문자
    _WASD = {
        pygame.K_w: 'W', pygame.K_a: 'A',
        pygame.K_s: 'S', pygame.K_d: 'D',
    }
    # 조합 쌍 → 조합 ID
    _COMBO_PAIRS = {
        frozenset({'W', 'S'}): 'WS',   # 파이어볼
        frozenset({'A', 'D'}): 'AD',   # 천둥격
        frozenset({'W', 'A'}): 'WA',   # 냉기 폭발
        frozenset({'W', 'D'}): 'WD',   # 바람 칼날
    }

    def __init__(self):
        self._prev_single     = set()
        self._held_key        = None
        self._move_timer      = 0.0
        # WASD 조합 감지 상태
        self._wasd_prev       = set()   # 이전 프레임에 눌린 WASD 문자 집합
        self._wasd_press_time = {}      # char -> 최초 눌린 시각(ms)
        self._wasd_fired      = set()   # 이미 단일/조합으로 처리된 문자

    def update(self, dt_ms):
        """매 프레임 호출. 발생한 액션 리스트를 반환."""
        keys    = pygame.key.get_pressed()
        actions = []
        now     = pygame.time.get_ticks()

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
                actions.append({'type': 'restart'})
            elif k == pygame.K_l:
                actions.append({'type': 'load'})
            elif k == pygame.K_u:
                actions.append({'type': 'skill_upgrade'})
            elif k == pygame.K_ESCAPE:
                actions.append({'type': 'escape'})

        # ── WASD 조합 / 단일 스킬 감지 ──────────────────────────────
        wasd_curr          = {char for k, char in self._WASD.items() if keys[k]}
        wasd_just_pressed  = wasd_curr - self._wasd_prev
        wasd_just_released = self._wasd_prev - wasd_curr

        # 새로 눌린 키: 시각 기록 + 조합 감지
        for char in wasd_just_pressed:
            self._wasd_press_time[char] = now
            if char in self._wasd_fired:
                continue
            # 현재 눌린 다른 WASD 키와 조합 여부 확인
            for other in (wasd_curr - {char}):
                if other in self._wasd_fired:
                    continue
                if now - self._wasd_press_time.get(other, 0) <= _COMBO_WINDOW_MS:
                    pair = frozenset({char, other})
                    if pair in self._COMBO_PAIRS:
                        actions.append({'type': 'combo_skill',
                                        'combo': self._COMBO_PAIRS[pair]})
                        self._wasd_fired.add(char)
                        self._wasd_fired.add(other)
                        break

        # 조합 창(150ms)을 넘긴 키 → 단일 스킬로 처리
        for char in wasd_curr:
            if char not in self._wasd_fired:
                if now - self._wasd_press_time.get(char, now) > _COMBO_WINDOW_MS:
                    actions.append({'type': 'skill', 'skill': char})
                    self._wasd_fired.add(char)

        # 떼어진 키: 아직 미처리라면 단일 스킬로 즉시 처리
        for char in wasd_just_released:
            if char not in self._wasd_fired:
                actions.append({'type': 'skill', 'skill': char})
            self._wasd_press_time.pop(char, None)
            self._wasd_fired.discard(char)

        self._wasd_prev = wasd_curr

        # ── 이동 (방향키 꾹 누름 지원) ────────────────────────────────
        active = None
        for k, vec in self._MOVE.items():
            if keys[k]:
                active = (k, vec)
                break

        if active:
            k, (dx, dy) = active
            if self._held_key != k:
                self._held_key   = k
                self._move_timer = MOVE_INITIAL_DELAY
                actions.append({'type': 'move', 'dx': dx, 'dy': dy})
            else:
                self._move_timer -= dt_ms
                if self._move_timer <= 0:
                    self._move_timer += MOVE_REPEAT_RATE
                    actions.append({'type': 'move', 'dx': dx, 'dy': dy})
        else:
            self._held_key   = None
            self._move_timer = 0.0

        return actions
