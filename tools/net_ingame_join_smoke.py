"""게임 중(마을) 코드 참가 검증 — 실제 소켓으로 붙어 즉시 세션 부착.

호스트가 마을에서 세션 중일 때, 조이너가 게임 중 '친구 참가'로 코드를 입력해
캐릭터 선택 없이 바로 마을 co-op에 합류한다.

성공 시 "INGAME JOIN SMOKE OK" + exit 0.
"""

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net.socket_transport import SocketTransport, DEFAULT_PORT  # noqa: E402
from net.invite import make_code  # noqa: E402


def run() -> bool:
    # 호스트: 마을에서 세션 시작
    host = Game(); host.start_town_test(1, char_class="axeman")
    htp = SocketTransport.host(port=DEFAULT_PORT, bind="127.0.0.1")
    time.sleep(0.1)
    host.start_net_session(htp, mode="town")
    assert host.net is not None and host.net.is_host
    print("[0] 호스트 마을 세션 OK")

    # 조이너: 마을 싱글 → 게임 중 코드 참가
    joiner = Game(); joiner.start_town_test(1, char_class="mage")
    assert joiner.net is None and joiner._in_town
    joiner._open_ingame_join()
    assert joiner._mp_join_open, "참가 입력 미개방"
    # 코드 렌더 크래시 없음
    joiner._mp_ip = make_code("127.0.0.1", DEFAULT_PORT)
    joiner._render()
    joiner._mp_join_start()        # 코드 파싱 → 접속 스레드
    assert not joiner._mp_join_open and joiner._mp_connecting and joiner._mp_join_ingame
    print("[1] 코드 입력 → 접속 시작 OK")

    # 접속 완료까지 폴링(호스트는 accept)
    deadline = time.time() + 8.0
    while joiner._mp_connecting and time.time() < deadline:
        host.net.tick()
        joiner._mp_poll_connect()
        time.sleep(0.03)
    assert joiner.net is not None and not joiner.net.is_host, "조이너 세션 미부착"
    print("[2] 게임 중 참가 → 세션 부착 OK (캐릭터 선택 없이)")

    # 상호 인식
    for _ in range(12):
        host.net.tick(); joiner.net.tick(); time.sleep(0.005)
    hpid, jpid = htp.local_id(), joiner.net.tp.local_id()
    assert jpid in host.net.remote_players, "호스트가 조이너 못 봄"
    assert hpid in joiner.net.remote_players, "조이너가 호스트 못 봄"
    print(f"[3] 상호 인식 OK  (호스트↔조이너)")

    htp.close(); joiner.net.tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("INGAME JOIN SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("INGAME JOIN SMOKE ERROR:", e); sys.exit(2)
    print("INGAME JOIN SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
