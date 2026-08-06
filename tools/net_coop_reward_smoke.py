"""P3 골드/경험치 공유 검증 — 호스트 처치 보상이 파티원 전원에게.

호스트가 적을 처치하면 골드·경험치를 'reward'로 브로드캐스트 → 클라도 전액 획득.

성공 시 "COOP REWARD SMOKE OK" + exit 0.
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


def pump(a, b, n=14):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = 4; client.floor = 4
    pump(host, client, 6)
    host._coop_begin_dungeon()
    pump(host, client, 8)

    e = next((x for x in host.dungeon.enemies
              if not x.is_prop and not x.is_boss and not x.flee), None)
    assert e is not None, "일반 적 없음"
    e.gold_drop = 25
    e.xp_value = 40
    client.player.gold = 100
    cli_gold0 = client.player.gold
    cli_lv0, cli_xp0 = client.player.level, client.player.xp
    print(f"[0] co-op 던전 OK  (클라 gold={cli_gold0}, lv={cli_lv0})")

    # ── 호스트가 처치 → 보상 브로드캐스트 ──
    host._hurt_enemy(e, 999999)   # 즉사 → _on_enemy_killed → reward 이벤트
    pump(host, client)

    assert client.player.gold > cli_gold0, \
        f"클라 골드 미공유: {client.player.gold} (이전 {cli_gold0})"
    changed = (client.player.level != cli_lv0) or (client.player.xp != cli_xp0)
    assert changed, "클라 경험치 미공유(레벨/xp 변화 없음)"
    print(f"[1] 골드 공유 OK  (클라 gold {cli_gold0}→{client.player.gold})")
    print(f"[2] 경험치 공유 OK  (클라 lv {cli_lv0}→{client.player.level}, xp {cli_xp0}→{client.player.xp})")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP REWARD SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP REWARD SMOKE ERROR:", e); sys.exit(2)
    print("COOP REWARD SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
