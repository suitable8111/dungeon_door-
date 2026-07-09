class Entity:
    def __init__(self, x, y, name, hp, max_hp, attack, defense):
        self.x = x
        self.y = y
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense

    def take_damage(self, amount):
        # 초과 피해 기록 — 오버킬 연출 판정용 (로직에는 영향 없음)
        self.last_overkill = max(0, amount - self.hp)
        self.hp = max(0, self.hp - amount)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self):
        return self.hp > 0
