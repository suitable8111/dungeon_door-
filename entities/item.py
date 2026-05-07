from core.lang import t


class Item:
    def __init__(self, x, y, data):
        self.x = x
        self.y = y
        self.key       = data.get('key', '')
        self.name      = data['name']
        self.color     = tuple(data['color'])
        self.item_type = data['type']
        self.effect    = data.get('effect', '')
        self.value     = data.get('value', 0)

    # ── 장비 슬롯 이름 반환 (장비 아이템이 아니면 None) ───────────
    @property
    def equip_slot(self) -> str | None:
        if self.item_type == 'weapon':    return 'weapon'
        if self.item_type == 'armor':     return 'body'
        if self.item_type == 'head':      return 'head'
        if self.item_type == 'off_hand':  return 'off_hand'
        if self.item_type == 'accessory': return 'accessory'
        return None

    # ── 사용 / 장착 ────────────────────────────────────────────────
    def use(self, player):
        slot = self.equip_slot
        if slot:
            return self._equip(player, slot)
        if self.effect == 'heal':
            actual = min(self.value, player.max_hp - player.hp)
            player.heal(self.value)
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

    _SLOT_NAMES = {
        'weapon': '무기', 'body': '갑옷', 'head': '투구',
        'off_hand': '보조무기', 'accessory': '장신구',
    }

    def _equip(self, player, slot):
        slot_name = self._SLOT_NAMES.get(slot, slot)

        # 이미 장착 중이면 해제
        if player.equipment[slot] is self:
            player.equipment[slot] = None
            if len(player.inventory) < player.max_inventory:
                player.inventory.append(self)
            return f"{self.name} {slot_name} 해제"

        # 이전 장비 → 인벤토리 반환
        prev = player.equipment[slot]
        if prev and prev not in player.inventory:
            if len(player.inventory) < player.max_inventory:
                player.inventory.append(prev)

        # 인벤토리에서 제거 후 장착
        if self in player.inventory:
            player.inventory.remove(self)
        player.equipment[slot] = self

        return f"{self.name} {slot_name} 장착! (+{self.value})"

    def unequip(self, player) -> str:
        slot = self.equip_slot
        if not slot or player.equipment.get(slot) is not self:
            return ""
        player.equipment[slot] = None
        if len(player.inventory) < player.max_inventory:
            player.inventory.append(self)
            return f"{self.name} 해제 → 인벤토리"
        return f"{self.name} 해제 (인벤토리 가득 참)"
