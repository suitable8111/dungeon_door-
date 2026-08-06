"""P2 공유 밭 동기화 검증 — 실제 Game 두 개(호스트+클라) 루프백.

1. 호스트가 밭에 심으면 → 클라가 같은 작물을 본다.
2. 클라가 수확하면 → 호스트의 밭도 비워진다(호스트 권위).
   (보상은 액션한 플레이어에게 로컬 지급)

성공 시 "FARM SMOKE OK" + exit 0.
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


def pump(a, b, n=8):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    assert host._in_town and client._in_town, "마을 진입 실패"

    host_tp, client_tp = loopback_pair()
    host.start_net_session(host_tp, mode="town")
    client.start_net_session(client_tp, mode="town")
    assert host.net.is_host and not client.net.is_host
    print("[0] 호스트+클라 마을 세션 OK")

    # ── 1) 호스트 심기 → 클라 동기 ──
    host._farm_menu_plot = 0
    host._farm_do('plant')
    crop = host._town.farm[0].get('crop')
    assert crop is not None, "호스트 심기 실패"
    pump(host, client)
    assert client._town.farm[0].get('crop') == crop, \
        f"클라 미동기: {client._town.farm[0].get('crop')} != {crop}"
    print(f"[1] 호스트 심기 → 클라 동기 OK  (작물={crop})")

    # ── 2) 클라 수확 → 호스트 밭 비워짐 ──
    gold_before = client.player.gold
    client._farm_menu_plot = 0
    client._farm_do('harvest')
    assert client._town.farm[0].get('crop') is None, "클라 로컬 수확 반영 안됨"
    assert client.player.gold >= gold_before, "수확 보상(골드) 미지급"
    pump(client, host)
    assert host._town.farm[0].get('crop') is None, \
        f"호스트 밭 미동기(수확): {host._town.farm[0]}"
    print(f"[2] 클라 수확 → 호스트 동기 OK  (골드 {gold_before}→{client.player.gold})")

    # ── 3) 호스트 수확 보상은 호스트에게(권위측 직접) ──
    host._farm_menu_plot = 1
    host._farm_do('plant')
    pump(host, client)
    assert client._town.farm[1].get('crop') is not None, "클라가 두번째 심기 못 봄"
    print("[3] 두번째 밭도 동기 OK")

    # ── 4) 목장: 호스트가 닭 구매 → 클라 동기 ──
    host._ranch_menu_pen = 0
    host._ranch_do({'act': 'buy', 'animal': 'chicken', 'cost': 60})
    assert host._town.ranch[0].get('animal') == 'chicken', "호스트 구매 실패"
    pump(host, client)
    assert client._town.ranch[0].get('animal') == 'chicken', \
        f"클라 목장 미동기: {client._town.ranch[0]}"
    print("[4] 호스트 가축 구매 → 클라 동기 OK  (chicken)")

    # ── 5) 클라가 판매 → 호스트 펜 비워짐 ──
    client._ranch_menu_pen = 0
    client._ranch_do({'act': 'sell'})
    assert client._town.ranch[0].get('animal') is None, "클라 로컬 판매 반영 안됨"
    pump(client, host)
    assert host._town.ranch[0].get('animal') is None, \
        f"호스트 펜 미동기(판매): {host._town.ranch[0]}"
    print("[5] 클라 판매 → 호스트 동기 OK")

    host_tp.close(); client_tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("FARM SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("FARM SMOKE ERROR:", e); sys.exit(2)
    print("FARM SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
