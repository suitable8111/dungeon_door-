"""P1 게임 통합 스모크 — 실제 Game(마을) + 루프백 가짜 피어.

검증
----
1. Game이 마을에서 멀티플레이 세션을 시작한다(start_net_session).
2. 가짜 원격 피어가 자기 상태를 브로드캐스트하면 Game.net.remote_players에 등장.
3. 원격이 이동하면 Game이 보는 원격 좌표가 따라온다.
4. Game._render()가 원격 아바타를 마을 화면에 그려도 크래시 없다(PNG 저장).

성공 시 "GAME NET SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net import loopback_pair, Session  # noqa: E402
from net import protocol as P  # noqa: E402

import tempfile  # noqa: E402
OUT = os.path.join(tempfile.gettempdir(), "net_game_smoke.png")


def run() -> bool:
    game = Game()
    game.start_town_test(1, char_class="axeman")
    assert game._in_town, "마을 진입 실패"
    px, py = game.player.x, game.player.y
    print(f"[0] 마을 진입 OK  (플레이어 @ {(px, py)})")

    # 루프백: game=호스트, 가짜 친구=클라
    host_tp, client_tp = loopback_pair()
    game.start_net_session(host_tp, mode="town")

    # 가짜 원격 피어(마법사) — 플레이어 옆에 스폰, 자기 상태 broadcast
    rst = {"pos": [px + 2, py], "facing": "left", "walk": 0}

    def rprovider():
        return P.player_state(client_tp.local_id(), rst["pos"][0], rst["pos"][1],
                              rst["facing"], rst["walk"], "mage", "친구", {},
                              hp=22, max_hp=22)

    friend = Session(client_tp, char_class="mage", name="친구", mode="town",
                     local_player_state=rprovider, state_interval=2)
    friend.start()

    dt = 16.0
    # 상호 인식
    for _ in range(8):
        game.net.tick(dt); friend.tick(dt)
    cpid = client_tp.local_id()
    assert cpid in game.net.remote_players, \
        f"Game이 원격 친구를 못 봄: {list(game.net.remote_players)}"
    print(f"[1] Game이 원격 친구 인식 OK  (pid={cpid}, 클래스={game.net.remote_players[cpid].char_class})")

    # 친구가 왼쪽으로 3칸 이동
    for _ in range(3):
        rst["pos"][0] -= 1
        rst["facing"] = "left"
        rst["walk"] ^= 1
        for _ in range(20):
            game.net.tick(dt); friend.tick(dt)
    rp = game.net.remote_players[cpid]
    assert rp.x == px - 1, f"원격 이동 동기 실패: {rp.x} != {px - 1}"
    print(f"[2] 원격 이동 동기 OK  (친구 x {px+2}→{rp.x})")

    # 렌더 — 원격이 마을 화면에 그려지는지
    game._render()
    surf = game._game_surf if hasattr(game, "_game_surf") else game.screen
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(surf, OUT)
    print(f"[3] 마을 렌더 OK  (원격 {len(game.net.remote_players)}명) -> {os.path.relpath(OUT)}")
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("GAME NET SMOKE FAIL:", e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("GAME NET SMOKE ERROR:", e)
        sys.exit(2)
    print("GAME NET SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
