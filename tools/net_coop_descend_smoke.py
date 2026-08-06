"""P3 co-op 하강 버그 회귀 — 던전→다음 던전이 호스트 주도로 동기, 크래시 없음.

버그: 클라가 독립적으로 다음 층 재생성 → 호스트 스냅샷이 안 맞는 적에 hp 덮어씀
→ ratio 범위 초과로 draw_hp_bar 색 크래시.
수정: 하강도 coop_enter로 호스트 주도(같은 시드) + draw_hp_bar 클램프.

성공 시 "COOP DESCEND SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game, draw_hp_bar  # noqa: E402
from net import loopback_pair  # noqa: E402


def pump(a, b, n=14):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = 4; client.floor = 4
    pump(host, client, 6)
    host._coop_begin_dungeon()
    pump(host, client, 8)
    assert host.floor == 4 and client.floor == 4
    print("[0] co-op 던전 4층 입장 OK")

    # ── 호스트 하강 → 둘 다 5층 동시 생성 ──
    host._coop_descend()
    pump(host, client, 12)
    assert host.floor == 5 and client.floor == 5, \
        f"하강 층 불일치: host={host.floor} client={client.floor}"
    assert host._coop_seed == client._coop_seed, "하강 시드 불일치"
    ht = [[t.tile_type for t in row] for row in host.dungeon.tiles]
    ct = [[t.tile_type for t in row] for row in client.dungeon.tiles]
    assert ht == ct, "하강 후 맵 불일치"
    print(f"[1] 호스트 주도 하강 OK  (둘 다 5층, 맵 동일, seed={host._coop_seed})")

    # ── 적 HP 무결성(버그 재현 방지) ──
    bad = [(e.hp, e.max_hp) for e in client.dungeon.enemies
           if not (0 <= e.hp <= e.max_hp)]
    assert not bad, f"클라 적 HP 손상: {bad[:3]}"
    print(f"[2] 클라 적 HP 무결성 OK  ({len(client.dungeon.enemies)}마리 0<=hp<=max)")

    # ── 렌더 크래시 없음(원래 크래시 지점) ──
    client._render(); host._render()
    # draw_hp_bar 방어: hp>max_hp여도 크래시 안 함
    surf = pygame.Surface((64, 64))
    draw_hp_bar(surf, 0, 0, 9999, 30)   # ratio>1 케이스
    draw_hp_bar(surf, 0, 0, -5, 30)     # 음수 케이스
    print("[3] 렌더/draw_hp_bar 클램프 OK (크래시 없음)")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP DESCEND SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP DESCEND SMOKE ERROR:", e); sys.exit(2)
    print("COOP DESCEND SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
