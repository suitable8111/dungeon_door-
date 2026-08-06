"""P3 전리품 동기화 + 획득 검증 — 실제 Game 두 개 루프백.

1. 호스트 바닥 아이템 → 클라에도 보임(동일 net_id/종류).
2. 클라가 획득 → 호스트 권위로 바닥에서 제거 + 그 클라 인벤에 지급.
3. 중복 방지: 호스트는 그 아이템을 얻지 않음.

성공 시 "COOP LOOT SMOKE OK" + exit 0.
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
from entities.item import Item  # noqa: E402


def pump(a, b, n=16):
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
    print("[0] co-op 던전 입장 OK")

    # ── 1) 호스트에 아이템 드랍 → 클라 반영 ──
    key = 'health_potion'
    d = dict(host._item_data[key]); d['key'] = key
    drop = Item(host.player.x + 1, host.player.y, d)
    host.dungeon.items.append(drop)
    pump(host, client)
    cit = next((it for it in client.dungeon.items
                if getattr(it, 'net_id', None) == drop.net_id), None)
    assert cit is not None, f"클라에 아이템 미동기: {[getattr(i,'net_id',None) for i in client.dungeon.items]}"
    assert cit.key == key, f"종류 불일치: {cit.key}"
    print(f"[1] 바닥 아이템 동기 OK  (net_id={drop.net_id}, {key})")

    # ── 2) 클라 획득 → 호스트 권위 제거 + 클라 인벤 지급 ──
    inv0 = len(client.player.inventory)
    host_inv0 = len(host.player.inventory)
    client._pickup(cit)              # 클라 경로 → 획득 요청
    assert len(client.player.inventory) == inv0, "클라가 승인 전 로컬 획득함"
    pump(client, host)               # 요청→호스트 처리→grant→클라 지급
    assert len(client.player.inventory) == inv0 + 1, \
        f"클라 인벤 미지급: {len(client.player.inventory)} != {inv0+1}"
    assert not any(getattr(it, 'net_id', None) == drop.net_id
                   for it in host.dungeon.items), "호스트 바닥에서 미제거"
    print(f"[2] 클라 획득 OK  (인벤 {inv0}→{len(client.player.inventory)})")

    # ── 3) 중복 방지: 호스트는 얻지 않음 ──
    assert len(host.player.inventory) == host_inv0, "호스트가 중복 획득함"
    pump(host, client)
    assert not any(getattr(it, 'net_id', None) == drop.net_id
                   for it in client.dungeon.items), "클라 바닥에서 미제거"
    print("[3] 중복 방지 OK  (호스트 미획득, 양쪽 바닥 제거)")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP LOOT SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP LOOT SMOKE ERROR:", e); sys.exit(2)
    print("COOP LOOT SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
