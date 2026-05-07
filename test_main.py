"""테스트 실행: python3 test_main.py [층수]  (기본값: 1층)"""
import sys

try:
    import pygame
except ImportError:
    print("pygame-ce를 먼저 설치해주세요:  pip install pygame-ce")
    sys.exit(1)

from core.game import Game

TEST_FLOOR = int(sys.argv[1]) if len(sys.argv) > 1 else 1

pygame.init()
game = Game()
game.start_test_mode(TEST_FLOOR)
game.run()
pygame.quit()
