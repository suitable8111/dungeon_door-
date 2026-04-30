import sys

try:
    import pygame
except ImportError:
    print("pygame-ce를 먼저 설치해주세요:")
    print("  pip install pygame-ce")
    sys.exit(1)

from core.game import Game


def main():
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
