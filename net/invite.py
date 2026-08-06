"""초대 코드 — 호스트 접속 정보(IP:포트)를 13자리 코드로 인코딩/디코딩.

스타듀밸리식 UX: 호스트가 코드를 생성해 공유하면 참가자가 붙여넣어 접속한다.
릴레이 서버가 없으므로 코드는 접속 정보 자체를 담는다(= IP의 사람친화 포장).
따라서 도달성은 raw IP와 동일(LAN/포트포워딩). 향후 SteamTransport가 들어오면
코드가 Steam 로비 ID를 담도록 바꾸면 되고, UI는 그대로 재사용한다.

포맷: [ver(1) ip(4) port(2) chk(1)] = 8바이트 → Crockford Base32 13글자.
Crockford 알파벳은 I/L/O/U를 빼 오타에 강하다(입력 시 I,L→1, O→0 자동 보정).
"""

from __future__ import annotations

import socket
import struct

# Crockford Base32 (32 chars, no I L O U)
_ALPH = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_DEC = {ch: i for i, ch in enumerate(_ALPH)}
# 흔한 혼동 문자 보정
_DEC.update({'I': 1, 'L': 1, 'O': 0, 'U': 0})

_VER = 1
CODE_LEN = 13


def local_ip() -> str:
    """이 머신의 기본 LAN IP. (외부로 UDP 소켓을 여는 척해 로컬 주소를 읽음)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # 실제 전송 없음 — 라우팅 테이블만 참조
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _enc8(data: bytes) -> str:
    num = int.from_bytes(data, "big")            # 64비트
    out = []
    for _ in range(CODE_LEN):
        out.append(_ALPH[num & 31])
        num >>= 5
    return "".join(reversed(out))


def _dec8(code: str) -> bytes:
    num = 0
    for ch in code:
        num = (num << 5) | _DEC[ch]
    num &= (1 << 64) - 1
    return num.to_bytes(8, "big")


def make_code(ip: str, port: int) -> str:
    """IP:포트 → 13자리 초대 코드."""
    payload = bytes([_VER]) + socket.inet_aton(ip) + struct.pack(">H", port)
    chk = sum(payload) & 0xFF
    return _enc8(payload + bytes([chk]))


def parse_code(code: str) -> tuple[str, int] | None:
    """초대 코드 → (ip, port). 형식/체크섬 불일치 시 None."""
    code = "".join(code.split()).upper()
    if len(code) != CODE_LEN or any(ch not in _DEC for ch in code):
        return None
    try:
        raw = _dec8(code)
    except (KeyError, ValueError):
        return None
    if raw[0] != _VER:
        return None
    if (sum(raw[:7]) & 0xFF) != raw[7]:
        return None
    ip = socket.inet_ntoa(raw[1:5])
    port = struct.unpack(">H", raw[5:7])[0]
    return ip, port


def looks_like_code(s: str) -> bool:
    """입력이 IP가 아니라 초대 코드로 보이는가 (점 없음 + 13자)."""
    s = "".join(s.split())
    return "." not in s and len(s) == CODE_LEN
