"""mp-host / mp-join CLI 경로 검증 — 실제 두 프로세스를 띄운다(헤드리스).

test_main.py의 멀티플레이 진입점이 실제로:
  - 소켓 호스트/클라를 세우고
  - 마을에서 게임 루프가 net.tick을 돌리며
  - 크래시 없이 유지되는지
를, GUI 없이 두 자식 프로세스로 확인한다.

각 프로세스는 자기 원격 인식 수를 stderr로 주기 출력하도록 DD_MP_DEBUG=1을 켠다.
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def spawn(args):
    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    env["DD_MP_DEBUG"] = "1"
    return subprocess.Popen(
        [sys.executable, "test_main.py", *args],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def run() -> bool:
    host = spawn(["mp-host", "axeman"])
    time.sleep(3)          # 호스트 리슨은 로드 전에 열리므로 짧게 대기
    client = spawn(["mp-join", "127.0.0.1", "mage"])
    time.sleep(24)         # 양쪽 게임 로드(~12s each) + 몇 초 동기화
    for p in (host, client):
        p.terminate()
    outs = {}
    for name, p in (("host", host), ("client", client)):
        try:
            outs[name] = p.communicate(timeout=5)[0] or ""
        except subprocess.TimeoutExpired:
            p.kill()
            outs[name] = p.communicate()[0] or ""

    ok = True
    for name in ("host", "client"):
        o = outs[name]
        if "Traceback" in o:
            print(f"[{name}] 크래시:\n{o[-800:]}")
            ok = False
    # 원격 인식 로그 확인
    saw = {"host": "REMOTES=1" in outs["host"], "client": "REMOTES=1" in outs["client"]}
    print(f"[cli] host REMOTES=1: {saw['host']}   client REMOTES=1: {saw['client']}")
    if not (saw["host"] and saw["client"]):
        print("--- host tail ---\n", outs["host"][-600:])
        print("--- client tail ---\n", outs["client"][-600:])
        ok = False
    return ok


if __name__ == "__main__":
    ok = run()
    print("CLI MP SMOKE OK" if ok else "CLI MP SMOKE FAIL")
    sys.exit(0 if ok else 1)
