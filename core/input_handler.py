import pygame

# 첫 입력 후 연속 이동 시작까지 대기 시간 (ms)
MOVE_INITIAL_DELAY = 220
# 연속 이동 간격 (ms)
MOVE_REPEAT_RATE   = 90


class InputHandler:
    # 이동: key -> (dx, dy)
    _MOVE = {
        pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
        pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
        pygame.K_KP8: (0, -1),  pygame.K_KP2: (0, 1),
        pygame.K_KP4: (-1, 0),  pygame.K_KP6: (1, 0),
        pygame.K_KP7: (-1, -1), pygame.K_KP9: (1, -1),
        pygame.K_KP1: (-1,  1), pygame.K_KP3: (1,  1),
    }
    # 아이템 슬롯: key -> slot index
    _ITEM = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
    # 단일 입력 키 목록 (한 번 누름만 인식)
    _SINGLE_KEYS = {
        pygame.K_SPACE, pygame.K_PERIOD, pygame.K_KP5,
        pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
        pygame.K_r, pygame.K_ESCAPE, pygame.K_RETURN,
        pygame.K_q, pygame.K_e, pygame.K_f,   # 스킬
        pygame.K_l,                             # 불러오기 (메뉴)
    }

    def __init__(self):
        self._prev_single = set()   # 이전 프레임에 눌린 단일 키
        self._held_key    = None    # 현재 꾹 눌린 이동 키
        self._move_timer  = 0.0    # 연속 이동 타이머

    def update(self, dt_ms):
        """매 프레임 호출. 발생한 액션 리스트를 반환."""
        keys = pygame.key.get_pressed()
        actions = []

        # ── 단일 입력 감지 (IME 우회: get_pressed 사용) ─────────────────
        curr_single = {k for k in self._SINGLE_KEYS if keys[k]}
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
            elif k == pygame.K_q:
                actions.append({'type': 'skill', 'skill': 'Q'})
            elif k == pygame.K_e:
                actions.append({'type': 'skill', 'skill': 'E'})
            elif k == pygame.K_f:
                actions.append({'type': 'skill', 'skill': 'F'})
            elif k == pygame.K_r:
                actions.append({'type': 'restart'})
            elif k == pygame.K_l:
                actions.append({'type': 'load'})
            elif k == pygame.K_ESCAPE:
                actions.append({'type': 'escape'})

        # ── 이동 (꾹 누름 지원) ─────────────────────────────────────────
        active = None
        for k, vec in self._MOVE.items():
            if keys[k]:
                active = (k, vec)
                break   # 우선순위: 딕셔너리 삽입 순서

        if active:
            k, (dx, dy) = active
            if self._held_key != k:
                # 새 키: 즉시 이동 + 타이머 리셋
                self._held_key   = k
                self._move_timer = MOVE_INITIAL_DELAY
                actions.append({'type': 'move', 'dx': dx, 'dy': dy})
            else:
                # 같은 키 유지: 타이머 감소
                self._move_timer -= dt_ms
                if self._move_timer <= 0:
                    self._move_timer += MOVE_REPEAT_RATE
                    actions.append({'type': 'move', 'dx': dx, 'dy': dy})
        else:
            self._held_key   = None
            self._move_timer = 0.0

        return actions
