from entities.entity import Entity


class Player(Entity):
    # move_speed=1.0 기준 연속 이동 간격(ms) / attack_speed=1.0 기준 공격 쿨다운(ms)
    BASE_MOVE_REPEAT_MS = 220
    BASE_ATK_CD_MS      = 700

    def __init__(self, x, y):
        super().__init__(x, y, "영웅", hp=30, max_hp=30, attack=5, defense=2)
        self.level = 1
        self.xp = 0
        self.xp_next = 15
        self.gold = 0

        # 신규 능력치
        self.attack_speed = 1.0   # 높을수록 공격 쿨다운 단축
        self.evasion      = 0     # 회피율 (0~100 %)
        self.move_speed   = 1.0   # 높을수록 연속이동 빠름

        # 디버프 (저주/슬로우/두려움)
        self.cursed_ms  = 0   # 받는 피해 50% 증가
        self.slowed_ms  = 0   # 이동속도 30% 감소
        self.feared_ms  = 0   # 명중률 40%로 저하

        # 버프
        self.invincible_ms    = 0   # 무적 (궁극기)
        self.heal_def_bonus   = 0   # 재생의 숨결 방어력 임시 증가
        self.heal_def_ms      = 0   # 버프 잔여 시간

        # 인벤토리 (최대 20칸)
        self.inventory: list    = []
        self.max_inventory: int = 20

        # 장착 장비 {슬롯: Item | None}
        self.equipment: dict = {
            'head': None, 'body': None, 'weapon': None,
            'off_hand': None, 'accessory': None, 'feet': None,
        }

    # ── 유효 능력치 (기본 + 전체 장비 보너스) ────────────────────
    @property
    def total_attack(self) -> int:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and item.effect in ('attack_up', 'stat_up_all')
        )
        return self.attack + bonus

    @property
    def total_defense(self) -> int:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and item.effect in ('defense_up', 'stat_up_all')
        )
        heal_buf = self.heal_def_bonus if self.heal_def_ms > 0 else 0
        return self.defense + bonus + heal_buf

    def take_damage(self, amount: int):
        if self.invincible_ms > 0:
            return
        if self.cursed_ms > 0:
            amount = int(amount * 1.5)
        self.hp = max(0, self.hp - amount)

    def tick_debuffs(self, dt_ms: int):
        if self.cursed_ms > 0:
            self.cursed_ms = max(0, self.cursed_ms - dt_ms)
        if self.slowed_ms > 0:
            self.slowed_ms = max(0, self.slowed_ms - dt_ms)
        if self.feared_ms > 0:
            self.feared_ms = max(0, self.feared_ms - dt_ms)
        if self.invincible_ms > 0:
            self.invincible_ms = max(0, self.invincible_ms - dt_ms)
        if self.heal_def_ms > 0:
            self.heal_def_ms = max(0, self.heal_def_ms - dt_ms)
            if self.heal_def_ms == 0:
                self.heal_def_bonus = 0

    @property
    def total_move_speed(self) -> float:
        bonus = sum(
            item.value for item in self.equipment.values()
            if item and item.effect == 'speed_up'
        )
        spd = self.move_speed + bonus
        if self.slowed_ms > 0:
            spd *= 0.7
        return spd

    # ── 쿨다운 / 이동 간격 계산 ────────────────────────────────────
    @property
    def atk_cooldown_ms(self) -> int:
        return max(100, int(self.BASE_ATK_CD_MS / self.attack_speed))

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
        self.xp_next = int(self.xp_next * 1.6)
        self.max_hp += 8
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
    def from_save(cls, x, y, data, item_data_dict):
        from entities.item import Item
        p = cls(x, y)
        p.hp           = data['hp']
        p.max_hp       = data['max_hp']
        p.attack       = data['attack']
        p.defense      = data['defense']
        p.level        = data['level']
        p.xp           = data['xp']
        p.xp_next      = data['xp_next']
        p.gold         = data.get('gold', 0)
        p.attack_speed = data.get('attack_speed', 1.0)
        p.evasion      = data.get('evasion', 0)
        p.move_speed   = data.get('move_speed', 1.0)

        p.inventory = []
        for key in data.get('inventory', []):
            if key in item_data_dict:
                d = dict(item_data_dict[key])
                d['key'] = key
                p.inventory.append(Item(0, 0, d))

        p.equipment = {'head': None, 'body': None, 'weapon': None, 'off_hand': None, 'accessory': None, 'feet': None}
        _COMPAT = {'armor': 'body'}
        for slot, key in data.get('equipment', {}).items():
            slot = _COMPAT.get(slot, slot)
            if slot in p.equipment and key and key in item_data_dict:
                d = dict(item_data_dict[key])
                d['key'] = key
                p.equipment[slot] = Item(0, 0, d)

        return p
