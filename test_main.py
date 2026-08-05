"""테스트 실행: python3 test_main.py [층수] [클래스]  (기본값: 1층 전사)
클래스:         warrior | archer   (예: python3 test_main.py 3 archer)
버닝 스테이지:  python3 test_main.py bunning [클래스]
마을:           python3 test_main.py town [복귀할 층수] [클래스]
정복 일지:      python3 test_main.py journal [클래스]   (샘플 일지 + 마을 시작)

멀티플레이(마을 co-op · 로컬/LAN 직접접속):
  호스트:  python3 test_main.py mp-host [클래스]
  참가:    python3 test_main.py mp-join [호스트IP] [클래스]   (IP 생략 시 127.0.0.1)
  → 창 두 개를 띄워 같은 마을을 함께 돌아다닌다. (Steam 불필요)
  같은 PC 테스트: 한 터미널에 mp-host, 다른 터미널에 mp-join
  다른 PC(같은 공유기): 참가 측이 호스트 PC의 LAN IP를 넣는다.

정복 일지/정산 디버그 키 (테스트 모드 전용, 기록은 *_test.json 격리):
  J = 정복 일지 열기/닫기
  [ = 현재 층 테마 클리어 +1
  ] = 999 마스터 정산(칭호·종결무기·NG+) 강제 발동
  \\ = 테스트 기록 초기화
  또는 python3 test_main.py 999 로 간 뒤 던전 문을 밟으면 실제 클리어로 정산.
"""
import sys

try:
    import pygame
except ImportError:
    print("pygame-ce를 먼저 설치해주세요:  pip install pygame-ce")
    sys.exit(1)

from core.game import Game


def _pop_class(args):
    """인자 목록에서 warrior/archer(또는 w/a)를 골라 제거하고 반환."""
    cls = 'warrior'
    _short = {'w': 'warrior', 'a': 'archer', 'm': 'mage', 'x': 'axeman'}
    for a in list(args):
        low = a.lower()
        if low in ('warrior', 'archer', 'mage', 'axeman'):
            cls = low; args.remove(a)
        elif low in _short:
            cls = _short[low]; args.remove(a)
    return cls

pygame.init()
game = Game()

args = sys.argv[1:]
char_class = _pop_class(args)
arg1 = args[0].lower() if args else ''

if arg1 == 'bunning':
    game.start_burning_mode(char_class=char_class)
elif arg1 == 'journal':
    game.start_journal_test(char_class=char_class)
elif arg1 == 'town':
    TEST_FLOOR = int(args[1]) if len(args) > 1 else 1
    game.start_town_test(TEST_FLOOR, char_class=char_class)
elif arg1 == 'mp-host':
    from net.socket_transport import SocketTransport, DEFAULT_PORT
    # 리슨을 먼저 열어 로딩 중에도 클라 접속을 받는다(수신은 백그라운드 스레드).
    tp = SocketTransport.host(port=DEFAULT_PORT)
    print(f"[MP] 호스트 리슨 시작 — 포트 {DEFAULT_PORT} (로딩 중에도 접속 가능)")
    game.start_town_test(1, char_class=char_class)
    game.start_net_session(tp, mode='town')
    print(f"[MP] 호스트 준비 완료 — 포트 {DEFAULT_PORT}")
    print(f"[MP] 같은 PC: 다른 터미널에서  python3 test_main.py mp-join")
    print(f"[MP] 다른 PC(같은 공유기): 참가 측이 이 PC의 LAN IP를 넣으세요")
elif arg1 == 'mp-join':
    from net.socket_transport import SocketTransport, DEFAULT_PORT
    ip = args[1] if len(args) > 1 else '127.0.0.1'
    game.start_town_test(1, char_class=char_class)
    try:
        tp = SocketTransport.connect(ip, DEFAULT_PORT, timeout=10.0)
    except OSError as e:
        print(f"[MP] 접속 실패({ip}:{DEFAULT_PORT}) — 호스트를 먼저 실행했는지 확인: {e}")
        sys.exit(1)
    game.start_net_session(tp, mode='town')
    print(f"[MP] {ip} 접속 완료 — 같은 마을에서 만나요")
else:
    TEST_FLOOR = int(args[0]) if args else 1
    game.start_test_mode(TEST_FLOOR, char_class=char_class)

game.run()
pygame.quit()
