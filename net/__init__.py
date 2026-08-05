"""멀티플레이 넷코드 패키지 (P0: 전송 추상화 + 루프백 + 세션 뼈대).

설계 원칙
---------
- 전송(Transport)은 인터페이스 뒤에 숨긴다. 개발/CI에서는 LoopbackTransport로
  Steam 없이 헤드리스 검증하고, 프로덕션에서는 SteamTransport(py_steam_net)로
  같은 인터페이스를 구현해 갈아끼운다.
- 호스트 권위(host-authoritative): 호스트의 게임이 진짜 시뮬. 클라는 입력 인텐트만
  보내고, 호스트가 뿌리는 스냅샷을 렌더한다.
- 모든 메시지는 '개별 메시지' 단위(프레이밍 불필요). Steam P2P 메시지 모델과 동일.
"""

from net.protocol import (
    CH_CONTROL, CH_INPUT, CH_SNAPSHOT,
    encode, decode,
    hello, input_msg, snapshot, chat, event,
)
from net.transport import Transport, LoopbackTransport, loopback_pair
from net.session import Session

__all__ = [
    "CH_CONTROL", "CH_INPUT", "CH_SNAPSHOT",
    "encode", "decode",
    "hello", "input_msg", "snapshot", "chat", "event",
    "Transport", "LoopbackTransport", "loopback_pair",
    "Session",
]
