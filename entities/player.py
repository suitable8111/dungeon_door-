from entities.entity import Entity
from core.constants import CLASSES


class Player(Entity):
    # move_speed=1.0 기준 연속 이동 간격(ms) / attack_speed=1.0 기준 공격 쿨다운(ms)
    BASE_MOVE_REPEAT_MS = 220
    BASE_ATK_CD_MS      = 700

    def __init__(self, x, y, char_class='warrior', char_name='Hero'):
        super().__init__(x, y, "영웅", hp=30, max_hp=30, attack=5, defense=2)
        # 캐릭터 정체성 (세이브 카드)
        self.char_class = char_class if char_class in CLASSES else 'warrior'
        self.char_name  = char_name or 'Hero'
        # 외형 커스터마이즈 (피부/헤어스타일/머리색) — 세이브 카드 프리뷰용
        self.appearance = {'skin': 0, 'hair': 0, 'haircol': 0}
        # 궁수는 이동/공속이 조금 높고 방어가 낮은 원거리 딜러
        if self.char_class == 'archer':
            self.hp = self.max_hp = 26
            self.attack = 5
            self.defense = 1
        # 마법사는 저HP·저방어 원거리 딜러 — 마법 볼트(무료) + DoT·소환 스킬 의존
        elif self.char_class == 'mage':
            self.hp = self.max_hp = 22
            self.attack = 4
            self.defense = 1
        # 도끼맨은 고HP·고공격·중방어 근접 딜러 — 대신 공격속도가 매우 느리다
        elif self.char_class == 'axeman':
            self.hp = self.max_hp = 34
            self.attack = 8
            self.defense = 3
        self.level = 1
        self.xp = 0
        self.xp_next = 15
        self.gold = 0
        self.enhance_stones = 0  # 강화석 보유 수량

        # 신규 능력치
        self.attack_speed = 1.0   # 높을수록 공격 쿨다운 단축
        self.evasion      = 0     # 회피율 (0~100 %)
        self.move_speed   = 1.0   # 높을수록 연속이동 빠름
        # 도끼맨: 기본 공격속도가 느리다(한 방이 강한 대신 굼뜸)
        if self.char_class == 'axeman':
            self.attack_speed = 0.6

        # 도끼맨 광폭화(버프) — 공속↑ + 흡혈
        self.aspd_buff_ms  = 0     # 공격속도 버프 잔여(ms)
        self.aspd_buff_pct = 0.0   # 공격속도 버프율
        self.lifesteal_ms  = 0     # 흡혈 잔여(ms)
        self.lifesteal_pct = 0.0   # 가한 피해의 흡혈 비율
        self.move_buff_ms  = 0     # 이동속도 버프 잔여(ms) — 라그나로크
        self.move_buff_pct = 0.0   # 이동속도 버프율

        # 디버프 (저주/슬로우/두려움/공격약화)
        self.cursed_ms  = 0   # 받는 피해 50% 증가
        self.slowed_ms  = 0   # 이동속도 30% 감소
        self.feared_ms  = 0   # 명중률 40%로 저하
        self.atk_down_ms  = 0     # 공격력 저하 지속시간 (저주 트랩)
        self.atk_down_pct = 0.0   # 공격력 저하율 (0~1)

        # 드라이브 게이지 (캔슬 자원): 3칸, 시간·타격으로 회복
        self.drive:     float = 3.0
        self.drive_max: int   = 3

        # 스태미나 SP (공격 자원): 공격마다 소모, 잠시 쉬면 회복
        self.stamina:     float = 100.0
        self.stamina_max: int   = 100

        # 방금 파손된 방어구 (Game 루프가 경고 연출 후 비움)
        self.just_broken: list = []

        # 여관밥 버프 (이번 런 한정 최대 HP +10%)
        self.well_fed: bool = False

        # 버프
        self.invincible_ms    = 0   # 무적 (궁극기)
        self.heal_def_bonus   = 0   # 재생의 숨결 방어력 임시 증가
        self.heal_def_ms      = 0   # 버프 잔여 시간
        self.damage_reduce_pct = 0.0  # 철갑 방벽: 피해 감소율 (0.0~1.0)
        self.damage_reduce_ms  = 0    # 버프 잔여 시간
        self.atk_bonus_pct     = 0.0  # 전투 함성: 공격력 증가율
        self.atk_bonus_ms      = 0    # 버프 잔여 시간
        # 궁수 자동 사격 (Auto Volley) 버프
        self.auto_volley_ms    = 0    # 버프 잔여 시간
        self.auto_volley_mul   = 1.0  # 화살 위력 배율 (강화 레벨 연동)
        self.auto_volley_tick  = 0    # 다음 발사까지 잔여 (ms)

        # 펫(동반자) 시스템 — 값만 저장, 활성 Pet 객체는 Game이 보유
        self.is_pet_unlocked   = False
        self.pet_type          = 'attack'   # 'buff' | 'debuff' | 'attack'
        self.pet_level         = 1
        self.pet_stones        = 0          # 펫 전용 강화석 보유 수
        self.active_pet        = None       # 런타임 Pet 객체 (직렬화 X)

        # 던전 증표 (이번 런 누적) — 소지 시 패시브 스탯 상승.
        #   atk=공격의 증표, haste=신속의 증표, guard=수호의 증표. 층 클리어마다 획득.
        self.tokens: dict = {'atk': 0, 'haste': 0, 'guard': 0}

        # 인벤토리 (최대 20칸)
        self.inventory: list    = []
        self.max_inventory: int = 20

        # 장착 장비 {슬롯: Item | None}
        self.equipment: dict = {
            'head': None, 'body': None, 'weapon': None,
            'off_hand': None, 'accessory': None, 'feet': None,
        }

    # ── 던전 증표 패시브 보너스 (누적 개수에 비례, 상한 有) ──────────
    @property
    def token_atk(self) -> int:
        """공격의 증표: 4개당 공격력 +1 (최대 +60)."""
        return min(60, self.tokens.get('atk', 0) // 4)

    @property
    def token_def(self) -> int:
        """수호의 증표: 4개당 방어력 +1 (최대 +45)."""
        return min(45, self.tokens.get('guard', 0) // 4)

    @property
    def token_aspd(self) -> float:
        """신속의 증표: 5개당 공격속도 +0.02 (최대 +0.40)."""
        return min(0.40, (self.tokens.get('haste', 0) // 5) * 0.02)

    # ── 유효 능력치 (기본 + 전체 장비 보너스 + 던전 증표) ────────────
    @property
    def total_attack(self) -> int:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and not item.broken and item.effect in ('attack_up', 'stat_up_all')
        )
        enhance = sum(
            item.enhance_level for item in self.equipment.values()
            if item and not item.broken and item.item_type == 'weapon'
        )
        base = self.attack + bonus + enhance + self.token_atk
        if self.atk_bonus_ms > 0:
            base = int(base * (1.0 + self.atk_bonus_pct))
        if self.atk_down_ms > 0:
            base = max(1, int(base * (1.0 - self.atk_down_pct)))
        return base

    @property
    def total_defense(self) -> int:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and not item.broken and item.effect in ('defense_up', 'stat_up_all')
        )
        enhance = sum(
            item.enhance_level for item in self.equipment.values()
            if item and not item.broken and item.item_type in ('armor', 'off_hand')
        )
        heal_buf = self.heal_def_bonus if self.heal_def_ms > 0 else 0
        return self.defense + bonus + enhance + heal_buf + self.token_def

    @property
    def dungeon_inventory(self) -> list:
        """세션 인벤토리 별칭 — 마을 진입 시 영구 창고로 이전, 사망 시 소실."""
        return self.inventory

    @property
    def total_sp_reduce(self) -> float:
        """SP 소모 경감 — 레벨 0.4%/Lv + 장비 sp_reduce 합 (총 45% 상한)."""
        equip = sum(getattr(it, 'sp_reduce', 0.0)
                    for it in self.equipment.values()
                    if it and not it.broken)
        return min(0.45, self.level * 0.004 + equip)

    @property
    def total_evasion(self) -> int:
        """투구 강화 포함 총 회피율 (0~80%)."""
        enhance = sum(
            item.enhance_level for item in self.equipment.values()
            if item and not item.broken and item.item_type == 'head'
        )
        return min(80, self.evasion + enhance)

    @property
    def skill_damage_mul(self) -> float:
        """장신구 강화로 증가하는 스킬 데미지 배율."""
        enhance = sum(
            item.enhance_level for item in self.equipment.values()
            if item and not item.broken and item.item_type == 'accessory'
        )
        return 1.0 + enhance * 0.05

    def take_damage(self, amount: int):
        if self.invincible_ms > 0:
            return
        if self.cursed_ms > 0:
            amount = int(amount * 1.5)
        if self.damage_reduce_ms > 0:
            amount = max(1, int(amount * (1.0 - self.damage_reduce_pct)))
        self.hp = max(0, self.hp - amount)
        self._degrade_armor()

    def _degrade_armor(self):
        """피격 시 장착 방어구 중 랜덤 1개 내구도 -1.

        회피하면 안 닳는다(take_damage 미호출). 0이 되는 순간
        just_broken에 기록 — Game 루프가 경고 연출을 소비한다.
        """
        import random
        candidates = [it for it in self.equipment.values()
                      if it and it.max_durability > 0 and it.durability > 0]
        if not candidates:
            return
        it = random.choice(candidates)
        it.durability -= 1
        if it.durability <= 0:
            self.just_broken.append(it)

    def tick_debuffs(self, dt_ms: int):
        if self.cursed_ms > 0:
            self.cursed_ms = max(0, self.cursed_ms - dt_ms)
        if self.slowed_ms > 0:
            self.slowed_ms = max(0, self.slowed_ms - dt_ms)
        if self.feared_ms > 0:
            self.feared_ms = max(0, self.feared_ms - dt_ms)
        if self.atk_down_ms > 0:
            self.atk_down_ms = max(0, self.atk_down_ms - dt_ms)
            if self.atk_down_ms == 0:
                self.atk_down_pct = 0.0
        if self.invincible_ms > 0:
            self.invincible_ms = max(0, self.invincible_ms - dt_ms)
        if self.heal_def_ms > 0:
            self.heal_def_ms = max(0, self.heal_def_ms - dt_ms)
            if self.heal_def_ms == 0:
                self.heal_def_bonus = 0
        if self.damage_reduce_ms > 0:
            self.damage_reduce_ms = max(0, self.damage_reduce_ms - dt_ms)
            if self.damage_reduce_ms == 0:
                self.damage_reduce_pct = 0.0
        if self.atk_bonus_ms > 0:
            self.atk_bonus_ms = max(0, self.atk_bonus_ms - dt_ms)
            if self.atk_bonus_ms == 0:
                self.atk_bonus_pct = 0.0
        if self.aspd_buff_ms > 0:
            self.aspd_buff_ms = max(0, self.aspd_buff_ms - dt_ms)
            if self.aspd_buff_ms == 0:
                self.aspd_buff_pct = 0.0
        if self.lifesteal_ms > 0:
            self.lifesteal_ms = max(0, self.lifesteal_ms - dt_ms)
            if self.lifesteal_ms == 0:
                self.lifesteal_pct = 0.0
        if self.move_buff_ms > 0:
            self.move_buff_ms = max(0, self.move_buff_ms - dt_ms)
            if self.move_buff_ms == 0:
                self.move_buff_pct = 0.0

    @property
    def total_move_speed(self) -> float:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and not item.broken and item.effect == 'speed_up'
        )
        enhance = sum(
            item.enhance_level * 0.05 for item in self.equipment.values()
            if item and not item.broken and item.item_type == 'boots'
        )
        spd = self.move_speed + bonus + enhance
        if self.move_buff_ms > 0:
            spd *= (1.0 + self.move_buff_pct)
        if self.slowed_ms > 0:
            spd *= 0.7
        return spd

    # ── 쿨다운 / 이동 간격 계산 ────────────────────────────────────
    @property
    def total_attack_speed(self) -> float:
        """기본 공격속도 + 신속의 증표 보너스 + 광폭화 버프."""
        spd = self.attack_speed + self.token_aspd
        if self.aspd_buff_ms > 0:
            spd *= (1.0 + self.aspd_buff_pct)
        return spd

    @property
    def atk_cooldown_ms(self) -> int:
        return max(100, int(self.BASE_ATK_CD_MS / self.total_attack_speed))

    @property
    def move_repeat_ms(self) -> int:
        return max(60, int(self.BASE_MOVE_REPEAT_MS / self.total_move_speed))

    # ── XP / 레벨업 ────────────────────────────────────────────────
    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self._level_up()
            leveled = True
        return leveled

    def _level_up(self):
        self.level += 1
        # 소프트캡 곡선: Lv20까지는 ×1.33, 이후 ×1.15 —
        # 몬스터 XP는 층수 다항 스케일이라 지수 곡선을 유지하면
        # 후반 레벨업이 완전히 멈춰 버린다
        rate = 1.33 if self.level < 20 else 1.15
        self.xp_next = int(self.xp_next * rate + 10)
        self.max_hp += 8 + self.level // 3
        self.hp = self.max_hp
        self.attack += 1
        if self.level % 2 == 0:
            self.defense += 1
            self.attack_speed = round(self.attack_speed + 0.12, 2)
        if self.level % 3 == 0:
            self.move_speed = round(self.move_speed + 0.15, 2)
        if self.level % 5 == 0:
            self.evasion = min(40, self.evasion + 3)

    # ── 저장 복원 ───────────────────────────────────────────────────
    @classmethod
    def from_save(cls, x, y, data, item_data_dict,
                  char_class='warrior', char_name='Hero', appearance=None):
        from entities.item import Item
        p = cls(x, y, char_class=char_class, char_name=char_name)
        if appearance:
            p.appearance = dict(appearance)
        p.hp           = data['hp']
        p.max_hp       = data['max_hp']
        p.attack       = data['attack']
        p.defense      = data['defense']
        p.level        = data['level']
        p.xp           = data['xp']
        p.xp_next      = data['xp_next']
        p.gold          = data.get('gold', 0)
        p.enhance_stones = data.get('enhance_stones', 0)
        p.attack_speed  = data.get('attack_speed', 1.0)
        p.evasion       = data.get('evasion', 0)
        p.move_speed    = data.get('move_speed', 1.0)
        # 던전 증표 (구버전 세이브 안전 기본값)
        _tok = data.get('tokens') or {}
        p.tokens = {'atk': int(_tok.get('atk', 0)),
                    'haste': int(_tok.get('haste', 0)),
                    'guard': int(_tok.get('guard', 0))}
        # 펫 (구버전 세이브 안전 기본값)
        p.is_pet_unlocked = data.get('is_pet_unlocked', False)
        p.pet_type        = data.get('pet_type', 'attack')
        p.pet_level       = data.get('pet_level', 1)
        p.pet_stones      = data.get('pet_stones', 0)

        def _make_item(entry, idd):
            # entry: 구 포맷 str or 신 포맷 {'key':..,'enhance_level':..}
            if isinstance(entry, str):
                key, enh = entry, 0
            else:
                key, enh = entry.get('key', ''), entry.get('enhance_level', 0)
            if key not in idd:
                return None
            d = dict(idd[key])
            d['key'] = key
            d['enhance_level'] = enh
            if isinstance(entry, dict) and 'durability' in entry:
                d['durability'] = entry['durability']
            return Item(0, 0, d)

        p.inventory = []
        for entry in data.get('inventory', []):
            item = _make_item(entry, item_data_dict)
            if item:
                p.inventory.append(item)

        p.equipment = {'head': None, 'body': None, 'weapon': None, 'off_hand': None, 'accessory': None, 'feet': None}
        _COMPAT = {'armor': 'body'}
        for slot, entry in data.get('equipment', {}).items():
            slot = _COMPAT.get(slot, slot)
            if slot in p.equipment and entry:
                item = _make_item(entry, item_data_dict)
                if item:
                    p.equipment[slot] = item

        return p
