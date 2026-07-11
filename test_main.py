"""테스트 실행: python3 test_main.py [층수]  (기본값: 1층)
버닝 스테이지:  python3 test_main.py bunning
마을:           python3 test_main.py town [복귀할 층수]
"""
import sys

try:
    import pygame
except ImportError:
    print("pygame-ce를 먼저 설치해주세요:  pip install pygame-ce")
    sys.exit(1)

from core.game import Game

pygame.init()
game = Game()

arg1 = sys.argv[1].lower() if len(sys.argv) > 1 else ''
if arg1 == 'bunning':
    game.start_burning_mode()
elif arg1 == 'town':
    TEST_FLOOR = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    game.start_town_test(TEST_FLOOR)
else:
    TEST_FLOOR = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    game.start_test_mode(TEST_FLOOR)

game.run()
pygame.quit()
