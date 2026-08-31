"""테스트 실행: python3 test_main.py [층수] [클래스]  (기본값: 1층 전사)
클래스:         warrior | archer | mage | axeman  (또는 w/a/m/x)
2차 전직 테스트: 전직 id 또는 <직업>1/<직업>2 로 Lv40 전직 상태로 바로 시작
  예) python3 test_main.py 10 dual_blade   (=warrior2 / w2 도 동일)
      python3 test_main.py 10 a1  (석궁마스터) · m2 (스피드마법사) · warrior1 (쌍검사)
  전직 id: dual_blade, magic_swordsman, crossbow_master, twin_bow, battle_mage, speed_mage
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
    """인자에서 직업/전직을 골라 제거하고 (char_class, subclass) 반환.

    직업:   warrior/archer/mage/axeman  또는  w/a/m/x
    전직:   전직 id 직접(dual_blade 등)  또는  <직업>1/<직업>2 (예: warrior2, w2, a1)
            → 스폰 시 해당 전직 상태(Lv40) 로 시작 (Lv40 그라인딩 없이 테스트)
    """
    from core.subclasses import SUBCLASSES, SUBCLASS_CHOICES, base_of
    cls = 'warrior'
    subclass = None
    _short = {'w': 'warrior', 'a': 'archer', 'm': 'mage', 'x': 'axeman'}
    for a in list(args):
        low = a.lower()
        if low in ('warrior', 'archer', 'mage', 'axeman'):
            cls = low; args.remove(a)
        elif low in _short:
            cls = _short[low]; args.remove(a)
        elif low in SUBCLASSES:                       # 전직 id 직접
            subclass = low; cls = base_of(low); args.remove(a)
        elif len(low) >= 2 and low[-1] in '12':       # <직업>1/2, w1/a2 등
            base = _short.get(low[:-1], low[:-1])
            choices = SUBCLASS_CHOICES.get(base)
            if choices:
                cls = base; subclass = choices[int(low[-1]) - 1]; args.remove(a)
    return cls, subclass

pygame.init()
game = Game()

args = sys.argv[1:]
char_class, _subclass = _pop_class(args)
arg1 = args[0].lower() if args else ''

if arg1 == 'bunning':
    game.start_burning_mode(char_class=char_class)
elif arg1 == 'survival':
    game.start_survival_mode(char_class=char_class)
elif arg1 == 'journal':
    game.start_journal_test(char_class=char_class)
elif arg1 == 'town':
    TEST_FLOOR = int(args[1]) if len(args) > 1 else 1
    game.start_town_test(TEST_FLOOR, char_class=char_class)
elif arg1 == 'mp-host':
    from net.socket_transport import SocketTransport, DEFAULT_PORT
    from net.invite import make_code, local_ip
    from net.upnp import PortForward
    import atexit
    # 리슨을 먼저 열어 로딩 중에도 클라 접속을 받는다(수신은 백그라운드 스레드).
    tp = SocketTransport.host(port=DEFAULT_PORT)
    _lan = local_ip()
    print(f"[MP] 호스트 리슨 시작 — 포트 {DEFAULT_PORT}")
    print("[MP] UPnP 포트포워딩 시도 중…")
    _pf = PortForward(DEFAULT_PORT)
    try:
        _ext = _pf.setup(_lan)      # 공인 IP면 반환(인터넷 가능), 아니면 None
    except Exception:
        _ext = None
    atexit.register(_pf.close)       # 종료 시 포트 매핑 제거
    _code = make_code(_ext, DEFAULT_PORT) if _ext else make_code(_lan, DEFAULT_PORT)
    _where = "인터넷 어디서든" if _ext else f"같은 공유기만 (UPnP: {_pf.status})"
    print(f"[MP] 초대 코드({_where}): {_code}")
    print(f"[MP] 친구는  python3 test_main.py mp-join {_code}  로 접속")
    game.start_town_test(1, char_class=char_class)
    game.start_net_session(tp, mode='town')
    print(f"[MP] 호스트 준비 완료 — 포트 {DEFAULT_PORT}")
    print(f"[MP] 같은 PC: 다른 터미널에서  python3 test_main.py mp-join")
    print(f"[MP] 다른 PC(같은 공유기): 참가 측이 이 PC의 LAN IP를 넣으세요")
elif arg1 == 'mp-join':
    from net.socket_transport import SocketTransport, DEFAULT_PORT
    from net.invite import parse_code, looks_like_code
    arg = args[1] if len(args) > 1 else '127.0.0.1'
    if looks_like_code(arg):
        parsed = parse_code(arg)
        ip, port = parsed if parsed else (arg, DEFAULT_PORT)
    else:
        ip, port = arg, DEFAULT_PORT
    game.start_town_test(1, char_class=char_class)
    try:
        tp = SocketTransport.connect(ip, port, timeout=10.0)
    except OSError as e:
        print(f"[MP] 접속 실패({ip}:{port}) — 호스트를 먼저 실행했는지 확인: {e}")
        sys.exit(1)
    game.start_net_session(tp, mode='town')
    print(f"[MP] {ip} 접속 완료 — 같은 마을에서 만나요")
else:
    TEST_FLOOR = int(args[0]) if args else 1
    game.start_test_mode(TEST_FLOOR, char_class=char_class)

# 전직 지정 시: Lv40 + 즉시 전직 상태로 시작 (테스트용)
if _subclass and game.player is not None:
    from core.subclasses import apply_subclass, name_key
    from core.lang import t
    game.player.level = max(game.player.level, 40)
    if apply_subclass(game.player, _subclass):
        game._apply_subclass_equips()   # 전직 전용 W/A/S/D 스킬 장착(안 하면 기본 스킬 그대로 남음)
        print(f"[TEST] 전직 적용: {_subclass} ({t(name_key(_subclass))}) — Lv{game.player.level}")
        print(f"[TEST] 장착 스킬: {game._equipped_skills}")
    else:
        print(f"[TEST] 전직 실패: {_subclass} (base={game.player.char_class})")

game.run()
pygame.quit()
