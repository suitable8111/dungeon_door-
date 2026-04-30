from entities.entity import Entity


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "영웅", hp=30, max_hp=30, attack=5, defense=2)
        self.level = 1
        self.xp = 0
        self.xp_next = 15
        self.inventory = []
        self.max_inventory = 5
        self.gold = 0

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

    @classmethod
    def from_save(cls, x, y, data, item_data_dict):
        """저장 데이터로 플레이어를 복원."""
        p = cls(x, y)
        p.hp       = data['hp']
        p.max_hp   = data['max_hp']
        p.attack   = data['attack']
        p.defense  = data['defense']
        p.level    = data['level']
        p.xp       = data['xp']
        p.xp_next  = data['xp_next']
        p.gold     = data.get('gold', 0)
        p.inventory = []
        for key in data.get('inventory', []):
            if key in item_data_dict:
                from entities.item import Item
                d = dict(item_data_dict[key])
                d['key'] = key
                p.inventory.append(Item(0, 0, d))
        return p
