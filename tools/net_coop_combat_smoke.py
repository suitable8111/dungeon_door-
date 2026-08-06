"""P3 co-op 전투 검증 — 클라 공격(피해 인텐트) + 멀티 보스 강화.

1. 클라가 적을 때리면 → 호스트 권위 HP가 깎임(클라는 로컬 HP 변경 안 함).
2. 클라가 적을 처치하면 → 호스트에서 제거 → 클라도 제거.
3. 멀티 보스는 일반 배수(2인 체력×1.6) 위에 추가 배수(×1.5)로 더 단단함.

성공 시 "COOP COMBAT SMOKE OK" + exit 0.
"""

import os
import sys
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net import loopback_pair  # noqa: E402
from map.generator import generate_dungeon  # noqa: E402
from core.constants import MAP_WIDTH, MAP_HEIGHT  # noqa: E402


def pump(a, b, n=14):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def eid(g, nid):
    return next((e for e in g.dungeon.enemies if getattr(e, 'net_id', None) == nid), None)


def make_pair(hfloor, cfloor):
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = hfloor; client.floor = cfloor
    pump(host, client, 6)
    host._coop_begin_dungeon()
    pump(host, client, 8)
    return host, client, h, c


def run() -> bool:
    host, client, h, c = make_pair(4, 4)
    assert host._coop_dungeon and client._coop_dungeon
    nid0 = host.dungeon.enemies[0].net_id
    print(f"[0] co-op 던전 입장 OK  (적 {len(host.dungeon.enemies)})")

    # ── 1) 클라 공격 → 호스트 HP 감소 ──
    he = eid(host, nid0)
    ce = eid(client, nid0)
    hp0 = he.hp
    ce.take_damage(7)         # 클라 경로(래핑됨) → 인텐트 전송
    assert ce.hp == hp0, "클라가 로컬 HP를 바꿈(권위 위반)"
    pump(client, host)
    assert he.hp == hp0 - 7, f"호스트 HP 미반영: {he.hp} != {hp0-7}"
    print(f"[1] 클라 공격 → 호스트 권위 HP 감소 OK  ({hp0}→{he.hp})")

    # ── 2) 클라가 처치 → 양쪽 제거 ──
    ce.take_damage(99999)
    pump(client, host)
    assert eid(host, nid0) is None, "호스트에서 미처치"
    pump(host, client)
    assert eid(client, nid0) is None, "클라에서 미제거"
    print("[2] 클라 처치 → 호스트 권위 처리 → 양쪽 제거 OK")

    h.close(); c.close()

    # ── 3) 멀티 보스 추가 강화 (보스층 5) ──
    host2, client2, h2, c2 = make_pair(5, 5)
    boss = host2.dungeon.boss
    assert boss is not None and getattr(boss, 'is_boss', False), "보스층에 보스 없음"
    seed = host2._coop_seed
    random.seed(seed)
    ref, _ = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, 5,
                              host2._enemy_data, host2._item_data)
    random.seed()
    rboss = ref.boss
    expect = max(1, round(rboss.max_hp * 1.6 * host2._COOP_BOSS_HP))
    assert boss.max_hp == expect, f"보스 강화 이상: {boss.max_hp} != {expect} (기본 {rboss.max_hp})"
    # 일반 적과 비교해 보스 배수가 더 큰지
    print(f"[3] 멀티 보스 강화 OK  (기본 {rboss.max_hp} → co-op {boss.max_hp}, "
          f"일반×1.6 위 보스×{host2._COOP_BOSS_HP})")

    h2.close(); c2.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP COMBAT SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP COMBAT SMOKE ERROR:", e); sys.exit(2)
    print("COOP COMBAT SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
