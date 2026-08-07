"""회귀: 스테일 씬 상태에서 이어하기-coop 시작.

버그: 마을/co-op던전에서 플레이하다 타이틀→멀티→이어하기로 co-op을 시작하면
같은 Game 인스턴스의 _in_town/_coop_dungeon가 True로 남아, _maybe_begin_coop이
_enter_town을 건너뛰어 던전+마을이 겹치고(렌더) 좌표가 어긋나 서로 안 보였다.
수정: _continue_game이 씬 상태를 초기화(_new_game과 동일).

성공 시 "COOP STALE SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.save_load import use_test_data, save_game  # noqa: E402
use_test_data(True)
from core.game import Game  # noqa: E402
from net import loopback_pair  # noqa: E402


def run() -> bool:
    # 세이브 하나 준비 (5층 마법사)
    g0 = Game(); g0._new_game(char_class="mage", slot=0)
    save_game(g0.player, 5, g0.skills, g0._unlocked_combos, g0._skill_books,
              g0._skill_levels, g0._skill_xp, g0._skill_points, g0._equipped_skills,
              g0._skill_enchants, g0._quests, 5, slot=0, name="TestMage",
              char_class="mage")

    htp, ctp = loopback_pair()
    # 스테일 상태 재현: 이전 세션이 마을/co-op던전이었던 것처럼
    g = Game()
    g._in_town = True
    g._coop_dungeon = True
    g._town = None
    g._pending_net = ("join", ctp)
    g._save_slot = 0
    g._continue_game(0)

    assert g._in_town is True, "마을 미진입"
    assert g.dungeon is (g._town.dungeon if g._town else None), \
        "던전+마을 겹침 (버그 재현!)"
    assert g._coop_dungeon is False, "co-op던전 스테일 미리셋"
    assert g.net is not None, "세션 미부착"
    assert (g.player.x, g.player.y) == g._town.spawn_pos, "마을 스폰 아님"
    print(f"[1] 스테일 이어하기-coop → 정상 마을 진입 OK  (pos={g._town.spawn_pos})")

    # new_game 경로도 여전히 OK
    g2 = Game()
    g2._in_town = True; g2._coop_dungeon = True
    g2._pending_net = ("host", htp)
    g2._new_game(char_class="axeman", slot=1)
    assert g2._in_town and g2.dungeon is g2._town.dungeon and not g2._coop_dungeon
    print("[2] 스테일 새게임-coop → 정상 마을 진입 OK")
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP STALE SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP STALE SMOKE ERROR:", e); sys.exit(2)
    print("COOP STALE SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
