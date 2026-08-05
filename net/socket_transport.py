"""TCP 소켓 전송 — 로컬/LAN 직접접속.

용도
----
1. 개발/테스트: 한 머신(또는 같은 LAN)에서 게임 창 두 개를 이어 '진짜로 둘이
   마을을 돌아다니는' 걸 눈으로 확인한다. (Steam 불필요)
2. 폴백 전송: Steam 바인딩이 부족할 때 직접 IP 접속용으로 그대로 쓴다.

같은 Transport 인터페이스를 구현하므로 게임/세션 코드는 손대지 않는다.

프레이밍
--------
TCP는 바이트 스트림이라 메시지 경계가 없다. 각 메시지를 5바이트 헤더
(>I 페이로드길이, B 채널) + 페이로드로 감싼다. 수신 스레드가 프레임을 잘라
스레드 안전 인박스에 넣고, poll()이 비운다.

피어 ID
-------
호스트=0 고정. 접속하는 클라는 호스트가 1,2,… 순으로 배정하고 접속 직후
welcome 프레임(채널 254)으로 통지한다. 클라는 welcome을 받고서야 local_id가
정해지므로 connect()는 그때까지 블로킹한다.
"""

from __future__ import annotations

import socket
import struct
import threading
from collections import deque

from net.transport import Transport

_HDR = struct.Struct(">IB")   # (payload_len, channel)
_CH_WELCOME = 254             # 전송 계층 핸드셰이크(앱 채널과 겹치지 않게 높은 값)
HOST_ID = 0
DEFAULT_PORT = 47800


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    """정확히 n바이트 수신. 연결이 끊기면 None."""
    buf = bytearray()
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except OSError:
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def _read_frame(sock: socket.socket) -> tuple[int, bytes] | None:
    """(channel, payload) 한 프레임 읽기. 끊기면 None."""
    head = _recv_exact(sock, _HDR.size)
    if head is None:
        return None
    plen, channel = _HDR.unpack(head)
    payload = _recv_exact(sock, plen) if plen else b""
    if payload is None:
        return None
    return channel, payload


def _pack(channel: int, data: bytes) -> bytes:
    return _HDR.pack(len(data), channel) + data


class _Peer:
    """호스트가 들고 있는 클라 하나(소켓 + 배정 id)."""
    def __init__(self, pid: int, sock: socket.socket):
        self.pid = pid
        self.sock = sock
        self.send_lock = threading.Lock()


class SocketTransport(Transport):
    """TCP 소켓 기반 Transport. host()/connect()로 생성한다."""

    def __init__(self, local_id: int):
        self._id = local_id
        self._inbox: deque[tuple[int, int, bytes]] = deque()
        self._inbox_lock = threading.Lock()
        self._running = True
        self._threads: list[threading.Thread] = []
        # 호스트 전용
        self._listener: socket.socket | None = None
        self._peers: dict[int, _Peer] = {}
        self._peers_lock = threading.Lock()
        self._next_pid = 1
        # 클라 전용
        self._sock: socket.socket | None = None

    # ── 팩토리 ────────────────────────────────────────────────────────
    @classmethod
    def host(cls, port: int = DEFAULT_PORT, bind: str = "0.0.0.0") -> "SocketTransport":
        t = cls(HOST_ID)
        t.is_host = True
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((bind, port))
        srv.listen(4)
        t._listener = srv
        th = threading.Thread(target=t._accept_loop, daemon=True)
        th.start()
        t._threads.append(th)
        return t

    @classmethod
    def connect(cls, host: str, port: int = DEFAULT_PORT,
                timeout: float = 30.0) -> "SocketTransport":
        # 호스트가 아직 로딩 중일 수 있으므로 연결거부는 timeout 동안 재시도한다.
        import time as _time
        deadline = _time.monotonic() + timeout
        sock = None
        last_err: Exception | None = None
        while _time.monotonic() < deadline:
            try:
                sock = socket.create_connection((host, port), timeout=5.0)
                break
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                _time.sleep(0.5)
        if sock is None:
            raise ConnectionError(f"{host}:{port} 접속 실패: {last_err}")
        sock.settimeout(None)
        # welcome 프레임을 받아 내 id를 확정한다(그 전엔 local_id 미정).
        frame = _read_frame(sock)
        if frame is None or frame[0] != _CH_WELCOME:
            sock.close()
            raise ConnectionError("호스트 welcome 핸드셰이크 실패")
        assigned = int(frame[1].decode("utf-8"))
        t = cls(assigned)
        t.is_host = False
        t._sock = sock
        th = threading.Thread(target=t._client_recv_loop, daemon=True)
        th.start()
        t._threads.append(th)
        return t

    # ── 호스트 루프 ───────────────────────────────────────────────────
    def _accept_loop(self) -> None:
        while self._running and self._listener is not None:
            try:
                sock, _addr = self._listener.accept()
            except OSError:
                break
            sock.settimeout(None)
            with self._peers_lock:
                pid = self._next_pid
                self._next_pid += 1
                self._peers[pid] = _Peer(pid, sock)
            # welcome: 배정된 id 통지
            try:
                sock.sendall(_pack(_CH_WELCOME, str(pid).encode("utf-8")))
            except OSError:
                self._drop_peer(pid)
                continue
            th = threading.Thread(target=self._host_recv_loop,
                                  args=(pid, sock), daemon=True)
            th.start()
            self._threads.append(th)

    def _host_recv_loop(self, pid: int, sock: socket.socket) -> None:
        while self._running:
            frame = _read_frame(sock)
            if frame is None:
                break
            channel, payload = frame
            with self._inbox_lock:
                self._inbox.append((pid, channel, payload))
        self._drop_peer(pid)

    def _drop_peer(self, pid: int) -> None:
        with self._peers_lock:
            peer = self._peers.pop(pid, None)
        if peer is not None:
            try:
                peer.sock.close()
            except OSError:
                pass

    # ── 클라 루프 ─────────────────────────────────────────────────────
    def _client_recv_loop(self) -> None:
        sock = self._sock
        while self._running and sock is not None:
            frame = _read_frame(sock)
            if frame is None:
                break
            channel, payload = frame
            with self._inbox_lock:
                self._inbox.append((HOST_ID, channel, payload))

    # ── Transport 구현 ────────────────────────────────────────────────
    def local_id(self) -> int:
        return self._id

    def peers(self) -> list[int]:
        if self.is_host:
            with self._peers_lock:
                return list(self._peers.keys())
        return [HOST_ID] if self._sock is not None else []

    def send(self, peer_id: int, channel: int, data: bytes) -> None:
        frame = _pack(channel, data)
        if self.is_host:
            with self._peers_lock:
                peer = self._peers.get(peer_id)
            if peer is None:
                return
            with peer.send_lock:
                try:
                    peer.sock.sendall(frame)
                except OSError:
                    self._drop_peer(peer_id)
        else:
            if self._sock is None:
                return
            try:
                self._sock.sendall(frame)
            except OSError:
                pass

    def poll(self) -> list[tuple[int, int, bytes]]:
        with self._inbox_lock:
            drained = list(self._inbox)
            self._inbox.clear()
        return drained

    def close(self) -> None:
        self._running = False
        if self._listener is not None:
            try:
                self._listener.close()
            except OSError:
                pass
        with self._peers_lock:
            for peer in self._peers.values():
                try:
                    peer.sock.close()
                except OSError:
                    pass
            self._peers.clear()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
