from core.lang import t, localized_name


class Item:
    def __init__(self, x, y, data):
        self.x = x
        self.y = y
        self.key          = data.get('key', '')
        # 다국어 이름 — name 프로퍼티가 현재 언어로 해석
        self._names       = {k: v for k, v in data.items() if k.startswith('name')}
        self.color        = tuple(data['color'])
        self.item_type    = data['type']
        self.effect       = data.get('effect', '')
        self.value        = data.get('value', 0)
        self.enhance_level = data.get('enhance_level', 0)  # 0~18
        self.sp_reduce     = data.get('sp_reduce', 0.0)    # SP 소모 경감 비율

        # ── 내구도 (방어구 4종 전용) — 피격마다 닳고 0이면 효과 정지 ──
        self.max_durability = Item.calc_max_durability(data)
        if self.max_durability > 0:
            self.durability = min(self.max_durability,
                                  data.get('durability', self.max_durability))
        else:
            self.durability = 0

    @staticmethod
    def calc_max_durability(data: dict) -> int:
        """최대 내구도. 방어구 = 40 + 방어값×8 (신발 ×10 환산),
        무기 = 80 + 공격값×12 (공격마다 닳아서 더 크게). 그 외 0."""
        t_ = data.get('type')
        v = data.get('value', 0)
        if t_ == 'weapon':
            return 80 + int(v * 12)
        if t_ not in ('armor', 'head', 'off_hand', 'boots'):
            return 0
        base = v if v >= 1 else v * 10
        return 40 + int(base * 8)

    @property
    def broken(self) -> bool:
        """파손 — 아이템은 남지만 모든 스탯 효과가 정지된다 (수리 가능)."""
        return self.max_durability > 0 and self.durability <= 0

    @property
    def name(self) -> str:
        """현재 언어의 아이템 이름 (게임 중 언어 변경 즉시 반영)."""
        return localized_name(self._names)

    # ── 장비 슬롯 이름 반환 (장비 아이템이 아니면 None) ───────────
    @property
    def equip_slot(self) -> str | None:
        if self.item_type == 'weapon':    return 'weapon'
        if self.item_type == 'armor':     return 'body'
        if self.item_type == 'head':      return 'head'
        if self.item_type == 'off_hand':  return 'off_hand'
        if self.item_type == 'accessory': return 'accessory'
        if self.item_type == 'boots':     return 'feet'
        return None

    # ── 사용 / 장착 ────────────────────────────────────────────────
    def use(self, player):
        slot = self.equip_slot
        if slot:
            return self._equip(player, slot)
        if self.effect == 'heal':
            # 고정량과 최대 HP 비례량(소형 25% / 대형 50%) 중 큰 쪽 —
            # 후반에 물약이 무의미해지지 않도록
            pct = 0.5 if self.value >= 40 else 0.25
            amount = max(self.value, int(player.max_hp * pct))
            actual = min(amount, player.max_hp - player.hp)
            player.heal(amount)
            return t('item_heal', self.name, actual)
        if self.effect == 'attack_up':
            player.attack += self.value
            return t('item_atk', self.name, self.value)
        if self.effect == 'defense_up':
            player.defense += self.value
            return t('item_def', self.name, self.value)
        if self.effect == 'stat_up_all':
            player.attack  += self.value
            player.defense += self.value
            return t('item_all', self.name, self.value, self.value)
        return t('item_use', self.name)

    _SLOT_T = {
        'weapon': 'slot_wpn_s', 'body': 'slot_body_s', 'head': 'slot_head_s',
        'off_hand': 'slot_off_s', 'accessory': 'slot_acc_s', 'feet': 'slot_feet_s',
    }

    def _equip(self, player, slot):
        slot_name = t(self._SLOT_T.get(slot, slot))

        # 이미 장착 중이면 해제
        if player.equipment[slot] is self:
            player.equipment[slot] = None
            if len(player.inventory) < player.max_inventory:
                player.inventory.append(self)
            return t('item_unequip', self.name, slot_name)

        # 이전 장비 → 인벤토리 반환
        prev = player.equipment[slot]
        if prev and prev not in player.inventory:
            if len(player.inventory) < player.max_inventory:
                player.inventory.append(prev)

        # 인벤토리에서 제거 후 장착
        if self in player.inventory:
            player.inventory.remove(self)
        player.equipment[slot] = self

        enh = f" [+{self.enhance_level}]" if self.enhance_level > 0 else ""
        return t('item_equip_msg', self.name, enh, slot_name, self.value)

    def unequip(self, player) -> str:
        slot = self.equip_slot
        if not slot or player.equipment.get(slot) is not self:
            return ""
        player.equipment[slot] = None
        if len(player.inventory) < player.max_inventory:
            player.inventory.append(self)
            return t('item_unequip_inv', self.name)
        return t('item_unequip_full', self.name)
