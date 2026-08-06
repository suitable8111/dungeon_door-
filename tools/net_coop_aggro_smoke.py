"""P3 적 어그로 검증 — 적이 클라 파티원도 노리고, 클라가 피해를 받는다.

호스트 적 AI가 가장 가까운 파티원을 타겟. 클라가 적 옆에 있고 호스트는 멀면
적이 클라를 공격 → 호스트가 'hit' 이벤트로 클라에 통보 → 클라 HP 감소.
(호스트는 안 맞음)

성공 시 "AGGRO SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net import loopback_pair  # noqa: E402


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="warrior")  # 회피 0
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = 4; client.floor = 4
    for _ in range(6):
        host.net.tick(); client.net.tick()
    host._coop_begin_dungeon()
    for _ in range(8):
        host.net.tick(); client.net.tick()

    # 공격 가능한 적 하나 선택
    e0 = next((e for e in host.dungeon.enemies
               if not e.is_prop and not e.flee and getattr(e, 'net_id', None) is not None), None)
    assert e0 is not None, "공격형 적 없음"

    # 클라를 적 옆에, 호스트는 멀리 배치
    client.player.x, client.player.y = e0.x + 1, e0.y
    host.player.x, host.player.y = e0.x + 25, e0.y
    e0.aware_range = 999
    host_hp0 = host.player.hp
    cli_hp0 = client.player.hp
    print(f"[0] 배치 OK  (적@({e0.x},{e0.y}), 클라 인접, 호스트 멀리)")

    # 여러 프레임 구동 — 적이 클라를 반복 공격
    for _ in range(50):
        client.net.tick()          # 클라 위치 브로드캐스트
        host.net.tick()            # 호스트가 클라 위치 수신
        e0._attack_t = -1          # 공격 쿨다운 강제 해제(반복 공격)
        e0._move_t = -1
        e0.staggered_ms = 0
        e0._pending_skill = None
        host._update_enemies(300)  # 호스트 AI: 클라 타겟 → 'hit' 전송
        client.net.tick()          # 클라가 'hit' 수신 → HP 감소

    assert client.player.hp < cli_hp0, \
        f"클라가 피해를 안 받음: {client.player.hp} (초기 {cli_hp0})"
    assert host.player.hp == host_hp0, \
        f"멀리 있는 호스트가 맞음: {host.player.hp} != {host_hp0}"
    print(f"[1] 적 어그로→클라 피해 OK  (클라 HP {cli_hp0}→{client.player.hp}, 호스트 무피해)")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("AGGRO SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("AGGRO SMOKE ERROR:", e); sys.exit(2)
    print("AGGRO SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
