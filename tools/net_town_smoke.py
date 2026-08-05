"""마을 co-op 모델(대칭 상태 브로드캐스트) 헤드리스 검증.

던전 모델(net_smoke.py)과 달리, 여기서는 두 피어가 각자 '자기' 플레이어를
독립적으로 움직이고 주기적으로 브로드캐스트한다. 각 피어는 상대를 RemotePlayer로
렌더한다 — 자기 아바타엔 예측/보정이 필요 없어 지터가 없다.

검증
----
1. 두 피어가 서로를 원격 플레이어로 인식한다(양방향).
2. 각자 독립 이동 → 상대 화면의 원격 좌표가 따라온다.
3. 보간 픽셀이 목표 타일에 수렴한다.
4. 실제 렌더(SDL dummy)에서 크래시 없다.

성공 시 "TOWN SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((320, 240))

from core.constants import TILE_SIZE  # noqa: E402
from net import loopback_pair, Session  # noqa: E402
from net import protocol as P  # noqa: E402


def make_peer(tp, cls, name, x, y):
    """가변 로컬 상태를 들고, provider로 그 상태를 노출하는 피어."""
    st = {"pos": [x, y], "facing": "down", "walk": 0}

    def provider():
        return P.player_state(tp.local_id(), st["pos"][0], st["pos"][1],
                              st["facing"], st["walk"], cls, name, {},
                              hp=30, max_hp=30)

    sess = Session(tp, char_class=cls, name=name, mode="town",
                   local_player_state=provider, spawn=(x, y), state_interval=2)
    return sess, st


def move(st, dx, dy):
    st["pos"][0] += dx
    st["pos"][1] += dy
    st["facing"] = {(1, 0): "right", (-1, 0): "left",
                    (0, 1): "down", (0, -1): "up"}[(dx, dy)]
    st["walk"] ^= 1


def run() -> bool:
    host_tp, client_tp = loopback_pair()
    host, hst = make_peer(host_tp, "axeman", "HOST", 10, 10)
    client, cst = make_peer(client_tp, "mage", "GUEST", 20, 20)
    host.start(); client.start()

    # 몇 틱 왕복 → 서로 인식
    for _ in range(6):
        host.tick(); client.tick(dt=16.0)
    hpid, cpid = host_tp.local_id(), client_tp.local_id()
    assert cpid in host.remote_players, "호스트가 클라를 못 봄"
    assert hpid in client.remote_players, "클라가 호스트를 못 봄"
    print(f"[1] 상호 인식 OK  (호스트↔클라 원격 등록)")

    # 각자 독립 이동: 호스트 오른쪽 4, 클라 위쪽 3
    for _ in range(4):
        move(hst, 1, 0)
        for _ in range(20):
            host.tick(); client.tick(dt=16.0)
    for _ in range(3):
        move(cst, 0, -1)
        for _ in range(20):
            host.tick(); client.tick(dt=16.0)

    # 클라가 보는 호스트 위치
    rp_h = client.remote_players[hpid]
    assert (rp_h.x, rp_h.y) == (14, 10), f"호스트 위치 동기 실패: {(rp_h.x, rp_h.y)}"
    assert rp_h.facing == "right", f"facing={rp_h.facing}"
    # 호스트가 보는 클라 위치
    rp_c = host.remote_players[cpid]
    assert (rp_c.x, rp_c.y) == (20, 17), f"클라 위치 동기 실패: {(rp_c.x, rp_c.y)}"
    print(f"[2] 양방향 독립 이동 동기 OK  (호스트→{(rp_h.x, rp_h.y)}, 클라→{(rp_c.x, rp_c.y)})")

    # 정지 후 정착(settle): 인게임에선 이동을 멈추면 원격 아바타가 목표 타일로 수렴
    for _ in range(40):
        host.tick(); client.tick(dt=16.0)

    # 보간 수렴
    assert abs(rp_h.render_px - rp_h.x * TILE_SIZE) < 1.0, "호스트 보간 미수렴"
    assert abs(rp_c.render_py - rp_c.y * TILE_SIZE) < 1.0, "클라 보간 미수렴"
    print(f"[3] 보간 수렴 OK  (render_px={rp_h.render_px:.1f}={rp_h.x*TILE_SIZE})")

    # 실제 렌더
    surf = pygame.Surface((800, 608), pygame.SRCALPHA)
    for rp in client.remote_players.values():
        rp.draw(surf, 0, 0)
    for rp in host.remote_players.values():
        rp.draw(surf, 0, 0)
    print(f"[4] 렌더 OK")
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("TOWN SMOKE FAIL:", e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("TOWN SMOKE ERROR:", e)
        sys.exit(2)
    print("TOWN SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
