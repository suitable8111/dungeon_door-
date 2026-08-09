"""리더보드 코어(로컬 폴백) 검증 — Steam 불필요.

submit/최고기록유지/영속화/폴백조회 를 확인. 성공 시 "LEADERBOARD SMOKE OK".
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.leaderboards as L  # noqa: E402


def run() -> bool:
    tmp = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    tmp.write('{}'); tmp.close()
    L.LB_PATH = tmp.name
    try:
        lb = L.LeaderboardManager(player_name='Tester')
        assert lb._steam is None, "테스트 환경에 Steam 이 붙으면 안 됨"

        # 1) submit_run 이 전체+직업별+레벨 반영
        lb.submit_run(floor=210, level=34, char_class='mage')
        assert lb.best('best_floor') == 210
        assert lb.best('best_floor_mage') == 210
        assert lb.best('best_floor_warrior') == 0
        assert lb.best('best_level') == 34
        print("[1] submit_run 전체/직업별/레벨 반영 OK")

        # 2) 최고기록만 유지(낮은 점수 무시, 높은 점수 갱신)
        assert lb.submit('best_floor', 150) is False and lb.best('best_floor') == 210
        assert lb.submit('best_floor', 640) is True and lb.best('best_floor') == 640
        print("[2] 최고기록 유지 OK")

        # 3) 영속화 왕복
        lb._save()
        lb2 = L.LeaderboardManager(player_name='Tester')
        assert lb2.best('best_floor') == 640 and lb2.best('best_floor_mage') == 210
        print("[3] 영속화 왕복 OK")

        # 4) 폴백 조회 = 내 기록 1줄
        entries = lb2.get_entries('best_floor', mode='global', count=20)
        assert len(entries) == 1 and entries[0]['me'] and entries[0]['score'] == 640
        assert lb2.get_entries('best_floor_archer')  == []   # 기록 없으면 빈 리스트
        print("[4] 로컬 폴백 조회 OK")

        # 5) 정의/직업 리더보드 존재
        for c in ('warrior', 'archer', 'mage'):
            assert f'best_floor_{c}' in L.LEADERBOARDS
        print("[5] 직업별 리더보드 정의 OK")
        return True
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    ok = False
    try:
        ok = run()
    except AssertionError as e:
        print("LEADERBOARD SMOKE FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        import traceback; traceback.print_exc(); print("ERROR:", e); sys.exit(2)
    print("LEADERBOARD SMOKE OK" if ok else "INCOMPLETE")
    sys.exit(0 if ok else 3)
