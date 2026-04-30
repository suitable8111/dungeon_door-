from core.lang import t


class Item:
    def __init__(self, x, y, data):
        self.x = x
        self.y = y
        self.key = data.get('key', '')
        self.name = data['name']
        self.color = tuple(data['color'])
        self.item_type = data['type']
        self.effect = data.get('effect', '')
        self.value = data.get('value', 0)

    def use(self, player):
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
