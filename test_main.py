"""테스트 실행: python3 test_main.py [층수] [클래스]  (기본값: 1층 전사)
클래스:         warrior | archer   (예: python3 test_main.py 3 archer)
버닝 스테이지:  python3 test_main.py bunning [클래스]
마을:           python3 test_main.py town [복귀할 층수] [클래스]
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
    for a in list(args):
        low = a.lower()
        if low in ('warrior', 'archer'):
            cls = low; args.remove(a)
        elif low in ('w', 'a'):
            cls = 'warrior' if low == 'w' else 'archer'; args.remove(a)
    return cls

pygame.init()
game = Game()

args = sys.argv[1:]
char_class = _pop_class(args)
arg1 = args[0].lower() if args else ''

if arg1 == 'bunning':
    game.start_burning_mode(char_class=char_class)
elif arg1 == 'town':
    TEST_FLOOR = int(args[1]) if len(args) > 1 else 1
    game.start_town_test(TEST_FLOOR, char_class=char_class)
else:
    TEST_FLOOR = int(args[0]) if args else 1
    game.start_test_mode(TEST_FLOOR, char_class=char_class)

game.run()
pygame.quit()
