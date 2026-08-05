"""호스트 권위 세션 — 전송 위에 얹는 게임 동기화 계층.

역할
----
- 호스트: 모든 플레이어의 '진짜' 상태를 소유한다. 자기 플레이어는 로컬 provider로
  매 틱 갱신하고, 원격 플레이어는 클라가 보낸 입력 인텐트로 갱신한 뒤, 일정 주기로
  전체 스냅샷을 브로드캐스트한다.
- 클라: 로컬 입력을 인텐트로 호스트에 보내고, 호스트 스냅샷을 받아 RemotePlayer
  뷰(자기 자신 제외 나머지)에 반영한다.

P0에서는 이동을 세션이 직접 처리해 Steam 없이 루프백으로 검증한다. P1에서 실제
Game 통합 시, apply_input 훅을 게임의 _process 라우팅으로 바꾸고 provider를 실제
플레이어에 연결하면 된다 — 인터페이스는 그대로다.
"""

from __future__ import annotations

from typing import Callable, Optional

from net import protocol as P
from net.transport import Transport
from entities.remote_player import RemotePlayer

# 방향키 델타 → facing 이름
_FACING = {(1, 0): "right", (-1, 0): "left", (0, 1): "down", (0, -1): "up"}


class Session:
    def __init__(
        self,
        transport: Transport,
        char_class: str = "warrior",
        name: str = "Hero",
        appearance: Optional[dict] = None,
        *,
        local_player_state: Optional[Callable[[], dict]] = None,
        walkable: Optional[Callable[[int, int], bool]] = None,
        spawn: tuple[int, int] = (0, 0),
        snapshot_interval: int = 3,
    ):
        self.tp = transport
        self.is_host = transport.is_host
        self.char_class = char_class
        self.name = name
        self.appearance = appearance or {}

        # 클라가 없으면(=호스트가 provider 미제공) 세션이 자체 상태를 들고 이동시킨다.
        self._provider = local_player_state
        self._walkable = walkable or (lambda x, y: True)
        self._snapshot_interval = max(1, snapshot_interval)

        # 로컬 플레이어의 권위 상태 (호스트 기준). provider가 있으면 매 틱 덮어씀.
        self._local = P.player_state(
            transport.local_id(), spawn[0], spawn[1], "down", 0,
            char_class, name, self.appearance, hp=30, max_hp=30)

        # 호스트: pid → 권위 상태 dict (자기 것 포함). 클라: 사용 안 함.
        self._authoritative: dict[int, dict] = {transport.local_id(): self._local}

        # 클라/호스트 공통: 원격 플레이어 렌더 뷰. pid → RemotePlayer.
        self.remote_players: dict[int, RemotePlayer] = {}

        # 수신 채팅 로그 (게임 UI가 소비)
        self.chat_log: list[tuple[int, str]] = []

        self._tick = 0
        self._seq = 0
        self._hello_sent = False

    # ── 접속 ────────────────────────────────────────────────────────
    def start(self) -> None:
        """세션 시작. 클라는 자기 정체성을 호스트에 알린다."""
        if not self.is_host and not self._hello_sent:
            self._send(P.CH_CONTROL, P.hello(self.char_class, self.name,
                                             self.appearance))
            self._hello_sent = True

    # ── 로컬 입력 ────────────────────────────────────────────────────
    def send_action(self, action: dict) -> None:
        """로컬 플레이어의 행동 인텐트를 처리한다.

        호스트면 즉시 권위 상태에 적용, 클라면 호스트로 전송한다.
        """
        if self.is_host:
            self._apply_action(self.tp.local_id(), action)
        else:
            self._seq += 1
            self._send(P.CH_INPUT, P.input_msg(action, self._seq))

    def send_chat(self, text: str) -> None:
        msg = P.chat(self.tp.local_id(), text)
        self.chat_log.append((self.tp.local_id(), text))
        if self.is_host:
            self.tp.broadcast(P.CH_CONTROL, P.encode(msg))
        else:
            self._send(P.CH_CONTROL, msg)

    # ── 매 프레임 ────────────────────────────────────────────────────
    def tick(self, dt: float = 16.0) -> None:
        self.tp.run_callbacks()
        self._tick += 1

        # 로컬 권위 상태를 실제 플레이어에서 갱신 (제공된 경우)
        if self.is_host and self._provider is not None:
            st = self._provider()
            if st:
                st["id"] = self.tp.local_id()
                self._authoritative[self.tp.local_id()] = st
                self._local = st

        # 수신 메시지 처리
        for from_id, channel, data in self.tp.poll():
            self._handle(from_id, channel, P.decode(data))

        # 호스트: 권위 상태 → 자기 RemotePlayer 뷰 동기화 (렌더를 양쪽 공통화)
        if self.is_host:
            self._sync_host_views()
            # 주기적 스냅샷 브로드캐스트
            if self._tick % self._snapshot_interval == 0:
                players = list(self._authoritative.values())
                self.tp.broadcast(P.CH_SNAPSHOT,
                                  P.encode(P.snapshot(self._tick, players)))

        # 원격 플레이어 보간 갱신 (양쪽 공통)
        for rp in self.remote_players.values():
            rp.update(dt)

    # ── 내부: 메시지 디스패치 ────────────────────────────────────────
    def _handle(self, from_id: int, channel: int, msg: dict) -> None:
        t = msg.get("t")
        if t == P.T_HELLO and self.is_host:
            self._register_remote(from_id, msg)
        elif t == P.T_INPUT and self.is_host:
            self._apply_action(from_id, msg.get("a", {}))
        elif t == P.T_SNAPSHOT and not self.is_host:
            self._apply_snapshot(msg)
        elif t == P.T_CHAT:
            self.chat_log.append((msg.get("id", from_id), msg.get("m", "")))
            if self.is_host:  # 호스트는 다른 피어들에게 중계
                for pid in self.tp.peers():
                    if pid != from_id:
                        self.tp.send(pid, P.CH_CONTROL, P.encode(msg))

    def _register_remote(self, pid: int, msg: dict) -> None:
        # 호스트 옆 스폰 위치 (P0: 호스트 우측 한 칸)
        hx, hy = self._local["x"], self._local["y"]
        sx, sy = hx + 1, hy
        st = P.player_state(pid, sx, sy, "down", 0,
                            msg.get("cls", "warrior"), msg.get("name", "Hero"),
                            msg.get("app", {}), hp=30, max_hp=30)
        self._authoritative[pid] = st

    def _apply_action(self, pid: int, action: dict) -> None:
        """호스트 권위: 한 플레이어의 행동을 상태에 반영한다.

        P0는 이동만 처리한다. P1에서 게임의 _process 라우팅으로 확장한다.
        """
        st = self._authoritative.get(pid)
        if st is None or action.get("type") != "move":
            return
        dx, dy = action.get("dx", 0), action.get("dy", 0)
        if (dx, dy) in _FACING:
            st["f"] = _FACING[(dx, dy)]
        nx, ny = st["x"] + dx, st["y"] + dy
        if self._walkable(nx, ny):
            st["x"], st["y"] = nx, ny
            st["w"] ^= 1

    def _apply_snapshot(self, msg: dict) -> None:
        """클라: 스냅샷을 RemotePlayer 뷰에 반영 (자기 자신 제외)."""
        me = self.tp.local_id()
        seen: set[int] = set()
        for st in msg.get("p", []):
            pid = st.get("id")
            if pid is None:
                continue
            seen.add(pid)
            if pid == me:
                # 호스트가 본 '내 위치' — P0에서는 로컬 예측을 신뢰하고 무시.
                # (P1: 권위 위치와 어긋나면 재조정 reconciliation)
                continue
            rp = self.remote_players.get(pid)
            if rp is None:
                rp = RemotePlayer(pid)
                self.remote_players[pid] = rp
            rp.apply_state(st)
        # 사라진 피어 정리
        for pid in list(self.remote_players):
            if pid not in seen and pid != me:
                del self.remote_players[pid]

    def _sync_host_views(self) -> None:
        """호스트: 권위 상태 dict를 RemotePlayer 렌더 뷰(자기 제외)에 반영."""
        me = self.tp.local_id()
        for pid, st in self._authoritative.items():
            if pid == me:
                continue
            rp = self.remote_players.get(pid)
            if rp is None:
                rp = RemotePlayer(pid)
                self.remote_players[pid] = rp
            rp.apply_state(st)
        # 떠난 원격 정리
        for pid in list(self.remote_players):
            if pid not in self._authoritative:
                del self.remote_players[pid]

    def _send(self, channel: int, msg: dict) -> None:
        for pid in self.tp.peers():
            self.tp.send(pid, channel, P.encode(msg))

    # ── 조회 헬퍼 ────────────────────────────────────────────────────
    def local_state(self) -> dict:
        return self._local

    def authoritative_state(self, pid: int) -> Optional[dict]:
        return self._authoritative.get(pid)
