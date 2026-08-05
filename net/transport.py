"""전송 계층 추상화.

Transport 인터페이스 하나에 대해 두 구현이 존재한다(존재할 예정이다):
  - LoopbackTransport : 같은 프로세스 안의 두 피어를 메모리 큐로 잇는다.
                        Steam 없이 macOS 헤드리스에서 넷코드 로직을 검증한다. (P0)
  - SteamTransport    : py_steam_net 로비 + P2P 메시지. 같은 인터페이스. (P1)

메시지는 개별 단위로 오간다(프레이밍 불필요). Steam send_message_to() 모델과 동일.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque


class Transport(ABC):
    """호스트/클라가 공유하는 전송 인터페이스."""

    #: 이 피어가 호스트(권위 시뮬)인지 여부.
    is_host: bool = False

    @abstractmethod
    def local_id(self) -> int:
        """이 피어의 고유 ID (Steam에서는 SteamID, 루프백에서는 0/1)."""

    @abstractmethod
    def peers(self) -> list[int]:
        """현재 연결된 원격 피어 ID 목록 (자기 자신 제외)."""

    @abstractmethod
    def send(self, peer_id: int, channel: int, data: bytes) -> None:
        """특정 피어에게 한 메시지 전송."""

    def broadcast(self, channel: int, data: bytes) -> None:
        """연결된 모든 원격 피어에게 전송 (기본 구현: send 반복)."""
        for pid in self.peers():
            self.send(pid, channel, data)

    @abstractmethod
    def poll(self) -> list[tuple[int, int, bytes]]:
        """도착한 메시지를 전부 꺼낸다. (from_peer_id, channel, data) 리스트.

        비차단. 호출할 때마다 인박스를 비운다.
        """

    def run_callbacks(self) -> None:
        """전송 백엔드의 콜백 펌프. 루프백은 no-op, Steam은 SteamAPI_RunCallbacks."""

    def close(self) -> None:
        """세션 종료 정리."""


class LoopbackTransport(Transport):
    """메모리 큐로 상대 피어와 직결된 전송. loopback_pair()로 생성한다."""

    def __init__(self, local_id: int):
        self._id = local_id
        self._inbox: deque[tuple[int, int, bytes]] = deque()
        # 상대 전송 인스턴스 (loopback_pair가 채워준다)
        self._peer: LoopbackTransport | None = None

    # ── 배선 ────────────────────────────────────────────────────────
    def _link(self, other: "LoopbackTransport") -> None:
        self._peer = other

    # ── Transport 구현 ───────────────────────────────────────────────
    def local_id(self) -> int:
        return self._id

    def peers(self) -> list[int]:
        return [self._peer.local_id()] if self._peer is not None else []

    def send(self, peer_id: int, channel: int, data: bytes) -> None:
        if self._peer is None or peer_id != self._peer.local_id():
            return  # 알 수 없는 피어 — 조용히 폐기
        # 바이트 사본을 넣어 송신측 버퍼 변조로부터 격리
        self._peer._inbox.append((self._id, channel, bytes(data)))

    def poll(self) -> list[tuple[int, int, bytes]]:
        drained = list(self._inbox)
        self._inbox.clear()
        return drained

    def close(self) -> None:
        self._peer = None
        self._inbox.clear()


def loopback_pair(host_id: int = 0, client_id: int = 1
                  ) -> tuple[LoopbackTransport, LoopbackTransport]:
    """서로 직결된 (host, client) 루프백 전송 한 쌍을 만든다."""
    host = LoopbackTransport(host_id)
    client = LoopbackTransport(client_id)
    host._link(client)
    client._link(host)
    host.is_host = True
    client.is_host = False
    return host, client
