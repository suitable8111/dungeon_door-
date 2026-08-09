"""메시지 스키마 + (역)직렬화.

P0에서는 사람이 읽기 쉬운 JSON 코덱을 쓴다(무의존성·디버그 용이). 인코딩은
encode()/decode() 뒤에 숨겨져 있으므로, P1 이후 대역폭이 문제되면 여기만
바이너리(msgpack/struct)로 교체하면 된다 — 호출부는 바뀌지 않는다.

메시지는 최상위 't'(type) 키를 가진 평범한 dict다.
"""

import json

# ── 채널 (Steam P2P 채널과 1:1 대응) ────────────────────────────────
CH_CONTROL  = 0   # hello / chat / event — 신뢰성 필요, 저빈도
CH_INPUT    = 1   # 클라 → 호스트 입력 인텐트
CH_SNAPSHOT = 2   # 호스트 → 클라 상태 스냅샷 (고빈도)

# ── 메시지 타입 ─────────────────────────────────────────────────────
T_HELLO    = "hello"
T_INPUT    = "input"
T_SNAPSHOT = "snap"
T_STATE    = "state"   # 마을 모델: 각 피어가 '자기' 상태를 스스로 알림(소유자 권위)
T_WORLD    = "world"   # 호스트 → 클라: 공유 월드 상태(밭·목장 등, 호스트 권위)
T_ACTION   = "wact"    # 클라 → 호스트: 월드 변경 액션 인텐트(심기·수확 등)
T_CHAT     = "chat"
T_EVENT    = "evt"


# ── 코덱 ────────────────────────────────────────────────────────────
def encode(msg: dict) -> bytes:
    """메시지 dict → 전송용 bytes."""
    return json.dumps(msg, separators=(",", ":")).encode("utf-8")


def decode(data: bytes) -> dict:
    """전송받은 bytes → 메시지 dict. 실패 시 빈 dict."""
    try:
        m = json.loads(data.decode("utf-8"))
        return m if isinstance(m, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


# ── 메시지 빌더 ─────────────────────────────────────────────────────
def hello(char_class: str, name: str, appearance: dict | None) -> dict:
    """접속 직후 클라가 자기 정체성을 알린다."""
    return {"t": T_HELLO, "cls": char_class, "name": name,
            "app": appearance or {}}


def input_msg(action: dict, seq: int = 0) -> dict:
    """클라 → 호스트: _process()에 넣을 액션 인텐트. seq는 중복/순서 판정용."""
    return {"t": T_INPUT, "a": action, "s": seq}


def snapshot(tick: int, players: list[dict]) -> dict:
    """호스트 → 클라: 권위 상태. players는 player_state() dict의 리스트."""
    return {"t": T_SNAPSHOT, "k": tick, "p": players}


def state_msg(player: dict) -> dict:
    """마을 모델: 한 피어가 자기 자신의 player_state를 브로드캐스트."""
    return {"t": T_STATE, "p": player}


def world_msg(state: dict) -> dict:
    """호스트 → 클라: 공유 월드 상태(밭·목장 등)."""
    return {"t": T_WORLD, "w": state}


def action_msg(action: dict) -> dict:
    """클라 → 호스트: 월드 변경 액션 인텐트."""
    return {"t": T_ACTION, "a": action}


def chat(sender_id: int, text: str) -> dict:
    return {"t": T_CHAT, "id": sender_id, "m": text}


def event(kind: str, data: dict | None = None) -> dict:
    """연출 큐(효과음/이펙트 등) — 게임플레이 상태와 분리된 부수 신호."""
    return {"t": T_EVENT, "e": kind, "d": data or {}}


def player_state(pid: int, x: int, y: int, facing: str, walk: int,
                 char_class: str, name: str, appearance: dict | None,
                 hp: int, max_hp: int, floor: int = 0,
                 defense: int = 0, evasion: int = 0, status: int = 0) -> dict:
    """스냅샷에 담기는 한 플레이어의 최소 상태.

    status: 0=정상 / 1=다운(부활 대기) / 2=관전(사망, 다음 층 부활 대기) — co-op 부활용.
    """
    return {"id": pid, "x": x, "y": y, "f": facing, "w": walk,
            "c": char_class, "n": name, "a": appearance or {},
            "hp": hp, "mhp": max_hp, "fl": floor,
            "de": defense, "ev": evasion, "st": status}
