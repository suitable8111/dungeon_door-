"""초대 코드 참가 경로 검증 — 실제 리슨 호스트에 코드로 접속.

1. make_code/parse_code 왕복(여러 IP).
2. Game._begin_join이 초대 코드를 파싱해 실제 소켓 접속에 성공.
3. 잘못된 코드는 badcode 상태로 거부.

성공 시 "INVITE SMOKE OK" + exit 0.
"""

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from net.invite import make_code, parse_code  # noqa: E402
from net.socket_transport import SocketTransport, DEFAULT_PORT  # noqa: E402
from core.game import Game  # noqa: E402


def run() -> bool:
    for ip, port in [("127.0.0.1", 47800), ("192.168.0.42", 47800),
                     ("10.0.0.1", 65535)]:
        assert parse_code(make_code(ip, port)) == (ip, port)
    print("[0] 코드 왕복 OK")

    # 실제 리슨 호스트
    listen = SocketTransport.host(port=DEFAULT_PORT, bind="127.0.0.1")
    time.sleep(0.1)

    g = Game()
    code = make_code("127.0.0.1", DEFAULT_PORT)
    g._mp_ip = code
    g._begin_join()               # 코드 파싱 → 접속 스레드 시작
    assert g._mp_connecting, "connecting 미설정"
    deadline = time.time() + 8.0
    while g._mp_connecting and time.time() < deadline:
        g._mp_poll_connect()
        time.sleep(0.05)
    assert g._pending_net is not None and g._pending_net[0] == "join", \
        f"코드 접속 실패: status={g._mp_status}"
    print(f"[1] 초대 코드 접속 OK  (code={code})")

    # 잘못된 코드
    g2 = Game()
    g2._mp_ip = "ZZZZZZZZZZZZZ"    # 체크섬 불일치
    g2._begin_join()
    assert not g2._mp_connecting and g2._mp_status is not None, "잘못된 코드 미거부"
    print(f"[2] 잘못된 코드 거부 OK  (status set)")

    listen.close()
    if g._pending_net:
        try:
            g._pending_net[1].close()
        except Exception:
            pass
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("INVITE SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("INVITE SMOKE ERROR:", e); sys.exit(2)
    print("INVITE SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
