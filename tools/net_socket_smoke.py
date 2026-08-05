"""SocketTransport 헤드리스 검증 — 실제 TCP(localhost) 위 마을 모델.

loopback(메모리 큐)과 달리 진짜 소켓 프레이밍·핸드셰이크·수신 스레드를 탄다.
두 SocketTransport를 localhost로 잇고, 마을 모델로 서로 이동을 동기화한다.

성공 시 "SOCKET SMOKE OK" + exit 0.
"""

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((320, 240))

from net.socket_transport import SocketTransport  # noqa: E402
from net import Session, protocol as P  # noqa: E402

PORT = 47850


def make_peer(tp, cls, name, x, y):
    st = {"pos": [x, y], "facing": "down", "walk": 0}

    def provider():
        return P.player_state(tp.local_id(), st["pos"][0], st["pos"][1],
                              st["facing"], st["walk"], cls, name, {}, 30, 30)
    sess = Session(tp, char_class=cls, name=name, mode="town",
                   local_player_state=provider, state_interval=2)
    return sess, st


def run() -> bool:
    host_tp = SocketTransport.host(port=PORT, bind="127.0.0.1")
    time.sleep(0.1)
    client_tp = SocketTransport.connect("127.0.0.1", PORT, timeout=5.0)
    time.sleep(0.2)  # accept/수신 스레드 정착
    print(f"[0] 접속 OK  (호스트 id={host_tp.local_id()}, 클라 id={client_tp.local_id()})")
    assert client_tp.local_id() != host_tp.local_id(), "id 충돌"

    host, hst = make_peer(host_tp, "axeman", "HOST", 10, 10)
    client, cst = make_peer(client_tp, "mage", "GUEST", 20, 20)
    host.start(); client.start()

    # 상호 인식
    for _ in range(10):
        host.tick(); client.tick(dt=16.0)
        time.sleep(0.005)
    hpid, cpid = host_tp.local_id(), client_tp.local_id()
    assert cpid in host.remote_players, f"호스트가 클라 못 봄: {list(host.remote_players)}"
    assert hpid in client.remote_players, f"클라가 호스트 못 봄: {list(client.remote_players)}"
    print("[1] 상호 인식 OK")

    # 클라가 위로 5칸 이동 → 호스트가 보는 위치 동기
    for _ in range(5):
        cst["pos"][1] -= 1
        cst["facing"] = "up"
        for _ in range(12):
            host.tick(); client.tick(dt=16.0)
            time.sleep(0.004)
    rp = host.remote_players[cpid]
    assert (rp.x, rp.y) == (20, 15), f"위치 동기 실패: {(rp.x, rp.y)}"
    assert rp.facing == "up", f"facing={rp.facing}"
    print(f"[2] TCP 이동 동기 OK  (클라 y 20→{rp.y})")

    host_tp.close(); client_tp.close()
    print("[3] 정리 OK")
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("SOCKET SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("SOCKET SMOKE ERROR:", e); sys.exit(2)
    print("SOCKET SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
