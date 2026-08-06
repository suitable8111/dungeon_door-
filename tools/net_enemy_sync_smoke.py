"""P3 적 실시간 동기화 검증 — 실제 Game 두 개(호스트+클라) 루프백.

1. co-op 던전 입장 후 양쪽 적이 동일 net_id로 정렬.
2. 호스트가 적 위치/HP 변경 → 클라가 그대로 반영(호스트 권위).
3. 호스트에서 적 처치 → 클라에서도 제거.
4. 클라 적 AI 정지(로컬 시뮬 안 함).

성공 시 "ENEMY SYNC SMOKE OK" + exit 0.
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


def pump(a, b, n=14):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def enemy_by_id(g, nid):
    return next((e for e in g.dungeon.enemies if getattr(e, 'net_id', None) == nid), None)


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    host_tp, client_tp = loopback_pair()
    host.start_net_session(host_tp, mode="town")
    client.start_net_session(client_tp, mode="town")
    host.floor = 4; client.floor = 4
    pump(host, client, 6)

    host._coop_begin_dungeon()
    pump(host, client, 8)
    assert host._coop_dungeon and client._coop_dungeon, "co-op 던전 미진입"
    hn = [e.net_id for e in host.dungeon.enemies if getattr(e, 'net_id', None) is not None]
    cn = [e.net_id for e in client.dungeon.enemies if getattr(e, 'net_id', None) is not None]
    assert hn and hn == cn, f"net_id 정렬 불일치: {len(hn)} vs {len(cn)}"
    print(f"[0] co-op 던전 입장 + net_id 정렬 OK  (적 {len(hn)}마리)")

    # ── 1) 호스트가 적0 위치/HP 변경 → 클라 반영 ──
    e0 = enemy_by_id(host, hn[0])
    e0.x += 4; e0.hp = max(1, e0.hp - 3)
    tx, ty, thp = e0.x, e0.y, e0.hp
    pump(host, client)
    ce0 = enemy_by_id(client, hn[0])
    assert ce0 is not None, "클라에 적0 없음"
    assert (ce0.x, ce0.y, ce0.hp) == (tx, ty, thp), \
        f"적 상태 미동기: {(ce0.x, ce0.y, ce0.hp)} != {(tx, ty, thp)}"
    print(f"[1] 적 위치/HP 동기 OK  (호스트→클라: pos=({tx},{ty}) hp={thp})")

    # ── 2) 클라 적 AI 정지 확인 ──
    before = [(e.net_id, e.x, e.y) for e in client.dungeon.enemies]
    for _ in range(10):
        client._update_enemies(200)   # 클라에서 AI 돌려도 움직이면 안 됨
    after = [(e.net_id, e.x, e.y) for e in client.dungeon.enemies]
    assert before == after, "클라 적 AI가 로컬로 움직임(정지 실패)"
    print("[2] 클라 적 AI 정지 OK")

    # ── 3) 호스트에서 적 처치 → 클라 제거 ──
    victim = hn[1]
    ev = enemy_by_id(host, victim)
    host._hurt_enemy(ev, 99999)       # 중앙 처치 처리로 라우팅 → 제거
    assert enemy_by_id(host, victim) is None, "호스트에서 적 미제거"
    pump(host, client)
    assert enemy_by_id(client, victim) is None, "클라에서 처치된 적 미제거"
    print(f"[3] 호스트 처치 → 클라 제거 OK  (net_id={victim})")

    host_tp.close(); client_tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("ENEMY SYNC SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("ENEMY SYNC SMOKE ERROR:", e); sys.exit(2)
    print("ENEMY SYNC SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
