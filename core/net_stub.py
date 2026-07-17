"""멀티플레이어 네트워크 스텁 (미래용 · 현재 비동작).

⚠️ 이 게임은 현재 순수 싱글플레이입니다. 실제 소켓/전송 계층은 없습니다.
   나중에 멀티플레이를 붙일 때 이 인터페이스에 실 전송을 채워 넣으면 되도록,
   '정복 일지 / 999 클리어 칭호' 공유의 결합 지점만 정의해 둔 껍데기입니다.

USER_PROFILE 패킷 규격 (방 입장 시 방장·파티원에게 브로드캐스트할 데이터):
    {
      "type": "USER_PROFILE",
      "name": str,
      "cleared": bool,            # 999층 최종 클리어 여부
      "title": str,               # 활성 칭호 id ('' 가능)
      "best_floor": int,
      "theme_clears": {str:int},  # 테마별 누적 클리어
    }
"""
from __future__ import annotations


def build_user_profile(name: str, records: dict) -> dict:
    """records(프로필)에서 USER_PROFILE 패킷 dict를 구성한다."""
    return {
        'type': 'USER_PROFILE',
        'name': name or 'Hero',
        'cleared': bool(records.get('game_cleared', False)),
        'title': records.get('active_title', ''),
        'best_floor': int(records.get('best_floor', 0)),
        'theme_clears': dict(records.get('theme_clears', {})),
    }


class NetworkManager:
    """실 전송이 없는 스텁. 로컬에 마지막 프로필/원격 프로필만 보관한다.

    실제 멀티플레이 구현 시 send()/on_message()에 전송 코드를 채우면 된다.
    """

    def __init__(self):
        self.connected: bool = False           # 항상 False (전송 계층 없음)
        self.local_profile: dict | None = None
        self.remote_profiles: dict[str, dict] = {}   # name -> profile
        self._handlers = {}

    # ── 방 입장 시 자기 프로필 브로드캐스트 (스텁: 로컬 저장만) ──────────
    def broadcast_profile(self, profile: dict) -> None:
        self.local_profile = profile
        # TODO(멀티플레이): self.send(profile) 로 방 전체에 전송
        if not self.connected:
            return
        self.send(profile)

    def send(self, packet: dict) -> None:
        """실 전송 자리 (현재 no-op)."""
        # TODO(멀티플레이): 소켓/웹소켓 전송 구현
        return

    def on_message(self, packet: dict) -> None:
        """원격 패킷 수신 핸들러 (미래용). USER_PROFILE만 처리."""
        if packet.get('type') == 'USER_PROFILE':
            self.remote_profiles[packet.get('name', '?')] = packet
        h = self._handlers.get(packet.get('type'))
        if h:
            h(packet)

    def register(self, ptype: str, handler) -> None:
        self._handlers[ptype] = handler

    def titled_members(self) -> list[dict]:
        """마을에서 칭호 이펙트를 뽐낼 원격 파티원 목록 (스텁: 비어있음)."""
        return [p for p in self.remote_profiles.values() if p.get('title')]
