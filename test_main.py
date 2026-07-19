"""테스트 실행: python3 test_main.py [층수] [클래스]  (기본값: 1층 전사)
클래스:         warrior | archer   (예: python3 test_main.py 3 archer)
버닝 스테이지:  python3 test_main.py bunning [클래스]
마을:           python3 test_main.py town [복귀할 층수] [클래스]
정복 일지:      python3 test_main.py journal [클래스]   (샘플 일지 + 마을 시작)

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
    _short = {'w': 'warrior', 'a': 'archer', 'm': 'mage'}
    for a in list(args):
        low = a.lower()
        if low in ('warrior', 'archer', 'mage'):
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
else:
    TEST_FLOOR = int(args[0]) if args else 1
    game.start_test_mode(TEST_FLOOR, char_class=char_class)

game.run()
pygame.quit()
