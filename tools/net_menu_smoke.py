"""메뉴 → co-op 시작 흐름 검증 (헤드리스).

1. 호스트: _pending_net 설정 후 _maybe_begin_coop() → 마을 진입 + 세션 부착.
2. 참가: 실제 리슨 호스트에 _begin_join() 스레드 접속 → _mp_poll_connect()가
   _pending_net을 'join'으로 전이.

save_load는 test 데이터로 격리(use_test_data)해 실제 세이브를 건드리지 않는다.
성공 시 "MENU NET SMOKE OK" + exit 0.
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
from net import loopback_pair  # noqa: E402
from net.socket_transport import SocketTransport, DEFAULT_PORT  # noqa: E402


def run() -> bool:
    # ── 1) 호스트 coop-begin: 캐릭터 선택 직후 마을 진입 + 세션 부착 ──
    game = Game()
    game.start_test_mode(1, char_class="axeman")   # 던전(마을 아님), test 격리
    assert not game._in_town, "테스트 시작이 이미 마을?"
    host_tp, client_tp = loopback_pair()
    game._pending_net = ("host", host_tp)
    game._maybe_begin_coop()
    assert game._in_town, "coop 시작 후 마을 미진입"
    assert game.net is not None and game.net.is_host, "호스트 세션 미부착"
    assert game.net.tp is host_tp, "부착된 전송이 다름"
    assert game._pending_net is None and game._mp_mode_banner is None, "대기상태 미정리"
    print(f"[1] 호스트 coop-begin OK  (마을 진입 + 세션 부착, is_host={game.net.is_host})")

    # ── 2) 참가 접속 스레드: 실제 리슨 호스트에 붙는다 ──
    listen = SocketTransport.host(port=DEFAULT_PORT, bind="127.0.0.1")
    time.sleep(0.1)
    game2 = Game()
    game2._mp_ip = "127.0.0.1"
    game2._begin_join()          # 백그라운드 스레드 접속 시작
    assert game2._mp_connecting, "connecting 플래그 미설정"
    # 결과 폴링(런 루프의 _mp_poll_connect를 수동 구동)
    deadline = time.time() + 8.0
    while game2._mp_connecting and time.time() < deadline:
        game2._mp_poll_connect()
        time.sleep(0.05)
    assert game2._pending_net is not None, f"참가 접속 실패: status={game2._mp_status}"
    role, tp = game2._pending_net
    assert role == "join", f"role={role}"
    assert game2._mp_mode_banner == "join", "참가 배너 미설정"
    print(f"[2] 참가 접속 스레드 OK  (role={role}, 배너={game2._mp_mode_banner})")

    # ── 3) 취소 정리: 열어둔 전송을 닫는다 ──
    game2._cancel_pending_net()
    assert game2._pending_net is None, "취소 후 대기 미정리"
    print("[3] 참가 취소 정리 OK")

    listen.close(); host_tp.close(); client_tp.close(); tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("MENU NET SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("MENU NET SMOKE ERROR:", e); sys.exit(2)
    print("MENU NET SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
