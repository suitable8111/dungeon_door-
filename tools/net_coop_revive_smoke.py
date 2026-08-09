"""협동 다운/부활/관전 + 파티 전멸 + 협동 퀘스트 + 도전과제 검증.

두 Game을 루프백으로 연결해 co-op 던전에 넣고:
 1. 호스트가 치명타로 '다운' → 클라가 원격에서 상태 1(다운) 인식
 2. 클라가 인접해 부활 채널 완료 → 호스트 부활(HP 40%)
 3. 다운 타임아웃 → 관전 전환 → 다음 층 하강 시 부활 복구
 4. 파티 전원 다운 → 전멸(게임오버)
 5. 협동 퀘스트(coop_kill/revive/floor) 진행·보고 + 보상
 6. 도전과제 정의/카운터 임계 동작(임시 매니저)

성공 시 "COOP REVIVE SMOKE OK" + exit 0.
"""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

from core.game import Game  # noqa: E402
from net import loopback_pair  # noqa: E402


def pump(a, b, n=10):
    for _ in range(n):
        a.net.tick(); b.net.tick()


def make_pair(floor=3):
    host = Game(); host.start_town_test(1, char_class="axeman")
    client = Game(); client.start_town_test(1, char_class="mage")
    h, c = loopback_pair()
    host.start_net_session(h, mode="town"); client.start_net_session(c, mode="town")
    host.floor = floor; client.floor = floor
    pump(host, client, 6)
    host._coop_begin_dungeon()
    pump(host, client, 8)
    return host, client, h, c


class _FakeEnemy:
    def __init__(self, key='slime', is_boss=False, elite=False):
        self.key = key; self.is_boss = is_boss; self.elite = elite


