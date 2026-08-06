"""P3 던전 co-op 입장 검증 — 실제 Game 두 개(호스트+클라) 루프백.

요구사항 검증:
1. 파티 최저 층으로 입장 (host floor=8, client floor=3 → 둘 다 3층).
2. 같은 시드 → 양쪽 던전 맵(타일)이 완전히 동일 (맵 전송 없이 결정론적 생성).
3. 적 난이도가 싱글보다 강함 (2인 → 체력×1.6, 공격력×1.3).

(적 실시간 이동 동기화는 다음 단계 — 여기서는 입장·맵·난이도 기반만 검증)
성공 시 "COOP DUNGEON SMOKE OK" + exit 0.
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


def pump(a, b, n=8):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    host_tp, client_tp = loopback_pair()
    host.start_net_session(host_tp, mode="town")
    client.start_net_session(client_tp, mode="town")

    # 서로 다른 탐험 층 설정
    host.floor = 8
    client.floor = 3
    pump(host, client, 8)   # 층 정보가 player_state로 교환됨
    cpid = client_tp.local_id()
    assert host.net.remote_players[cpid].floor == 3, \
        f"호스트가 클라 층 못 봄: {host.net.remote_players[cpid].floor}"
    print("[0] 파티 층 정보 교환 OK  (host=8, client=3)")

    # ── 1) 호스트가 던전 입장 개시 → 최저 층(3)으로 ──
    host._coop_begin_dungeon()
    pump(host, client, 6)   # coop_enter 이벤트 전달
    assert host._coop_dungeon and client._coop_dungeon, "co-op 던전 플래그 미설정"
    assert host.floor == 3 and client.floor == 3, \
        f"최저 층 아님: host={host.floor} client={client.floor}"
    assert host._coop_seed == client._coop_seed, \
        f"시드 불일치: {host._coop_seed} != {client._coop_seed}"
    print(f"[1] 최저 층 입장 OK  (둘 다 3층, seed={host._coop_seed})")

    # ── 2) 같은 시드 → 맵 타일 완전 동일 ──
    ht = [[t.tile_type for t in row] for row in host.dungeon.tiles]
    ct = [[t.tile_type for t in row] for row in client.dungeon.tiles]
    assert ht == ct, "던전 타일이 양쪽 불일치(결정론적 생성 실패)"
    print(f"[2] 맵 동일 OK  ({MAP_WIDTH}x{MAP_HEIGHT} 타일 전부 일치)")

    # ── 3) 난이도: 적 체력·공격력이 싱글 기준보다 강함 ──
    seed = host._coop_seed
    random.seed(seed)
    ref, _ = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, 3,
                              host._enemy_data, host._item_data)
    random.seed()
    # 호스트 던전의 생성 적(앞쪽 N개)이 참조 대비 강화됐는지
    diff = host._coop_diff
    assert diff and diff['hp'] == 1.6 and diff['atk'] == 1.3, f"난이도 배수 이상: {diff}"
    checked = 0
    for he, re in zip(host.dungeon.enemies, ref.enemies):
        if getattr(re, 'key', re.name) == getattr(he, 'key', he.name):
            assert he.max_hp == max(1, round(re.max_hp * 1.6)), \
                f"체력 강화 안됨: {he.max_hp} vs {re.max_hp}"
            checked += 1
        if checked >= 5:
            break
    assert checked >= 1, "비교한 적이 없음"
    print(f"[3] 난이도 강화 OK  (체력×{diff['hp']}, 공격×{diff['atk']}, {checked}마리 확인)")

    host_tp.close(); client_tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP DUNGEON SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP DUNGEON SMOKE ERROR:", e); sys.exit(2)
    print("COOP DUNGEON SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
