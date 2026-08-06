"""마을 co-op 채팅 검증 — 실제 Game 두 개(호스트+클라) 루프백.

1. 호스트가 채팅 → 클라의 chat_log·말풍선·피드에 반영.
2. 클라가 채팅 → 호스트에 반영(호스트 중계 포함).
3. 채팅 오버레이/말풍선 렌더 크래시 없음.

성공 시 "CHAT SMOKE OK" + exit 0.
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
        a.net.tick(); a._pump_chat(); a._update_chat_timers(16)
        b.net.tick(); b._pump_chat(); b._update_chat_timers(16)


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    host_tp, client_tp = loopback_pair()
    host.start_net_session(host_tp, mode="town")
    client.start_net_session(client_tp, mode="town")
    # 서로 인식(원격 플레이어 등록 → 이름표시용)
    pump(host, client, 6)
    print("[0] 호스트+클라 세션 OK")

    # ── 1) 호스트 채팅 → 클라 반영 ──
    host.net.send_chat("안녕 친구!")
    pump(host, client)
    assert any("안녕" in txt for _, txt in client.net.chat_log), \
        f"클라 채팅 미수신: {client.net.chat_log}"
    hpid = host_tp.local_id()
    assert hpid in client._chat_bubbles, f"클라 말풍선 없음: {client._chat_bubbles}"
    assert any("안녕" in r[1] for r in client._chat_feed), "클라 피드 없음"
    print(f"[1] 호스트→클라 채팅 OK  (말풍선 pid={hpid}, 피드 {len(client._chat_feed)})")

    # ── 2) 클라 채팅 → 호스트 반영 ──
    client.net.send_chat("반가워요!")
    pump(client, host)
    assert any("반가" in txt for _, txt in host.net.chat_log), \
        f"호스트 채팅 미수신: {host.net.chat_log}"
    cpid = client_tp.local_id()
    assert cpid in host._chat_bubbles, "호스트 말풍선 없음"
    print(f"[2] 클라→호스트 채팅 OK  (말풍선 pid={cpid})")

    # ── 3) 렌더 크래시 없음 (말풍선 + 오버레이) ──
    host._chat_open = True; host._chat_text = "타이핑중"
    host._render()
    host._chat_open = False
    client._render()
    print("[3] 채팅 렌더 OK (말풍선·입력줄·피드)")

    host_tp.close(); client_tp.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("CHAT SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("CHAT SMOKE ERROR:", e); sys.exit(2)
    print("CHAT SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