def run() -> bool:
    host, client, h, c = make_pair(3)
    assert host._coop_dungeon and client._coop_dungeon, "co-op 입장 실패"
    hpid = h.local_id()
    assert hpid in client.net.remote_players, "클라가 호스트 미인식"
    print("[0] co-op 던전 입장 OK")

    # ── 1) 호스트 다운 → 클라가 상태 1 인식 ──
    host.player.hp = 0
    host._enter_downed()
    assert host._downed and not host._spectating, "다운 상태 아님"
    pump(host, client)
    rp = client.net.remote_players[hpid]
    assert rp.status == 1, f"클라가 다운 인식 실패(status={rp.status})"
    print("[1] 호스트 다운 → 클라 상태 전파 OK")

    # ── 2) 클라 인접 → 부활 채널 완료 → 호스트 부활 ──
    client.player.x = rp.x + 1
    client.player.y = rp.y
    # 진행도 부분 채우기(1틱) → 링 표시 확인
    client._coop_downed_tick(500)
    assert 0 < rp.revive_prog < 1, f"부활 진행도 이상({rp.revive_prog})"
    # 완료까지 채널
    client._coop_downed_tick(client._REVIVE_MS)
    pump(host, client)
    assert not host._downed and not host._spectating, "호스트 부활 실패"
    assert host.player.hp == max(1, int(host.player.max_hp * host._REVIVE_FRAC)), \
        f"부활 HP 이상({host.player.hp}/{host.player.max_hp})"
    print(f"[2] 인접 부활 OK  (HP {host.player.hp}/{host.player.max_hp})")

    # ── 3) 다운 타임아웃 → 관전, 하강 시 복구 ──
    host.player.hp = 0
    host._enter_downed()
    host._coop_downed_tick(host._DOWN_MS + 100)   # 블리드아웃 소진
    assert host._spectating and not host._downed, "관전 전환 실패"
    pump(host, client)
    assert client.net.remote_players[hpid].status == 2, "관전 상태 미전파"
    host._coop_start(host.floor + 1, 123456, host._coop_diff)  # 다음 층 하강
    assert not host._spectating and host.player.hp > 0, "하강 부활 복구 실패"
    print("[3] 관전 → 하강 부활 복구 OK")

    # ── 4) 파티 전멸(전원 다운) → 게임오버 ──
    # 클라를 다운시켜 브로드캐스트, 호스트도 다운 → 전멸 판정
    client.player.hp = 0; client._enter_downed()
    pump(host, client)
    host.player.hp = 0; host._enter_downed()
    host._coop_downed_tick(16)   # 전멸 체크
    assert host.state == 'dead', f"전멸 게임오버 실패(state={host.state})"
    print("[4] 파티 전멸 → 게임오버 OK")

    h.close(); c.close()

    # ── 5) 협동 퀘스트 진행·보고 ──
    host2, client2, h2, c2 = make_pair(3)
    from core.coop_quests import COOP_QUESTS
    # party_hunt(coop_kill 50) 수락 → 50킬 → done → 보고
    host2._coop_quests['party_hunt']['state'] = 'active'
    for _ in range(COOP_QUESTS['party_hunt']['count']):
        host2._coop_quest_on_kill(_FakeEnemy())
    assert host2._coop_quests['party_hunt']['state'] == 'done', "party_hunt 미완료"
    g0 = host2.player.gold
    host2._claim_coop_quest('party_hunt')
    assert host2._coop_quests['party_hunt']['state'] == 'claimed', "보고 실패"
    assert host2.player.gold == g0 + COOP_QUESTS['party_hunt']['reward']['gold'], "보상 골드 미지급"
    # brotherhood(coop_revive 3) — 이제 언락됨
    from core.coop_quests import current_quest
    assert current_quest(host2._coop_quests) == 'brotherhood', "체인 언락 실패"
    host2._coop_quests['brotherhood']['state'] = 'active'
    for _ in range(3):
        host2._coop_quest_on_revive()
    assert host2._coop_quests['brotherhood']['state'] == 'done', "brotherhood 미완료"
    # deep_bond(coop_floor 5) — 층 하강 추적
    host2._coop_quests['brotherhood']['state'] = 'claimed'
    host2._coop_quests['deep_bond']['state'] = 'active'
    host2._coop_quest_on_floor(5)
    assert host2._coop_quests['deep_bond']['state'] == 'done', "deep_bond 미완료(층)"
    print("[5] 협동 퀘스트(킬/부활/하강) 진행·보고 OK")
    h2.close(); c2.close()

    # ── 6) 도전과제 정의 + 카운터 임계 ──
    from core.achievements import AchievementManager, ACHIEVEMENTS
    for k in ('ACH_COOP_KILLS_100', 'ACH_REVIVE', 'ACH_REVIVE_10',
              'ACH_COOP_1H', 'ACH_COOP_3H', 'ACH_COOP_5H',
              'ACH_COOP_QUEST', 'ACH_COOP_BOSS'):
        assert k in ACHIEVEMENTS, f"업적 정의 누락: {k}"
    tmp = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    tmp.write('{}'); tmp.close()
    import core.achievements as A
    _orig = A.ACH_PATH
    A.ACH_PATH = tmp.name
    try:
        got = []
        am = AchievementManager(on_unlock=lambda n: got.append(n))
        am.add_stat('coop_secs', 3600)     # → 1H
        am.add_stat('coop_secs', 7200)     # 누적 10800 → 3H
        am.add_stat('revives', 10)         # → REVIVE_10
        am.add_stat('coop_kills', 100)     # → KILLS_100
        assert 'ACH_COOP_1H' in got and 'ACH_COOP_3H' in got, "시간 업적 미달성"
        assert 'ACH_REVIVE_10' in got and 'ACH_COOP_KILLS_100' in got, "카운터 업적 미달성"
    finally:
        A.ACH_PATH = _orig
        os.unlink(tmp.name)
    print("[6] 도전과제 정의 + 카운터 임계 OK")

    # 렌더 크래시 없음(다운 오버레이 포함)
    host3, client3, h3, c3 = make_pair(3)
    host3.player.hp = 0; host3._enter_downed()
    pump(host3, client3)
    client3._render(); host3._render()
    h3.close(); c3.close()
    print("[7] 다운 오버레이 렌더 OK")
    return True


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("COOP REVIVE SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("COOP REVIVE SMOKE ERROR:", e); sys.exit(2)
    print("COOP REVIVE SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
