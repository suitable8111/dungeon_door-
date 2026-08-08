"""파티원 공격/스킬 이펙트 공유 검증 — 실제 Game 두 개 루프백.

호스트가 공격하면 fx 이벤트 브로드캐스트 → 클라가 원격 아바타 공격 포즈 +
스윙/볼트 VFX를 재생.

성공 시 "FX SMOKE OK" + exit 0.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from core.animator import AttackSwingAnim, BoltAnim  # noqa: E402
from net import loopback_pair  # noqa: E402


def pump(a, b, n=6):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def run() -> bool:
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town")
    client.start_net_session(c, mode="town")
    pump(host, client)
    hpid = h.local_id()
    assert hpid in client.net.remote_players, "클라가 호스트 원격 미인식"
    print("[0] 세션 OK")

    # ── 1) 호스트 근접 공격 → 클라가 스윙 + 공격포즈 재생 ──
    n0 = len(client.animator._anims)
    host._facing = 'right'; host._atk_variant = 'slash1'
    host._trigger_atk_anim()            # fx 브로드캐스트
    pump(host, client)
    rp = client.net.remote_players[hpid]
    assert rp.atk_ms > 0, "원격 공격 포즈 미설정"
    assert rp.atk_facing == 'right', f"공격 방향={rp.atk_facing}"
    added = client.animator._anims[n0:]
    assert any(isinstance(a, AttackSwingAnim) for a in added), \
        f"근접 스윙 VFX 미재생: {[type(a).__name__ for a in added]}"
    print(f"[1] 근접 공격 공유 OK  (포즈+스윙, facing={rp.atk_facing})")

    # ── 2) 호스트 원거리(cast) → 볼트 재생 ──
    n1 = len(client.animator._anims)
    host._facing = 'up'; host._atk_variant = 'cast'
    host._trigger_atk_anim()
    pump(host, client)
    added2 = client.animator._anims[n1:]
    assert any(isinstance(a, BoltAnim) for a in added2), \
        f"원거리 볼트 VFX 미재생: {[type(a).__name__ for a in added2]}"
    print("[2] 원거리 공격 공유 OK  (볼트)")

    # ── 3) 포즈 감쇠 + 렌더 크래시 없음 ──
    for _ in range(30):
        rp.update(16)
    assert rp.atk_ms == 0, "공격 포즈 미감쇠"
    client._render(); host._render()
    print("[3] 포즈 감쇠 + 렌더 OK")

    h.close(); c.close()
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("FX SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("FX SMOKE ERROR:", e); sys.exit(2)
    print("FX SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
