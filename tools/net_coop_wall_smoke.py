"""P3 균열 벽(bomb 벽) 동기화 검증 — 실제 Game 두 개 루프백.

1. 호스트가 균열 벽을 부수면 → 클라 맵에서도 통로가 된다(런타임 타일 동기).
2. 클라가 던진 폭탄 → 호스트가 권위 시뮬 → 벽 파괴 → 양쪽 통로가 된다.

성공 시 "COOP WALL SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net import loopback_pair  # noqa: E402
from map.tile import Tile, TileType  # noqa: E402


def pump(a, b, n=14):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def set_cracked(g, x, y):
    g.dungeon.tiles[y][x] = Tile.cracked_wall()


def is_floor(g, x, y):
    return g.dungeon.tiles[y][x].tile_type != TileType.CRACKED_WALL and \
        not g.dungeon.tiles[y][x].blocked


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = 4; client.floor = 4
    pump(host, client, 6)
    host._coop_begin_dungeon()
    pump(host, client, 8)
    px, py = host.player.x, host.player.y
    print("[0] co-op 던전 입장 OK")

    # ── 1) 호스트가 벽 파괴 → 클라 통로화 ──
    ax, ay = px + 3, py
    set_cracked(host, ax, ay); set_cracked(client, ax, ay)
    assert not is_floor(client, ax, ay), "사전 조건: 클라에 벽 있어야"
    host._break_cracked_walls_near(ax, ay, 0)     # 호스트 파괴 + 브로드캐스트
    assert is_floor(host, ax, ay), "호스트 벽 미파괴"
    pump(host, client)
    assert is_floor(client, ax, ay), "클라 맵에 벽 파괴 미반영"
    print(f"[1] 호스트 벽 파괴 → 클라 통로화 OK  ({ax},{ay})")

    # ── 2) 클라 폭탄 → 호스트 권위 파괴 → 양쪽 통로화 ──
    bx, by = px - 3, py
    set_cracked(host, bx, by); set_cracked(client, bx, by)
    client.net.send_world_action({'kind': 'bomb', 'x': bx, 'y': by, 'r': 1})
    pump(client, host)                            # 호스트가 폭탄 스폰
    assert any(b['x'] == bx and b['y'] == by for b in host._bombs), "호스트 폭탄 미스폰"
    host._update_bombs(700)                       # 도화선 만료 → 폭발 → 벽 파괴+브로드캐스트
    assert is_floor(host, bx, by), "호스트 벽 미파괴(폭탄)"
    pump(host, client)
    assert is_floor(client, bx, by), "클라 벽 미파괴(폭탄)"
    print(f"[2] 클라 폭탄 → 호스트 권위 파괴 → 양쪽 통로화 OK  ({bx},{by})")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP WALL SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP WALL SMOKE ERROR:", e); sys.exit(2)
    print("COOP WALL SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
