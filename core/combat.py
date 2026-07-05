"""공용 데미지 계산.

뺄셈 공식(ATK-DEF)은 초반엔 원킬, 후반엔 1딜 벽을 만들기 쉽다.
최소 관통(공격력의 18%)과 ±10% 비례 분산을 더해
어느 층에서도 데미지가 0에 수렴하거나 고정 숫자로 굳지 않게 한다.
"""
import random

MIN_PEN_RATIO = 0.18   # 방어 무시 최소 관통 비율
VAR_LO, VAR_HI = 0.90, 1.15  # 데미지 분산


def roll_damage(atk: float, defense: float, mult: float = 1.0) -> int:
    raw = atk * mult
    base = max(raw - defense, raw * MIN_PEN_RATIO, 1.0)
    return max(1, int(base * random.uniform(VAR_LO, VAR_HI)))
