"""P0 넷코드 스모크 테스트 — Steam 없이 헤드리스 루프백 검증.

검증 항목
--------
1. loopback_pair로 호스트/클라 전송이 배선된다.
2. 클라 접속(HELLO) → 호스트가 원격 플레이어를 등록한다.
3. 클라가 이동 인텐트를 보내면 호스트 권위 상태가 갱신된다.
4. 호스트 스냅샷 → 클라의 RemotePlayer 뷰가 호스트 위치를 따라온다.
5. 양쪽 RemotePlayer를 SDL dummy 서피스에 실제로 렌더해도 크래시가 없다.

성공하면 "NET SMOKE OK" 출력 + exit 0.
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


def _walkable(x, y):
    # 0..40 정사각 방. 벽 밖으로 못 나감.
    return 0 <= x < 40 and 0 <= y < 40


def run() -> bool:
    host_tp, client_tp = loopback_pair()

    # 호스트 권위(던전) 모델 검증: 호스트가 모든 상태의 권위.
    host = Session(host_tp, char_class="axeman", name="HOST", mode="dungeon",
                   walkable=_walkable, spawn=(10, 10), snapshot_interval=2)
    # 클라: 마법사, 접속 시 호스트 옆에 스폰됨
    client = Session(client_tp, char_class="mage", name="GUEST", mode="dungeon",
                     walkable=_walkable, spawn=(0, 0))

    host.start()
    client.start()

    # 1) 첫 틱: 클라 HELLO 도착 → 호스트가 원격 등록
    host.tick(); client.tick()
    peers = host_tp.peers()
    assert peers == [client_tp.local_id()], f"peers={peers}"
    assert host.authoritative_state(client_tp.local_id()) is not None, "원격 미등록"
    print(f"[1] 클라 접속·등록 OK  (호스트 권위 플레이어 수={len(host._authoritative)})")

    # 2) 클라가 오른쪽으로 5칸 이동 인텐트 전송
    guest_start = dict(host.authoritative_state(client_tp.local_id()))
    for _ in range(5):
        client.send_action({"type": "move", "dx": 1, "dy": 0})
        host.tick(); client.tick()
    guest_now = host.authoritative_state(client_tp.local_id())
    moved = guest_now["x"] - guest_start["x"]
    assert moved == 5, f"클라 이동 반영 실패: {guest_start['x']}→{guest_now['x']}"
    assert guest_now["f"] == "right", f"facing={guest_now['f']}"
    print(f"[2] 클라 이동 권위 반영 OK  (x {guest_start['x']}→{guest_now['x']}, facing={guest_now['f']})")

    # 3) 호스트가 아래로 3칸 이동 → 클라 RemotePlayer 뷰가 따라오는지
    host_start_y = host.local_state()["y"]
    for _ in range(3):
        host.send_action({"type": "move", "dx": 0, "dy": 1})
        # 스냅샷 여러 번 왕복 + 보간 수렴
        for _ in range(30):
            host.tick(); client.tick(dt=16.0)
    hpid = host_tp.local_id()
    rp = client.remote_players.get(hpid)
    assert rp is not None, "클라가 호스트를 RemotePlayer로 못 봄"
    assert rp.y == host_start_y + 3, f"호스트 타일 위치 동기 실패: {rp.y} != {host_start_y+3}"
    # 보간 픽셀이 목표 타일에 수렴했는지
    assert abs(rp.render_py - rp.y * TILE_SIZE) < 1.0, \
        f"보간 미수렴: render_py={rp.render_py} target={rp.y*TILE_SIZE}"
    print(f"[3] 호스트→클라 스냅샷 동기 OK  (호스트 y={rp.y}, 보간 render_py={rp.render_py:.1f})")

    # 4) 채팅 왕복
    client.send_action  # noop ref
    host.send_chat("환영합니다!")
    host.tick(); client.tick()
    assert any("환영" in m for _, m in client.chat_log), f"채팅 미수신: {client.chat_log}"
    print(f"[4] 채팅 브로드캐스트 OK  ({client.chat_log[-1]})")

    # 5) 실제 렌더 — 양쪽 RemotePlayer를 서피스에 그려 크래시 없는지
    surf = pygame.Surface((800, 608), pygame.SRCALPHA)
    cam_x, cam_y = 0, 0
    for rp in client.remote_players.values():
        rp.draw(surf, cam_x, cam_y)
    for rp in host.remote_players.values():
        rp.draw(surf, cam_x, cam_y)
    # 호스트 쪽 원격(=클라)도 있어야 실제 게임 통합 시 상호 가시성 보장
    print(f"[5] 렌더 OK  (클라가 보는 원격 {len(client.remote_players)}명, "
          f"호스트가 보는 원격 {len(host.remote_players)}명)")

    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("SMOKE FAIL:", e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("SMOKE ERROR:", e)
        sys.exit(2)
    print("NET SMOKE OK" if ok else "NET SMOKE INCOMPLETE")
    sys.exit(0 if ok else 3)
