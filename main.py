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

    # 테스트 모드: python3 main.py -test [층수]
    test_floor = None
    args = sys.argv[1:]
    if '-test' in args:
        idx = args.index('-test')
        test_floor = 1
        if idx + 1 < len(args):
            try:
                test_floor = int(args[idx + 1])
            except ValueError:
                pass

    game = Game()
    if test_floor is not None:
        game._test_floor = test_floor  # 메뉴에 디버그 버튼 표시
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
