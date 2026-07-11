"""다국어 지원 모듈 — en / ko / ja / zh(간체) / ru.

- t(key, *args)      : UI 문자열 번역
- LocalizedDict      : 게임 데이터 dict의 name/desc 등을 현재 언어로 자동 해석
- localized_name(d)  : JSON 데이터(적/아이템)의 name_<lang> 필드 해석
"""

LANGS = ('en', 'ko', 'ja', 'zh', 'ru')

# 설정 메뉴에 표시할 각 언어의 자국어 이름
LANG_NAMES = {
    'en': 'English',
    'ko': '한국어',
    'ja': '日本語',
    'zh': '简体中文',
    'ru': 'Русский',
}

_LANG = 'en'


def set_lang(lang: str):
    global _LANG
    _LANG = lang if lang in LANGS else 'en'


def get_lang() -> str:
    return _LANG


def next_lang(lang: str) -> str:
    """설정 메뉴 순환용 — 다음 언어 코드."""
    try:
        return LANGS[(LANGS.index(lang) + 1) % len(LANGS)]
    except ValueError:
        return LANGS[0]


# ── 게임 데이터 지역화 ──────────────────────────────────────────────────────
class LocalizedDict(dict):
    """조회 시 현재 언어의 접미사 필드를 우선 반환하는 dict.

    d['name']은 lang='ja'면 d['name_ja'] → d['name_en'] → d['name'](ko 원문)
    순서로 폴백한다. 소비 코드는 일반 dict처럼 사용하면 된다.
    """
    _L_FIELDS = frozenset(('name', 'desc', 'usage', 'level_desc', 'gimmick'))

    def __getitem__(self, k):
        if k in self._L_FIELDS and _LANG != 'ko':
            v = dict.get(self, f'{k}_{_LANG}')
            if not v and _LANG != 'en':
                v = dict.get(self, f'{k}_en')
            if v:
                return v
        return dict.__getitem__(self, k)

    def get(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            return default


def localize_defs(obj):
    """dict 트리를 재귀적으로 LocalizedDict로 감싼다 (skills/theme 정의용)."""
    if isinstance(obj, dict):
        return LocalizedDict({k: localize_defs(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [localize_defs(v) for v in obj]
    return obj


def localized_name(data: dict) -> str:
    """JSON 데이터 엔트리(적/아이템)의 이름을 현재 언어로 반환."""
    if _LANG != 'ko':
        v = data.get(f'name_{_LANG}') or data.get('name_en')
        if v:
            return v
    return data['name']


# ── 번역 테이블 ────────────────────────────────────────────────────────────
_T: dict[str, dict[str, str]] = {
    # ── HUD 섹션 헤더 ──────────────────────────────────────────────────────
    'sec_hp':        {'ko': 'HP', 'en': 'HP', 'ja': 'HP', 'zh': 'HP', 'ru': 'HP'},
    'sec_stats':     {'ko': '스탯', 'en': 'Stats', 'ja': 'ステータス', 'zh': '属性', 'ru': 'Параметры'},
    'sec_inv':       {'ko': '빠른 아이템  [1-5]', 'en': 'Quick Items [1-5]', 'ja': 'アイテム [1-5]', 'zh': '快捷物品 [1-5]', 'ru': 'Предметы [1-5]'},
    'sec_equip':     {'ko': '장착 장비  [O]', 'en': 'Equipment  [O]', 'ja': '装備  [O]', 'zh': '装备  [O]', 'ru': 'Снаряжение [O]'},
    'inv_title':     {'ko': '인  벤  토  리', 'en': 'Inventory', 'ja': 'インベントリ', 'zh': '物品栏', 'ru': 'Инвентарь'},
    'inv_hint':      {'ko': '↑↓←→ 이동   Enter 사용/장착   ESC 닫기',
                      'en': '↑↓←→ Move   Enter Use/Equip   ESC Close',
                      'ja': '↑↓←→ 移動   Enter 使用/装備   ESC 閉じる',
                      'zh': '↑↓←→ 移动   Enter 使用/装备   ESC 关闭',
                      'ru': '↑↓←→ Выбор   Enter Исп./Надеть   ESC Закрыть'},
    'equip_title':   {'ko': '장  비  장  착', 'en': 'Equipment', 'ja': '装備', 'zh': '装备', 'ru': 'Снаряжение'},
    'equip_hint':    {'ko': '↑↓←→ 이동   Enter 해제   ESC 닫기',
                      'en': '↑↓←→ Move   Enter Unequip   ESC Close',
                      'ja': '↑↓←→ 移動   Enter 解除   ESC 閉じる',
                      'zh': '↑↓←→ 移动   Enter 卸下   ESC 关闭',
                      'ru': '↑↓←→ Выбор   Enter Снять   ESC Закрыть'},
    'equip_none':    {'ko': '-- 없음 --', 'en': '-- None --', 'ja': '-- なし --', 'zh': '-- 无 --', 'ru': '-- Пусто --'},
    'slot_weapon':   {'ko': '주  무  기', 'en': 'Weapon', 'ja': '武器', 'zh': '武器', 'ru': 'Оружие'},
    'slot_armor':    {'ko': '갑  옷', 'en': 'Armor', 'ja': '鎧', 'zh': '护甲', 'ru': 'Броня'},
    'slot_head':     {'ko': '머  리', 'en': 'Head', 'ja': '頭', 'zh': '头部', 'ru': 'Голова'},
    'slot_body':     {'ko': '몸  통', 'en': 'Body', 'ja': '胴体', 'zh': '身体', 'ru': 'Тело'},
    'slot_off_hand': {'ko': '보조무기', 'en': 'Off-Hand', 'ja': '盾・補助', 'zh': '副手', 'ru': 'Второе оружие'},
    'slot_accessory':{'ko': '장신구', 'en': 'Accessory', 'ja': 'アクセサリー', 'zh': '饰品', 'ru': 'Аксессуар'},
    'slot_feet':     {'ko': '신  발', 'en': 'Boots', 'ja': '靴', 'zh': '鞋子', 'ru': 'Обувь'},
    'sec_skills':    {'ko': '스킬  [W/A/S/D]', 'en': 'Skills [W/A/S/D]', 'ja': 'スキル [W/A/S/D]', 'zh': '技能 [W/A/S/D]', 'ru': 'Навыки [W/A/S/D]'},
    'sec_combo':     {'ko': '강화 스킬', 'en': 'Enhanced Skills', 'ja': '強化スキル', 'zh': '强化技能', 'ru': 'Усиленные навыки'},
    'sec_arcane_sp': {'ko': '오의 SP', 'en': 'Arcane SP', 'ja': '奥義SP', 'zh': '奥义SP', 'ru': 'Тайная SP'},
    'sec_ultimate':  {'ko': '궁극기  [R]', 'en': 'Ultimate [R]', 'ja': '必殺技 [R]', 'zh': '终极技 [R]', 'ru': 'Ультимейт [R]'},
    'sec_controls':  {'ko': '조작법', 'en': 'Controls', 'ja': '操作方法', 'zh': '操作说明', 'ru': 'Управление'},
    'sec_minimap':   {'ko': '미니맵', 'en': 'Minimap', 'ja': 'ミニマップ', 'zh': '小地图', 'ru': 'Миникарта'},
    'inv_empty':     {'ko': '---', 'en': '---', 'ja': '---', 'zh': '---', 'ru': '---'},

    # ── 조작법 힌트 ────────────────────────────────────────────────────────
    'ctrl_move':    {'ko': '↑↓←→', 'en': 'Arrows', 'ja': '↑↓←→', 'zh': '↑↓←→', 'ru': '↑↓←→'},
    'ctrl_move_d':  {'ko': '이동', 'en': 'Move', 'ja': '移動', 'zh': '移动', 'ru': 'Ходьба'},
    'ctrl_atk':     {'ko': 'Space', 'en': 'Space', 'ja': 'Space', 'zh': 'Space', 'ru': 'Space'},
    'ctrl_atk_d':   {'ko': '공격', 'en': 'Attack', 'ja': '攻撃', 'zh': '攻击', 'ru': 'Атака'},
    'ctrl_skill':   {'ko': 'W/A/S/D', 'en': 'W/A/S/D', 'ja': 'W/A/S/D', 'zh': 'W/A/S/D', 'ru': 'W/A/S/D'},
    'ctrl_skill_d': {'ko': '스킬', 'en': 'Skills', 'ja': 'スキル', 'zh': '技能', 'ru': 'Навыки'},
    'ctrl_combo':   {'ko': 'Ctrl+W/A/S/D', 'en': 'Ctrl+W/A/S/D', 'ja': 'Ctrl+W/A/S/D', 'zh': 'Ctrl+W/A/S/D', 'ru': 'Ctrl+W/A/S/D'},
    'ctrl_combo_d': {'ko': '강화 스킬', 'en': 'Enhanced', 'ja': '強化スキル', 'zh': '强化技', 'ru': 'Усиленные'},
    'ctrl_item':    {'ko': '1-5', 'en': '1-5', 'ja': '1-5', 'zh': '1-5', 'ru': '1-5'},
    'ctrl_item_d':  {'ko': '아이템', 'en': 'Items', 'ja': 'アイテム', 'zh': '物品', 'ru': 'Предметы'},
    'ctrl_inv':     {'ko': 'I', 'en': 'I', 'ja': 'I', 'zh': 'I', 'ru': 'I'},
    'ctrl_inv_d':   {'ko': '인벤토리', 'en': 'Inventory', 'ja': 'インベントリ', 'zh': '物品栏', 'ru': 'Инвентарь'},
    'ctrl_equip':   {'ko': 'O', 'en': 'O', 'ja': 'O', 'zh': 'O', 'ru': 'O'},
    'ctrl_equip_d': {'ko': '장비', 'en': 'Equipment', 'ja': '装備', 'zh': '装备', 'ru': 'Снаряжение'},
    'ctrl_esc':     {'ko': 'ESC', 'en': 'ESC', 'ja': 'ESC', 'zh': 'ESC', 'ru': 'ESC'},
    'ctrl_esc_d':   {'ko': '저장/메뉴', 'en': 'Save/Menu', 'ja': '保存/メニュー', 'zh': '保存/菜单', 'ru': 'Сохр./Меню'},

    # ── 단일 스킬 이름 / 설명 (HUD 짧은 표기) ─────────────────────────────
    'skill_w_name': {'ko': '섬광 돌진', 'en': 'Flash Dash', 'ja': '閃光ダッシュ', 'zh': '闪光冲刺', 'ru': 'Рывок-вспышка'},
    'skill_w_desc': {'ko': '3칸+경직', 'en': '3-tile dash+stagger', 'ja': '3マス+硬直', 'zh': '3格+僵直', 'ru': '3 клетки+оглушение'},
    'skill_a_name': {'ko': '강철 회오리', 'en': 'Steel Whirl', 'ja': '鋼鉄の旋風', 'zh': '钢铁旋风', 'ru': 'Стальной вихрь'},
    'skill_a_desc': {'ko': '8방향 휩쓸기', 'en': '8-dir sweep', 'ja': '8方向薙ぎ', 'zh': '8向横扫', 'ru': 'Удар в 8 сторон'},
    'skill_s_name': {'ko': '재생의 숨결', 'en': 'Regen Breath', 'ja': '再生の息吹', 'zh': '再生之息', 'ru': 'Дыхание жизни'},
    'skill_s_desc': {'ko': 'HP25%+방어', 'en': '+25% HP+DEF', 'ja': 'HP25%+防御', 'zh': 'HP25%+防御', 'ru': '+25% HP+Защита'},
    'skill_d_name': {'ko': '심판의 일격', 'en': 'Judgment Strike', 'ja': '審判の一撃', 'zh': '审判一击', 'ru': 'Удар правосудия'},
    'skill_d_desc': {'ko': '2.5배 강타', 'en': '250% ATK', 'ja': '2.5倍強打', 'zh': '2.5倍重击', 'ru': '250% АТК'},
    # 이전 키 유지 (하위 호환)
    'skill_q_name': {'ko': '돌진', 'en': 'Dash', 'ja': 'ダッシュ', 'zh': '冲刺', 'ru': 'Рывок'},
    'skill_q_desc': {'ko': '3칸 전진', 'en': '3-tile dash', 'ja': '3マス前進', 'zh': '前进3格', 'ru': 'Рывок на 3 клетки'},
    'skill_e_name': {'ko': '회오리', 'en': 'Whirl', 'ja': '旋風', 'zh': '旋风', 'ru': 'Вихрь'},
    'skill_e_desc': {'ko': '8방향 공격', 'en': '8-dir atk', 'ja': '8方向攻撃', 'zh': '8向攻击', 'ru': 'Атака в 8 сторон'},
    'skill_f_name': {'ko': '치유', 'en': 'Heal', 'ja': '治癒', 'zh': '治疗', 'ru': 'Лечение'},
    'skill_f_desc': {'ko': 'HP 30%', 'en': '+30% HP', 'ja': 'HP 30%', 'zh': 'HP 30%', 'ru': '+30% HP'},

    # ── 메인 메뉴 ──────────────────────────────────────────────────────────
    'menu_new':      {'ko': '새  게  임', 'en': 'New  Game', 'ja': 'ニューゲーム', 'zh': '新游戏', 'ru': 'Новая игра'},
    'menu_cont':     {'ko': '이어하기', 'en': 'Continue', 'ja': 'つづきから', 'zh': '继续游戏', 'ru': 'Продолжить'},
    'menu_cont_f':   {'ko': '이어하기   B{}F', 'en': 'Continue  B{}F', 'ja': 'つづきから  B{}F', 'zh': '继续游戏  B{}F', 'ru': 'Продолжить  B{}F'},
    'menu_settings': {'ko': '설정', 'en': 'Settings', 'ja': '設定', 'zh': '设置', 'ru': 'Настройки'},
    'menu_quit':     {'ko': '종료', 'en': 'Quit', 'ja': '終了', 'zh': '退出', 'ru': 'Выход'},
    'menu_hint':     {'ko': '↑↓ 선택   Enter 확인   ESC 종료',
                      'en': '↑↓ Select   Enter OK   ESC Quit',
                      'ja': '↑↓ 選択   Enter 決定   ESC 終了',
                      'zh': '↑↓ 选择   Enter 确认   ESC 退出',
                      'ru': '↑↓ Выбор   Enter ОК   ESC Выход'},

    # ── 메뉴 설정 패널 ─────────────────────────────────────────────────────
    'settings_title': {'ko': '설정', 'en': 'Settings', 'ja': '設定', 'zh': '设置', 'ru': 'Настройки'},
    'settings_back':  {'ko': '뒤로', 'en': 'Back', 'ja': '戻る', 'zh': '返回', 'ru': 'Назад'},
    'settings_hint':  {'ko': '↑↓ 선택   ◄► 조절   ESC 뒤로',
                       'en': '↑↓ Select   ◄► Adjust   ESC Back',
                       'ja': '↑↓ 選択   ◄► 調整   ESC 戻る',
                       'zh': '↑↓ 选择   ◄► 调整   ESC 返回',
                       'ru': '↑↓ Выбор   ◄► Изменить   ESC Назад'},

    # ── 일시정지 메뉴 ──────────────────────────────────────────────────────
    'pause_title':  {'ko': '─ 일시 정지 ─', 'en': '─  Paused  ─', 'ja': '─ ポーズ ─', 'zh': '─ 暂停 ─', 'ru': '─  Пауза  ─'},
    'pause_resume': {'ko': '계속하기', 'en': 'Resume', 'ja': '再開', 'zh': '继续', 'ru': 'Продолжить'},
    'pause_save':   {'ko': '저장하기', 'en': 'Save Game', 'ja': 'セーブ', 'zh': '保存游戏', 'ru': 'Сохранить'},
    'pause_bgm':    {'ko': 'BGM 볼륨', 'en': 'BGM Volume', 'ja': 'BGM音量', 'zh': 'BGM音量', 'ru': 'Громкость BGM'},
    'pause_sfx':    {'ko': 'SFX 볼륨', 'en': 'SFX Volume', 'ja': 'SFX音量', 'zh': '音效音量', 'ru': 'Громкость SFX'},
    'pause_fs':     {'ko': '전체화면', 'en': 'Fullscreen', 'ja': 'フルスクリーン', 'zh': '全屏', 'ru': 'Полный экран'},
    'pause_fs_on':  {'ko': 'ON', 'en': 'ON', 'ja': 'ON', 'zh': '开', 'ru': 'ВКЛ'},
    'pause_fs_off': {'ko': 'OFF', 'en': 'OFF', 'ja': 'OFF', 'zh': '关', 'ru': 'ВЫКЛ'},
    'pause_lang':   {'ko': '언어', 'en': 'Language', 'ja': '言語', 'zh': '语言', 'ru': 'Язык'},
    # lang_ko/lang_en은 하위 호환용 — 새 코드는 LANG_NAMES 사용
    'lang_ko':      {'ko': '한국어', 'en': 'Korean', 'ja': '韓国語', 'zh': '韩语', 'ru': 'Корейский'},
    'lang_en':      {'ko': 'English', 'en': 'English', 'ja': '英語', 'zh': '英语', 'ru': 'Английский'},
    'pause_title_': {'ko': '타이틀로', 'en': 'Title Screen', 'ja': 'タイトルへ', 'zh': '回到标题', 'ru': 'В главное меню'},
    'pause_quit':   {'ko': '종료', 'en': 'Quit', 'ja': '終了', 'zh': '退出', 'ru': 'Выход'},
    'pause_hint':   {'ko': 'ESC 닫기    Space / Enter 선택',
                     'en': 'ESC Close   Space / Enter Select',
                     'ja': 'ESC 閉じる   Space / Enter 選択',
                     'zh': 'ESC 关闭   Space / Enter 选择',
                     'ru': 'ESC Закрыть   Space / Enter Выбрать'},
    'adj_hint':     {'ko': '◄ ► 조절', 'en': '◄ ► Adjust', 'ja': '◄ ► 調整', 'zh': '◄ ► 调整', 'ru': '◄ ► Изменить'},
    'save_hint':    {'ko': 'Enter 저장', 'en': 'Enter Save', 'ja': 'Enter セーブ', 'zh': 'Enter 保存', 'ru': 'Enter Сохранить'},

    # ── 게임 오버 ──────────────────────────────────────────────────────────
    'gameover':     {'ko': 'GAME OVER', 'en': 'GAME OVER', 'ja': 'GAME OVER', 'zh': 'GAME OVER', 'ru': 'GAME OVER'},
    'survived':     {'ko': 'Floor {} 까지 생존했습니다.', 'en': 'Survived to Floor {}.',
                     'ja': 'Floor {} まで生き延びた。', 'zh': '存活至第 {} 层。', 'ru': 'Вы дошли до этажа {}.'},
    'best_rec':     {'ko': '최고 기록  Floor {}  킬 {}  G {}', 'en': 'Best  Floor {}  Kills {}  G {}',
                     'ja': '最高記録  Floor {}  キル {}  G {}', 'zh': '最佳纪录  层 {}  击杀 {}  G {}',
                     'ru': 'Рекорд  Этаж {}  Убийств {}  G {}'},
    'total_runs':   {'ko': '총 {}회 플레이', 'en': '{} total runs', 'ja': 'プレイ回数 {}回', 'zh': '共 {} 次挑战', 'ru': 'Всего попыток: {}'},
    'go_hint':      {'ko': '[R] 재시작    [ESC] 종료', 'en': '[R] Restart    [ESC] Quit',
                     'ja': '[R] リトライ    [ESC] 終了', 'zh': '[R] 重新开始    [ESC] 退出',
                     'ru': '[R] Заново    [ESC] Выход'},

    # ── 상점 ───────────────────────────────────────────────────────────────
    'shop_title':   {'ko': '상  점', 'en': 'Shop', 'ja': 'ショップ', 'zh': '商店', 'ru': 'Магазин'},
    'shop_gold':    {'ko': '보유 골드: {} G', 'en': 'Gold: {} G', 'ja': '所持ゴールド: {} G', 'zh': '持有金币: {} G', 'ru': 'Золото: {} G'},
    'shop_empty':   {'ko': '품절입니다.', 'en': 'Sold out.', 'ja': '売り切れです。', 'zh': '已售罄。', 'ru': 'Распродано.'},
    'shop_hint':    {'ko': '[1-5] 구매    [ESC] 나가기', 'en': '[1-5] Buy    [ESC] Exit',
                     'ja': '[1-5] 購入    [ESC] 出る', 'zh': '[1-5] 购买    [ESC] 离开',
                     'ru': '[1-5] Купить    [ESC] Выйти'},

    # ── 보스바 ─────────────────────────────────────────────────────────────
    'boss_bar':     {'ko': '★ BOSS  {}   {} / {}', 'en': '★ BOSS  {}   {} / {}',
                     'ja': '★ BOSS  {}   {} / {}', 'zh': '★ BOSS  {}   {} / {}', 'ru': '★ БОСС  {}   {} / {}'},

    # ── 인게임 메시지 ──────────────────────────────────────────────────────
    'welcome':      {'ko': 'Dungeon Door에 오신 걸 환영합니다!', 'en': 'Welcome to Dungeon Door!',
                     'ja': 'Dungeon Doorへようこそ!', 'zh': '欢迎来到 Dungeon Door!', 'ru': 'Добро пожаловать в Dungeon Door!'},
    'exhausted':    {'ko': '⚠ 지쳤다... 숨을 고르자 (SP 부족)',
                     'en': '⚠ Exhausted... catch your breath (no SP)',
                     'ja': '⚠ 疲れた... 息を整えろ (SP不足)',
                     'zh': '⚠ 太累了... 喘口气 (SP不足)',
                     'ru': '⚠ Выдохся... переведи дух (нет SP)'},
    'combat_hint':  {'ko': 'Space 연타: 3단 콤보 / 방향+Space: 런지·백스텝 / 후딜 중 스킬: 드라이브 캔슬(◆)',
                     'en': 'Space rapid: 3-hit combo / Dir+Space: Lunge·Backstep / Skill in recovery: Drive Cancel (◆)',
                     'ja': 'Space連打: 3段コンボ / 方向+Space: 突進·後退斬り / 硬直中スキル: ドライブキャンセル(◆)',
                     'zh': '连按Space: 三段连击 / 方向+Space: 突刺·后撤斩 / 后摇中技能: 驱动取消(◆)',
                     'ru': 'Space подряд: комбо ×3 / Напр.+Space: выпад·отскок / Навык в откате: драйв-отмена (◆)'},
    'wasd_hint':    {'ko': '↑↓←→ 이동 / Space 공격 / W·A·S·D 스킬 / ESC 저장·메뉴',
                     'en': 'Arrows Move / Space Attack / W·A·S·D Skills / ESC Save·Menu',
                     'ja': '↑↓←→ 移動 / Space 攻撃 / W·A·S·D スキル / ESC 保存·メニュー',
                     'zh': '↑↓←→ 移动 / Space 攻击 / W·A·S·D 技能 / ESC 保存·菜单',
                     'ru': '↑↓←→ Ходьба / Space Атака / W·A·S·D Навыки / ESC Сохр.·Меню'},
    'floor_arrive': {'ko': 'Floor {}에 도착했습니다.', 'en': 'Arrived at Floor {}.',
                     'ja': 'Floor {} に到着した。', 'zh': '到达第 {} 层。', 'ru': 'Вы на этаже {}.'},
    'floor_cont':   {'ko': 'Floor {} 에서 계속합니다.', 'en': 'Continuing from Floor {}.',
                     'ja': 'Floor {} から再開。', 'zh': '从第 {} 层继续。', 'ru': 'Продолжаем с этажа {}.'},
    'boss_incoming':{'ko': '★ 보스가 기다리고 있다!', 'en': '★ The boss awaits!',
                     'ja': '★ ボスが待ち構えている!', 'zh': '★ 首领在等着你!', 'ru': '★ Впереди босс!'},
    'shop_floor':   {'ko': '상점이 있는 층입니다.', 'en': 'A shop is on this floor.',
                     'ja': 'この階にはショップがある。', 'zh': '这一层有商店。', 'ru': 'На этом этаже есть магазин.'},
    'auto_saved':   {'ko': '✓ 자동 저장됨', 'en': '✓ Auto-saved', 'ja': '✓ オートセーブ完了', 'zh': '✓ 已自动保存', 'ru': '✓ Автосохранение'},
    'saved':        {'ko': '✓ 저장됨', 'en': '✓ Saved', 'ja': '✓ セーブ完了', 'zh': '✓ 已保存', 'ru': '✓ Сохранено'},

    # ── 전투 메시지 ────────────────────────────────────────────────────────
    'crit_hit':     {'ko': '★ 치명타! {}에게 {} 피해!', 'en': '★ Crit! {} hit for {}!',
                     'ja': '★ 会心! {}に{}ダメージ!', 'zh': '★ 暴击! 对{}造成{}伤害!', 'ru': '★ Крит! {} получает {} урона!'},
    'normal_hit':   {'ko': '▶ {}에게 {} 피해', 'en': '▶ {} hit for {}',
                     'ja': '▶ {}に{}ダメージ', 'zh': '▶ 对{}造成{}伤害', 'ru': '▶ {} получает {} урона'},
    'kill_gold':    {'ko': '{} 처치! +{} XP  +{} G', 'en': '{} killed! +{} XP  +{} G',
                     'ja': '{}を倒した! +{} XP  +{} G', 'zh': '击杀{}! +{} XP  +{} G', 'ru': '{} убит! +{} XP  +{} G'},
    'kill':         {'ko': '{} 처치! +{} XP', 'en': '{} killed! +{} XP',
                     'ja': '{}を倒した! +{} XP', 'zh': '击杀{}! +{} XP', 'ru': '{} убит! +{} XP'},
    'levelup':      {'ko': '레벨업! Lv.{}  HP 회복!', 'en': 'Level Up! Lv.{}  HP restored!',
                     'ja': 'レベルアップ! Lv.{}  HP回復!', 'zh': '升级! Lv.{}  HP已恢复!', 'ru': 'Новый уровень! Ур.{}  HP восстановлено!'},
    'pickup':       {'ko': '{} 획득!', 'en': '{} picked up!', 'ja': '{}を手に入れた!', 'zh': '获得{}!', 'ru': 'Получено: {}!'},
    'inv_full':     {'ko': '인벤토리가 가득 찼습니다!', 'en': 'Inventory is full!',
                     'ja': 'インベントリがいっぱいだ!', 'zh': '物品栏已满!', 'ru': 'Инвентарь полон!'},
    'buy_ok':       {'ko': '{} 구매! -{} G', 'en': '{} bought! -{} G',
                     'ja': '{}を購入! -{} G', 'zh': '购买{}! -{} G', 'ru': 'Куплено: {}! -{} G'},
    'no_gold':      {'ko': '골드가 부족합니다!', 'en': 'Not enough gold!',
                     'ja': 'ゴールドが足りない!', 'zh': '金币不足!', 'ru': 'Недостаточно золота!'},
    'teleport':     {'ko': '✦ 텔레포트!', 'en': '✦ Teleport!', 'ja': '✦ テレポート!', 'zh': '✦ 传送!', 'ru': '✦ Телепорт!'},
    'skill_cd':     {'ko': '스킬 재충전 중... ({:.1f}s)', 'en': 'Skill on cooldown... ({:.1f}s)',
                     'ja': 'スキル再充填中... ({:.1f}s)', 'zh': '技能冷却中... ({:.1f}s)', 'ru': 'Навык перезаряжается... ({:.1f}с)'},
    'skill_dash':   {'ko': '⚡ 돌진! {}칸', 'en': '⚡ Dash! {} tiles',
                     'ja': '⚡ ダッシュ! {}マス', 'zh': '⚡ 冲刺! {}格', 'ru': '⚡ Рывок! {} кл.'},
    'skill_whirl_h':{'ko': '🌀 회오리! {}마리 타격', 'en': '🌀 Whirl! Hit {}',
                     'ja': '🌀 旋風! {}体に命中', 'zh': '🌀 旋风! 命中{}个', 'ru': '🌀 Вихрь! Задето: {}'},
    'skill_whirl_m':{'ko': '🌀 회오리 — 적 없음', 'en': '🌀 Whirl — no enemies',
                     'ja': '🌀 旋風 — 敵なし', 'zh': '🌀 旋风 — 无敌人', 'ru': '🌀 Вихрь — врагов нет'},
    'skill_heal':   {'ko': '✨ 치유! HP +{}', 'en': '✨ Heal! HP +{}',
                     'ja': '✨ 治癒! HP +{}', 'zh': '✨ 治疗! HP +{}', 'ru': '✨ Лечение! HP +{}'},
    'boss_clear':   {'ko': '★ 보스를 처치했습니다! 계단이 나타났습니다!', 'en': '★ Boss defeated! Stairs appeared!',
                     'ja': '★ ボスを倒した! 階段が現れた!', 'zh': '★ 击败首领! 楼梯出现了!',
                     'ru': '★ Босс повержен! Появилась лестница!'},

    # ── 스킬 전투 메시지 추가 ──────────────────────────────────────────────
    'skill_power':      {'ko': '💥 강타! {}에게 {} 피해', 'en': '💥 Power! Hit {} for {}',
                         'ja': '💥 強打! {}に{}ダメージ', 'zh': '💥 重击! 对{}造成{}伤害', 'ru': '💥 Мощь! {} получает {}'},
    'skill_power_miss': {'ko': '💥 강타! 빗나감', 'en': '💥 Power Strike! Miss',
                         'ja': '💥 強打! 空振り', 'zh': '💥 重击! 落空', 'ru': '💥 Мощный удар! Промах'},
    'skill_fireball':   {'ko': '🔥 파이어볼! {}에게 {} 피해', 'en': '🔥 Fireball! Hit {} for {}',
                         'ja': '🔥 ファイアボール! {}に{}ダメージ', 'zh': '🔥 火球! 对{}造成{}伤害', 'ru': '🔥 Огненный шар! {} получает {}'},
    'skill_fireball_m': {'ko': '🔥 파이어볼! 빗나감', 'en': '🔥 Fireball! Miss',
                         'ja': '🔥 ファイアボール! 空振り', 'zh': '🔥 火球! 落空', 'ru': '🔥 Огненный шар! Промах'},
    'skill_thunder':    {'ko': '⚡ 천둥격! {}마리 타격', 'en': '⚡ Thunder! Hit {}',
                         'ja': '⚡ 雷撃! {}体に命中', 'zh': '⚡ 雷击! 命中{}个', 'ru': '⚡ Гром! Задето: {}'},
    'skill_thunder_m':  {'ko': '⚡ 천둥격! 적 없음', 'en': '⚡ Thunder! No targets',
                         'ja': '⚡ 雷撃! 敵なし', 'zh': '⚡ 雷击! 无目标', 'ru': '⚡ Гром! Целей нет'},
    'skill_frost':      {'ko': '❄ 냉기 폭발! {}마리 타격', 'en': '❄ Frost! Hit {}',
                         'ja': '❄ 冷気爆発! {}体に命中', 'zh': '❄ 冰霜爆发! 命中{}个', 'ru': '❄ Мороз! Задето: {}'},
    'skill_frost_m':    {'ko': '❄ 냉기 폭발! 적 없음', 'en': '❄ Frost! No targets',
                         'ja': '❄ 冷気爆発! 敵なし', 'zh': '❄ 冰霜爆发! 无目标', 'ru': '❄ Мороз! Целей нет'},
    'skill_wind':       {'ko': '💨 바람 칼날! {}마리 관통', 'en': '💨 Wind! Pierce {}',
                         'ja': '💨 風の刃! {}体を貫通', 'zh': '💨 风刃! 穿透{}个', 'ru': '💨 Ветер! Пронзено: {}'},
    'skill_wind_m':     {'ko': '💨 바람 칼날! 빗나감', 'en': '💨 Wind Blade! Miss',
                         'ja': '💨 風の刃! 空振り', 'zh': '💨 风刃! 落空', 'ru': '💨 Клинок ветра! Промах'},
    'skill_fortify':    {'ko': '✨ 강화술! 공속 +{} 방어 +{} ({}초)', 'en': '✨ Fortify! Spd +{} Def +{} ({}s)',
                         'ja': '✨ 強化術! 攻速+{} 防御+{} ({}秒)', 'zh': '✨ 强化术! 攻速+{} 防御+{} ({}秒)',
                         'ru': '✨ Усиление! Скор.+{} Защ.+{} ({}с)'},
    'skill_fortify_end':{'ko': '강화술 효과가 사라졌다.', 'en': 'Fortify faded.',
                         'ja': '強化術の効果が切れた。', 'zh': '强化术效果消失了。', 'ru': 'Усиление рассеялось.'},

    # ── 버닝 스테이지 ─────────────────────────────────────────────────────
    'burning_enter':    {'ko': '🔥 버닝 스테이지! 60초를 버텨라!', 'en': '🔥 Burning Stage! Survive 60 seconds!',
                         'ja': '🔥 バーニングステージ! 60秒生き延びろ!', 'zh': '🔥 燃烧舞台! 坚持60秒!',
                         'ru': '🔥 Пылающая арена! Продержись 60 секунд!'},
    'burning_wave':     {'ko': '🔥 파도 {}!', 'en': '🔥 Wave {}!', 'ja': '🔥 ウェーブ {}!', 'zh': '🔥 第{}波!', 'ru': '🔥 Волна {}!'},
    'burning_survived': {'ko': '🏆 생존! 보스 스테이지로 이동!', 'en': '🏆 Survived! Moving to Boss Stage!',
                         'ja': '🏆 生存! ボスステージへ!', 'zh': '🏆 存活! 前往首领关卡!', 'ru': '🏆 Выжил! Вперёд к боссу!'},
    'burning_failed':   {'ko': '💀 쓰러졌다. 현재 층으로 복귀.', 'en': '💀 Defeated. Returning to current floor.',
                         'ja': '💀 倒れた。元の階へ戻る。', 'zh': '💀 倒下了。返回当前层。', 'ru': '💀 Поражение. Возврат на этаж.'},
    'burning_10sec':    {'ko': '⚠ 10초 남았다!', 'en': '⚠ 10 seconds left!',
                         'ja': '⚠ 残り10秒!', 'zh': '⚠ 还剩10秒!', 'ru': '⚠ Осталось 10 секунд!'},

    # ── 강화 스킬 해금 메시지 ─────────────────────────────────────────────
    'combo_unlock':     {'ko': '★ {} 해금!', 'en': '★ {} unlocked!',
                         'ja': '★ {} 解放!', 'zh': '★ {} 已解锁!', 'ru': '★ {} — открыто!'},
    'combo_need_level': {'ko': '{} 스킬북 획득! (Lv.{} 달성 시 해금)', 'en': '{} skill book! (Unlock at Lv.{})',
                         'ja': '{}のスキルブック入手! (Lv.{}で解放)', 'zh': '获得{}技能书! (Lv.{}解锁)',
                         'ru': 'Книга навыка {}! (Откроется на ур.{})'},
    'combo_need_skill_level': {'ko': '{} 스킬북 획득! (W/A/S/D 스킬 Lv.{} 달성 시 해금)',
                               'en': '{} skill book! (Unlock when skills reach Lv.{})',
                               'ja': '{}のスキルブック入手! (スキルLv.{}で解放)',
                               'zh': '获得{}技能书! (技能达到Lv.{}解锁)',
                               'ru': 'Книга навыка {}! (Нужны навыки ур.{})'},
    'skill_need_level': {'ko': '{} 사용 불가 — Lv.{} 필요', 'en': '{} unavailable — requires Lv.{}',
                         'ja': '{}は使用不可 — Lv.{}が必要', 'zh': '{}不可用 — 需要Lv.{}',
                         'ru': '{} недоступен — нужен ур.{}'},

    # ── 장비 강화 ──────────────────────────────────────────────────────────
    'enhance_stone_pickup': {'ko': '강화석 획득! (보유: {}개)', 'en': 'Enhancement Stone! (Have: {})',
                             'ja': '強化石を入手! (所持: {}個)', 'zh': '获得强化石! (持有: {})',
                             'ru': 'Камень усиления! (Всего: {})'},
    'enhance_success':      {'ko': '✦ {} 강화 성공! [+{}]', 'en': '✦ {} enhanced! [+{}]',
                             'ja': '✦ {}の強化成功! [+{}]', 'zh': '✦ {}强化成功! [+{}]',
                             'ru': '✦ {} улучшено! [+{}]'},
    'enhance_fail':         {'ko': '▲ {} 강화 실패... [+{}] 유지', 'en': '▲ {} failed... stays [+{}]',
                             'ja': '▲ {}の強化失敗... [+{}]のまま', 'zh': '▲ {}强化失败... 保持[+{}]',
                             'ru': '▲ {} — неудача... остаётся [+{}]'},
    'enhance_no_item':      {'ko': '강화할 장비가 없습니다.', 'en': 'No item equipped in this slot.',
                             'ja': '強化する装備がない。', 'zh': '该槽位没有装备。', 'ru': 'В этом слоте нет предмета.'},
    'enhance_no_stone':     {'ko': '강화석이 없습니다!', 'en': 'No enhancement stones!',
                             'ja': '強化石がない!', 'zh': '没有强化石!', 'ru': 'Нет камней усиления!'},
    'enhance_max':          {'ko': '{} 최대 강화 달성! (+18)', 'en': '{} is at max enhancement! (+18)',
                             'ja': '{}は最大強化済み! (+18)', 'zh': '{}已达最大强化! (+18)',
                             'ru': '{} усилено до предела! (+18)'},
    'combo_no_book':    {'ko': '{} — 스킬북을 찾으세요', 'en': '{} — find the skill book',
                         'ja': '{} — スキルブックを探せ', 'zh': '{} — 寻找技能书', 'ru': '{} — найдите книгу навыка'},
    'combo_no_unlock':  {'ko': '{} — 스킬북 + Lv.{} 필요', 'en': '{} — need book + Lv.{}',
                         'ja': '{} — ブック + Lv.{}が必要', 'zh': '{} — 需要技能书 + Lv.{}',
                         'ru': '{} — нужна книга + ур.{}'},

    # ── 스킬 강화 패널 ────────────────────────────────────────────────────
    'upg_title':   {'ko': '스킬  강화', 'en': 'Skill  Upgrade', 'ja': 'スキル強化', 'zh': '技能强化', 'ru': 'Прокачка навыка'},
    'upg_sp':      {'ko': 'SP  {}', 'en': 'SP  {}', 'ja': 'SP  {}', 'zh': 'SP  {}', 'ru': 'SP  {}'},
    'upg_hint':    {'ko': '↑↓ 선택   Space 강화   ESC 닫기', 'en': '↑↓ Select   Space Upgrade   ESC Close',
                    'ja': '↑↓ 選択   Space 強化   ESC 閉じる', 'zh': '↑↓ 选择   Space 强化   ESC 关闭',
                    'ru': '↑↓ Выбор   Space Прокачать   ESC Закрыть'},
    'upg_confirm': {'ko': 'Space: 강화', 'en': 'Space: Upgrade', 'ja': 'Space: 強化', 'zh': 'Space: 强化', 'ru': 'Space: Прокачать'},
    'upg_max':     {'ko': '최대 레벨', 'en': 'MAX Level', 'ja': '最大レベル', 'zh': '已满级', 'ru': 'МАКС. уровень'},
    'upg_done':    {'ko': '{} 강화! Lv.{}', 'en': '{} upgraded! Lv.{}',
                    'ja': '{}を強化! Lv.{}', 'zh': '{}强化! Lv.{}', 'ru': '{} улучшен! Ур.{}'},
    'upg_no_sp':   {'ko': 'SP 부족!', 'en': 'No SP!', 'ja': 'SP不足!', 'zh': 'SP不足!', 'ru': 'Не хватает SP!'},
    'sp_badge':    {'ko': '★ SP {}  [U] 스킬 강화', 'en': '★ SP {}  [U] Upgrade',
                    'ja': '★ SP {}  [U] スキル強化', 'zh': '★ SP {}  [U] 技能强化', 'ru': '★ SP {}  [U] Прокачка'},
    'ctrl_upg':    {'ko': 'U', 'en': 'U', 'ja': 'U', 'zh': 'U', 'ru': 'U'},
    'ctrl_upg_d':  {'ko': '스킬 강화', 'en': 'Skill Upg', 'ja': 'スキル強化', 'zh': '技能强化', 'ru': 'Прокачка'},

    # ── 스킬 도감 (K키) ──────────────────────────────────────────────────
    'sb_title':          {'ko': '스킬 도감', 'en': 'Skill Book', 'ja': 'スキル図鑑', 'zh': '技能图鉴', 'ru': 'Книга навыков'},
    'sb_sp':             {'ko': 'SP: {}포인트', 'en': 'SP: {}', 'ja': 'SP: {}', 'zh': 'SP: {}', 'ru': 'SP: {}'},
    'sb_hint':           {'ko': '↑↓ 선택   Enter 장착변경   U 스킬업   1위력 2신속 3절약 4오의 인챈트   K/ESC 닫기',
                          'en': '↑↓ Select   Enter Equip   U SkillUp   1-4 Enchant   K/ESC Close',
                          'ja': '↑↓ 選択   Enter 装備変更   U 強化   1-4 エンチャント   K/ESC 閉じる',
                          'zh': '↑↓ 选择   Enter 更换装备   U 升级   1-4 附魔   K/ESC 关闭',
                          'ru': '↑↓ Выбор   Enter Экипировать   U Прокачка   1-4 Чары   K/ESC Закрыть'},
    'sb_equip_hint':     {'ko': '↑↓ 선택   Enter 장착 확정   ESC 취소',
                          'en': '↑↓ Select   Enter Equip   ESC Cancel',
                          'ja': '↑↓ 選択   Enter 装備   ESC キャンセル',
                          'zh': '↑↓ 选择   Enter 装备   ESC 取消',
                          'ru': '↑↓ Выбор   Enter Надеть   ESC Отмена'},
    'sb_basic':          {'ko': '[ 기본 스킬 ]', 'en': '[ Basic Skills ]', 'ja': '[ 基本スキル ]', 'zh': '[ 基础技能 ]', 'ru': '[ Базовые навыки ]'},
    'sb_combo':          {'ko': '[ 조합 스킬 ]', 'en': '[ Combo Skills ]', 'ja': '[ コンボスキル ]', 'zh': '[ 组合技能 ]', 'ru': '[ Комбо-навыки ]'},
    'sb_ultimate':       {'ko': '[ 궁극기 ]', 'en': '[ Ultimate ]', 'ja': '[ 必殺技 ]', 'zh': '[ 终极技 ]', 'ru': '[ Ультимейт ]'},
    'sb_locked':         {'ko': '잠금 (Lv.{} 필요)', 'en': 'Locked (Lv.{} req)',
                          'ja': 'ロック (Lv.{}必要)', 'zh': '锁定 (需Lv.{})', 'ru': 'Закрыто (нужен ур.{})'},
    'sb_locked_key':     {'ko': '[{}] 잠금 (Lv.{} 필요)', 'en': '[{}] Locked (Lv.{})',
                          'ja': '[{}] ロック (Lv.{})', 'zh': '[{}] 锁定 (Lv.{})', 'ru': '[{}] Закрыто (ур.{})'},
    'sb_available':      {'ko': '사용 가능', 'en': 'Available', 'ja': '使用可能', 'zh': '可使用', 'ru': 'Доступно'},
    'sb_max':            {'ko': 'MAX', 'en': 'MAX', 'ja': 'MAX', 'zh': 'MAX', 'ru': 'MAX'},
    'sb_max_done':       {'ko': '★ 최대 레벨 달성!', 'en': '★ Max Level!', 'ja': '★ 最大レベル達成!', 'zh': '★ 已达满级!', 'ru': '★ Макс. уровень!'},
    'sb_lv_header':      {'ko': 'Lv', 'en': 'Lv', 'ja': 'Lv', 'zh': 'Lv', 'ru': 'Ур'},
    'sb_eff_header':     {'ko': '효과', 'en': 'Effect', 'ja': '効果', 'zh': '效果', 'ru': 'Эффект'},
    'sb_cd_header':      {'ko': '쿨다운', 'en': 'CD', 'ja': 'CD', 'zh': '冷却', 'ru': 'КД'},
    'sb_upgrade_line':   {'ko': 'Lv{} → Lv{} 업그레이드: {} SP', 'en': 'Lv{} → Lv{} Upgrade: {} SP',
                          'ja': 'Lv{} → Lv{} 強化: {} SP', 'zh': 'Lv{} → Lv{} 升级: {} SP',
                          'ru': 'Ур{} → Ур{} Прокачка: {} SP'},
    'sb_upgrade_btn':    {'ko': '[ Enter ] 업그레이드', 'en': '[ Enter ] Upgrade',
                          'ja': '[ Enter ] 強化', 'zh': '[ Enter ] 升级', 'ru': '[ Enter ] Прокачать'},
    'sb_no_book':        {'ko': '스킬북 미보유', 'en': 'No Skill Book', 'ja': 'スキルブック未所持', 'zh': '未持有技能书', 'ru': 'Нет книги навыка'},
    'sb_req_player_lv':  {'ko': '플레이어 Lv.{} 필요', 'en': 'Player Lv.{} req',
                          'ja': 'プレイヤーLv.{}必要', 'zh': '需玩家Lv.{}', 'ru': 'Нужен ур. игрока {}'},
    'sb_req_player_cur': {'ko': '플레이어 Lv.{} 필요 (현재 Lv.{})', 'en': 'Player Lv.{} req (cur {})',
                          'ja': 'プレイヤーLv.{}必要 (現在Lv.{})', 'zh': '需玩家Lv.{} (当前Lv.{})',
                          'ru': 'Нужен ур.{} (сейчас {})'},
    'sb_req_skill_cur':  {'ko': '{} Lv{} 필요 (현재 Lv{})', 'en': '{} Lv{} req (cur {})',
                          'ja': '{} Lv{}必要 (現在Lv{})', 'zh': '需{} Lv{} (当前Lv{})',
                          'ru': '{} ур.{} (сейчас {})'},
    'sb_req_skills':     {'ko': '{}·{} 각각 스킬 Lv{}, 플레이어 Lv.{} 필요',
                          'en': '{}·{} Skill Lv{} each, Player Lv.{} req',
                          'ja': '{}·{} 各スキルLv{}、プレイヤーLv.{}必要',
                          'zh': '{}·{} 各需技能Lv{}, 玩家Lv.{}',
                          'ru': '{}·{} — навыки ур.{}, игрок ур.{}'},
    'sb_key_label':      {'ko': '[{}키]', 'en': '[{}]', 'ja': '[{}キー]', 'zh': '[{}键]', 'ru': '[{}]'},

    # ── 아이템 사용 메시지 ─────────────────────────────────────────────────
    'item_heal':    {'ko': '{} 사용! HP +{}', 'en': '{} used! HP +{}',
                     'ja': '{}を使用! HP +{}', 'zh': '使用{}! HP +{}', 'ru': '{} — HP +{}'},
    'item_atk':     {'ko': '{} 장착! ATK +{}', 'en': '{} equipped! ATK +{}',
                     'ja': '{}を装備! ATK +{}', 'zh': '装备{}! ATK +{}', 'ru': '{} надето! АТК +{}'},
    'item_def':     {'ko': '{} 장착! DEF +{}', 'en': '{} equipped! DEF +{}',
                     'ja': '{}を装備! DEF +{}', 'zh': '装备{}! DEF +{}', 'ru': '{} надето! ЗАЩ +{}'},
    'item_all':     {'ko': '{} 착용! ATK+{} DEF+{}', 'en': '{} worn! ATK+{} DEF+{}',
                     'ja': '{}を装着! ATK+{} DEF+{}', 'zh': '穿戴{}! ATK+{} DEF+{}',
                     'ru': '{} надето! АТК+{} ЗАЩ+{}'},
    'item_use':     {'ko': '{} 사용', 'en': '{} used', 'ja': '{}を使用', 'zh': '使用{}', 'ru': '{} использовано'},

    # ── 테마 / 999층 ──────────────────────────────────────────────────
    'new_theme':    {'ko': '◆ 새로운 구역: {}', 'en': '◆ New Zone: {}',
                     'ja': '◆ 新しいエリア: {}', 'zh': '◆ 新区域: {}', 'ru': '◆ Новая зона: {}'},
    'victory':      {'ko': '★★★ 축하합니다! 999층 클리어! ★★★', 'en': '★★★ Congratulations! Floor 999 cleared! ★★★',
                     'ja': '★★★ おめでとう! 999階クリア! ★★★', 'zh': '★★★ 恭喜! 通关999层! ★★★',
                     'ru': '★★★ Поздравляем! Этаж 999 пройден! ★★★'},

    # ── 스탯 레이블 (HUD 사이드 패널) ──────────────────────────────────
    'stat_atk':     {'ko': '공격력', 'en': 'ATK', 'ja': '攻撃力', 'zh': '攻击', 'ru': 'АТК'},
    'stat_def':     {'ko': '방어력', 'en': 'DEF', 'ja': '防御力', 'zh': '防御', 'ru': 'ЗАЩ'},
    'stat_aspd':    {'ko': '공격속도', 'en': 'ATK Spd', 'ja': '攻撃速度', 'zh': '攻速', 'ru': 'Скор. атаки'},
    'stat_eva':     {'ko': '회피율', 'en': 'Evasion', 'ja': '回避率', 'zh': '闪避', 'ru': 'Уклонение'},
    'stat_mspd':    {'ko': '이동속도', 'en': 'MOV Spd', 'ja': '移動速度', 'zh': '移速', 'ru': 'Скор. ходьбы'},
    'stat_spred':   {'ko': 'SP 경감', 'en': 'SP Cost', 'ja': 'SP軽減', 'zh': 'SP减耗', 'ru': 'Эконом. SP'},

    # ── 장비 슬롯 짧은 이름 ────────────────────────────────────────────
    'slot_head_s':  {'ko': '투구', 'en': 'Head', 'ja': '兜', 'zh': '头盔', 'ru': 'Шлем'},
    'slot_body_s':  {'ko': '갑옷', 'en': 'Armor', 'ja': '鎧', 'zh': '护甲', 'ru': 'Броня'},
    'slot_wpn_s':   {'ko': '무기', 'en': 'Wpn', 'ja': '武器', 'zh': '武器', 'ru': 'Оруж.'},
    'slot_off_s':   {'ko': '보조무기', 'en': 'Off-Hand', 'ja': '盾・補助', 'zh': '副手', 'ru': 'Второе'},
    'slot_off_hud': {'ko': '보조', 'en': 'Off', 'ja': '補助', 'zh': '副手', 'ru': 'Втор.'},
    'slot_acc_s':   {'ko': '장신구', 'en': 'Acc', 'ja': '装飾', 'zh': '饰品', 'ru': 'Аксесс.'},
    'slot_feet_s':  {'ko': '신발', 'en': 'Boots', 'ja': '靴', 'zh': '鞋子', 'ru': 'Обувь'},

    # ── 아이템 장착 / 해제 메시지 ─────────────────────────────────────
    'item_discard':      {'ko': '[{}] 버림', 'en': '[{}] discarded',
                          'ja': '[{}]を捨てた', 'zh': '丢弃[{}]', 'ru': '[{}] выброшено'},
    'item_unequip':      {'ko': '{} {} 해제', 'en': '{} {} unequipped',
                          'ja': '{} {}を解除', 'zh': '卸下{} {}', 'ru': '{} {} снято'},
    'item_equip_msg':    {'ko': '{}{} {} 장착! (+{})', 'en': '{}{} {} equipped! (+{})',
                          'ja': '{}{} {}を装備! (+{})', 'zh': '装备{}{} {}! (+{})',
                          'ru': '{}{} {} надето! (+{})'},
    'item_unequip_inv':  {'ko': '{} 해제 → 인벤토리', 'en': '{} unequipped → inventory',
                          'ja': '{}を解除 → インベントリ', 'zh': '卸下{} → 物品栏',
                          'ru': '{} снято → инвентарь'},
    'item_unequip_full': {'ko': '{} 해제 (인벤토리 가득 참)', 'en': '{} unequipped (inv full)',
                          'ja': '{}を解除 (インベントリ満杯)', 'zh': '卸下{} (物品栏已满)',
                          'ru': '{} снято (инвентарь полон)'},

    # ── 장비 강화 패널 ─────────────────────────────────────────────────
    'enh_title':     {'ko': '장비 강화', 'en': 'Enhancement', 'ja': '装備強化', 'zh': '装备强化', 'ru': 'Усиление'},
    'enh_stones':    {'ko': '강화석: {}개', 'en': 'Stones: {}', 'ja': '強化石: {}個', 'zh': '强化石: {}', 'ru': 'Камни: {}'},
    'enh_rate':      {'ko': '성공률 {}%', 'en': '{}% chance', 'ja': '成功率 {}%', 'zh': '成功率 {}%', 'ru': 'Шанс {}%'},
    'enh_cost':      {'ko': '강화석 1개', 'en': '1 Stone', 'ja': '強化石 1個', 'zh': '强化石 x1', 'ru': '1 камень'},
    'enh_empty':     {'ko': '--- 비어있음 ---', 'en': '--- Empty ---', 'ja': '--- 空き ---', 'zh': '--- 空 ---', 'ru': '--- Пусто ---'},
    'enh_hint':      {'ko': '↑↓ 선택   Enter 강화   P/ESC 닫기',
                      'en': '↑↓ Select   Enter Enhance   P/ESC Close',
                      'ja': '↑↓ 選択   Enter 強化   P/ESC 閉じる',
                      'zh': '↑↓ 选择   Enter 强化   P/ESC 关闭',
                      'ru': '↑↓ Выбор   Enter Усилить   P/ESC Закрыть'},
    'enh_stat_head': {'ko': '회피율 +1%', 'en': 'Evasion +1%', 'ja': '回避率 +1%', 'zh': '闪避 +1%', 'ru': 'Уклонение +1%'},
    'enh_stat_body': {'ko': '방어력 +1', 'en': 'DEF +1', 'ja': '防御力 +1', 'zh': '防御 +1', 'ru': 'ЗАЩ +1'},
    'enh_stat_wpn':  {'ko': '공격력 +1', 'en': 'ATK +1', 'ja': '攻撃力 +1', 'zh': '攻击 +1', 'ru': 'АТК +1'},
    'enh_stat_off':  {'ko': '방어력 +1', 'en': 'DEF +1', 'ja': '防御力 +1', 'zh': '防御 +1', 'ru': 'ЗАЩ +1'},
    'enh_stat_acc':  {'ko': '스킬 데미지 +5%', 'en': 'Skill DMG +5%', 'ja': 'スキルダメージ +5%', 'zh': '技能伤害 +5%', 'ru': 'Урон навыков +5%'},
    'enh_stat_feet': {'ko': '이동속도 +0.05', 'en': 'MOV Spd +0.05', 'ja': '移動速度 +0.05', 'zh': '移速 +0.05', 'ru': 'Скор. +0.05'},

    # ── 스킬 도감 UI ──────────────────────────────────────────────────
    'sb_slot_section':    {'ko': '장착 슬롯', 'en': 'Equipped', 'ja': '装備スロット', 'zh': '装备槽', 'ru': 'Слоты'},
    'sb_avail_section':   {'ko': '보유 스킬', 'en': 'Available', 'ja': '所持スキル', 'zh': '持有技能', 'ru': 'Доступные'},
    'sb_pick_slot_banner':{'ko': '[{}] → 어느 슬롯에 장착?', 'en': '[{}] → Which slot?',
                           'ja': '[{}] → どのスロットに?', 'zh': '[{}] → 装到哪个槽?', 'ru': '[{}] → В какой слот?'},
    'sb_pick_skill_banner':{'ko': '→ {} 슬롯에 장착할 스킬 선택', 'en': '→ Pick skill for {} slot',
                            'ja': '→ {}スロットのスキルを選択', 'zh': '→ 选择{}槽的技能',
                            'ru': '→ Выберите навык для слота {}'},
    'sb_slot_here':       {'ko': '← 여기에', 'en': '← Here', 'ja': '← ここに', 'zh': '← 这里', 'ru': '← Сюда'},
    'sb_slot_change':     {'ko': '[변경]', 'en': '[Change]', 'ja': '[変更]', 'zh': '[更换]', 'ru': '[Сменить]'},
    'enc_header':         {'ko': '인챈트  (1위력  2신속  3절약  4오의)',
                           'en': 'Enchant  (1Pwr  2Haste  3Eff  4Arc)',
                           'ja': 'エンチャント (1威力 2神速 3節約 4奥義)',
                           'zh': '附魔  (1威力 2迅捷 3节约 4奥义)',
                           'ru': 'Чары  (1Мощь 2Быстр 3Экон 4Тайна)'},

    # ── 전투 / 스킬 메시지 ────────────────────────────────────────────
    'fear_miss':        {'ko': '두려움에 공격이 빗나갔습니다!', 'en': 'Fear! Attack missed!',
                         'ja': '恐怖で攻撃が外れた!', 'zh': '因恐惧攻击落空!', 'ru': 'Страх! Атака мимо!'},
    'sp_gained':        {'ko': '스킬 포인트 +3 (보유: {})', 'en': 'Skill Points +3 (have: {})',
                         'ja': 'スキルポイント+3 (所持: {})', 'zh': '技能点+3 (持有: {})',
                         'ru': 'Очки навыков +3 (всего: {})'},
    'monster_appear':   {'ko': '몬스터가 나타났다!', 'en': 'A monster appeared!',
                         'ja': 'モンスターが現れた!', 'zh': '怪物出现了!', 'ru': 'Появился монстр!'},
    'skill_regen_def':  {'ko': '방어력 +{} ({}초)', 'en': 'DEF +{} ({}s)',
                         'ja': '防御力+{} ({}秒)', 'zh': '防御+{} ({}秒)', 'ru': 'ЗАЩ +{} ({}с)'},
    'skill_shadow_step':{'ko': '그림자 속으로 사라졌다!', 'en': 'Vanished into the shadows!',
                         'ja': '影の中へ消えた!', 'zh': '消失在暗影中!', 'ru': 'Растворился в тенях!'},
    'skill_iron_shell': {'ko': '철갑 방벽! 피해 {}% 감소 ({}초)', 'en': 'Iron Shell! DMG -{}% ({}s)',
                         'ja': '鉄甲障壁! 被ダメージ-{}% ({}秒)', 'zh': '铁甲壁垒! 伤害-{}% ({}秒)',
                         'ru': 'Панцирь! Урон -{}% ({}с)'},
    'skill_flame_hit':  {'ko': '화염 강타! {}명 적중', 'en': 'Flame Strike! Hit {}',
                         'ja': '火炎強打! {}体に命中', 'zh': '烈焰重击! 命中{}个', 'ru': 'Огненный удар! Задето: {}'},
    'skill_flame_miss': {'ko': '화염이 허공을 갈랐다!', 'en': 'Flame cut the air!',
                         'ja': '炎が空を切った!', 'zh': '火焰划过虚空!', 'ru': 'Пламя рассекло воздух!'},
    'skill_life_hit':   {'ko': '생명 흡수! {} HP 회복', 'en': 'Life Steal! +{} HP',
                         'ja': '生命吸収! HP+{}回復', 'zh': '生命汲取! 恢复{}HP', 'ru': 'Похищение жизни! +{} HP'},
    'skill_life_miss':  {'ko': '생명 흡수 (미적중)', 'en': 'Life Steal (miss)',
                         'ja': '生命吸収 (空振り)', 'zh': '生命汲取 (未命中)', 'ru': 'Похищение жизни (мимо)'},
    'skill_war_cry':    {'ko': '전투 함성! 공격력 +{}% ({}초)', 'en': 'War Cry! ATK +{}% ({}s)',
                         'ja': '雄叫び! 攻撃力+{}% ({}秒)', 'zh': '战吼! 攻击+{}% ({}秒)',
                         'ru': 'Боевой клич! АТК +{}% ({}с)'},
    'skill_dark_hit':   {'ko': '암흑 파동! {}명 적중', 'en': 'Dark Pulse! Hit {}',
                         'ja': '暗黒波動! {}体に命中', 'zh': '黑暗波动! 命中{}个', 'ru': 'Тёмная волна! Задето: {}'},
    'skill_dark_miss':  {'ko': '파동이 허공에 사라졌다!', 'en': 'Dark Pulse faded!',
                         'ja': '波動が虚空に消えた!', 'zh': '波动消散于虚空!', 'ru': 'Волна растаяла!'},

    # ── 인챈트 타입 이름 ──────────────────────────────────────────────
    'enc_type_power':      {'ko': '위력', 'en': 'Power', 'ja': '威力', 'zh': '威力', 'ru': 'Мощь'},
    'enc_type_haste':      {'ko': '신속', 'en': 'Haste', 'ja': '神速', 'zh': '迅捷', 'ru': 'Быстрота'},
    'enc_type_efficiency': {'ko': '절약', 'en': 'Efficiency', 'ja': '節約', 'zh': '节约', 'ru': 'Экономия'},
    'enc_type_arcane':     {'ko': '오의', 'en': 'Arcane', 'ja': '奥義', 'zh': '奥义', 'ru': 'Тайна'},

    # ── 스킬 강화 / 인챈트 메시지 ─────────────────────────────────────
    'skill_upg_maxed':  {'ko': '{} 스킬이 이미 최대 레벨입니다.', 'en': '{} is already max level.',
                         'ja': '{}は既に最大レベルだ。', 'zh': '{}已达最大等级。', 'ru': '{} уже на макс. уровне.'},
    'skill_upg_nosp':   {'ko': 'SP가 부족합니다. (필요: {}, 보유: {})', 'en': 'Not enough SP. (need: {}, have: {})',
                         'ja': 'SPが足りない。(必要: {}, 所持: {})', 'zh': 'SP不足。(需要: {}, 持有: {})',
                         'ru': 'Не хватает SP. (нужно: {}, есть: {})'},
    'enc_max':          {'ko': '이미 최대 레벨입니다.', 'en': 'Already at max level.',
                         'ja': '既に最大レベルだ。', 'zh': '已达最大等级。', 'ru': 'Уже макс. уровень.'},
    'enc_no_sp':        {'ko': 'SP 부족 (필요: {}, 보유: {})', 'en': 'Not enough SP (need: {}, have: {})',
                         'ja': 'SP不足 (必要: {}, 所持: {})', 'zh': 'SP不足 (需要: {}, 持有: {})',
                         'ru': 'Мало SP (нужно: {}, есть: {})'},
    'enc_done':         {'ko': '[{}] {} Lv.{}!', 'en': '[{}] {} Lv.{}!',
                         'ja': '[{}] {} Lv.{}!', 'zh': '[{}] {} Lv.{}!', 'ru': '[{}] {} Ур.{}!'},
    'arcane_no_skill':  {'ko': '오의: 먼저 오의 스킬을 사용하세요.', 'en': 'Arcane: Use an arcane skill first.',
                         'ja': '奥義: 先に奥義スキルを使え。', 'zh': '奥义: 请先使用奥义技能。',
                         'ru': 'Тайна: сначала используйте навык с чарами.'},
    'arcane_no_enc':    {'ko': '오의: 오의 인챈트가 해금되지 않았습니다.', 'en': 'Arcane: enchant not unlocked.',
                         'ja': '奥義: エンチャント未解放。', 'zh': '奥义: 附魔未解锁。',
                         'ru': 'Тайна: чары не открыты.'},
    'arcane_no_sp':     {'ko': '오의: SP 부족 ({}/{})', 'en': 'Arcane: Low SP ({}/{})',
                         'ja': '奥義: SP不足 ({}/{})', 'zh': '奥义: SP不足 ({}/{})', 'ru': 'Тайна: мало SP ({}/{})'},
    'arcane_trigger':   {'ko': '★ 오의 발동!', 'en': '★ Arcane Art!', 'ja': '★ 奥義発動!', 'zh': '★ 奥义发动!', 'ru': '★ Тайное искусство!'},
    'skill_equip_slot': {'ko': '[{}] 슬롯에 [{}] 장착!', 'en': '[{}] equipped with [{}]!',
                         'ja': '[{}]スロットに[{}]を装備!', 'zh': '[{}]槽装备[{}]!',
                         'ru': 'В слот [{}] — [{}]!'},

    # ── 궁극기 메시지 ──────────────────────────────────────────────────
    'ult_no_level':     {'ko': '{}: Lv.{} 필요 (현재 Lv.{})', 'en': '{}: Requires Lv.{} (cur Lv.{})',
                         'ja': '{}: Lv.{}が必要 (現在Lv.{})', 'zh': '{}: 需要Lv.{} (当前Lv.{})',
                         'ru': '{}: нужен ур.{} (сейчас {})'},
    'ult_breaker_hit':  {'ko': '⚔ 던전 브레이커! {}마리 초토화!', 'en': '⚔ Dungeon Breaker! {} obliterated!',
                         'ja': '⚔ ダンジョンブレイカー! {}体を殲滅!', 'zh': '⚔ 地城破坏者! 歼灭{}个!',
                         'ru': '⚔ Разрушитель! Уничтожено: {}!'},
    'ult_breaker_miss': {'ko': '⚔ 던전 브레이커! 적 없음', 'en': '⚔ Dungeon Breaker! No enemies',
                         'ja': '⚔ ダンジョンブレイカー! 敵なし', 'zh': '⚔ 地城破坏者! 无敌人',
                         'ru': '⚔ Разрушитель! Врагов нет'},
    'ult_slash_hit':    {'ko': '真 일도양단! 무적 2초 + {}마리 섬멸!',
                         'en': '真 True Cut! 2s invincible + {} defeated!',
                         'ja': '真・一刀両断! 無敵2秒 + {}体を殲滅!',
                         'zh': '真·一刀两断! 无敌2秒 + 歼灭{}个!',
                         'ru': '真 Истинный разруб! 2с неуязвимости + {} врагов!'},
    'ult_slash_miss':   {'ko': '真 일도양단! (적 없음)', 'en': '真 True Cut! (No enemies)',
                         'ja': '真・一刀両断! (敵なし)', 'zh': '真·一刀两断! (无敌人)',
                         'ru': '真 Истинный разруб! (врагов нет)'},

    # ── 적 전투 메시지 ────────────────────────────────────────────────
    'enemy_atk':       {'ko': '{}이(가) {} 피해를 입혔습니다!', 'en': '{} dealt {} damage!',
                        'ja': '{}から{}ダメージを受けた!', 'zh': '{}造成{}伤害!', 'ru': '{} наносит {} урона!'},
    'enemy_evade':     {'ko': '{}의 공격을 회피했습니다!', 'en': 'Dodged {}\'s attack!',
                        'ja': '{}の攻撃を回避した!', 'zh': '闪避了{}的攻击!', 'ru': 'Уклонение от атаки {}!'},
    'enemy_whiff':     {'ko': '{}의 공격이 빗나갔습니다!', 'en': '{}\'s attack missed!',
                        'ja': '{}の攻撃が外れた!', 'zh': '{}的攻击落空了!', 'ru': '{} промахнулся!'},
    'boss_charge_hit': {'ko': '{}이(가) 돌진 강타! {} 피해!', 'en': '{} charge strike! {} damage!',
                        'ja': '{}の突進強打! {}ダメージ!', 'zh': '{}冲锋重击! {}伤害!',
                        'ru': '{} — таранный удар! {} урона!'},
    'boss_charge_use': {'ko': '{}이(가) 돌진합니다!', 'en': '{} is charging!',
                        'ja': '{}が突進してくる!', 'zh': '{}发起冲锋!', 'ru': '{} несётся в атаку!'},
    'boss_charge_ev':  {'ko': '{}의 돌진을 회피했습니다!', 'en': 'Dodged {}\'s charge!',
                        'ja': '{}の突進を回避した!', 'zh': '闪避了{}的冲锋!', 'ru': 'Уклонение от рывка {}!'},
    'boss_whirl_hit':  {'ko': '{}이(가) 회전베기! {} 피해!', 'en': '{} whirlwind! {} damage!',
                        'ja': '{}の回転斬り! {}ダメージ!', 'zh': '{}旋风斩! {}伤害!',
                        'ru': '{} — вихревой удар! {} урона!'},
    'boss_whirl_use':  {'ko': '{}이(가) 회전베기를 사용했습니다!', 'en': '{} used whirlwind!',
                        'ja': '{}が回転斬りを放った!', 'zh': '{}使用了旋风斩!', 'ru': '{} закружился в вихре!'},
    'boss_whirl_ev':   {'ko': '{}의 회전베기를 회피했습니다!', 'en': 'Dodged {}\'s whirlwind!',
                        'ja': '{}の回転斬りを回避した!', 'zh': '闪避了{}的旋风斩!',
                        'ru': 'Уклонение от вихря {}!'},
    'boss_nova_hit':   {'ko': '{}이(가) 죽음의 파동! {} 피해!', 'en': '{} death nova! {} damage!',
                        'ja': '{}の死の波動! {}ダメージ!', 'zh': '{}死亡新星! {}伤害!',
                        'ru': '{} — волна смерти! {} урона!'},
    'boss_nova_use':   {'ko': '{}이(가) 죽음의 파동을 시전했습니다!', 'en': '{} cast death nova!',
                        'ja': '{}が死の波動を放った!', 'zh': '{}释放了死亡新星!', 'ru': '{} испускает волну смерти!'},
    'boss_nova_ev':    {'ko': '{}의 죽음의 파동을 회피했습니다!', 'en': 'Dodged {}\'s death nova!',
                        'ja': '{}の死の波動を回避した!', 'zh': '闪避了{}的死亡新星!',
                        'ru': 'Уклонение от волны {}!'},
    'boss_summon':     {'ko': '{}이(가) 언데드를 소환했습니다!', 'en': '{} summoned undead!',
                        'ja': '{}がアンデッドを召喚した!', 'zh': '{}召唤了亡灵!', 'ru': '{} призывает нежить!'},
    'boss_prep_charge':     {'ko': '⚠ {}이(가) 돌진을 준비합니다!', 'en': '⚠ {} is preparing to charge!',
                             'ja': '⚠ {}が突進の構え!', 'zh': '⚠ {}准备冲锋!', 'ru': '⚠ {} готовит рывок!'},
    'boss_prep_whirlwind':  {'ko': '⚠ {}이(가) 회전베기를 준비합니다!', 'en': '⚠ {} winds up a whirlwind!',
                             'ja': '⚠ {}が回転斬りの構え!', 'zh': '⚠ {}蓄力旋风斩!', 'ru': '⚠ {} готовит вихрь!'},
    'boss_prep_death_nova': {'ko': '⚠ {}이(가) 죽음의 파동을 모읍니다!', 'en': '⚠ {} is gathering a death nova!',
                             'ja': '⚠ {}が死の波動を溜めている!', 'zh': '⚠ {}正在凝聚死亡新星!',
                             'ru': '⚠ {} копит волну смерти!'},
    'boss_curse':      {'ko': '{}이(가) 저주를 걸었습니다! 받는 피해 50% 증가', 'en': '{} cursed you! DMG taken +50%',
                        'ja': '{}に呪われた! 被ダメージ+50%', 'zh': '被{}诅咒! 受到伤害+50%',
                        'ru': '{} проклял вас! Получаемый урон +50%'},
    'boss_slow':       {'ko': '{}이(가) 슬로우를 걸었습니다! 이동속도 감소', 'en': '{} slowed you! Move speed down',
                        'ja': '{}にスロウをかけられた! 移動速度低下', 'zh': '被{}减速! 移速下降',
                        'ru': '{} замедлил вас! Скорость снижена'},
    'boss_fear':       {'ko': '{}이(가) 두려움을 심었습니다! 명중률 40%로 저하', 'en': '{} instilled fear! Hit rate 40%',
                        'ja': '{}に恐怖を植え付けられた! 命中率40%に低下', 'zh': '被{}恐惧! 命中率降至40%',
                        'ru': '{} вселил страх! Точность 40%'},

    # ── 엘리트 변종 ───────────────────────────────────────────────────
    'elite_swift':    {'ko': '신속한 {}', 'en': 'Swift {}', 'ja': '神速の{}', 'zh': '迅捷的{}', 'ru': 'Быстрый {}'},
    'elite_ironhide': {'ko': '강철의 {}', 'en': 'Ironhide {}', 'ja': '鋼鉄の{}', 'zh': '铁甲的{}', 'ru': 'Бронированный {}'},
    'elite_berserk':  {'ko': '광폭한 {}', 'en': 'Berserk {}', 'ja': '狂暴な{}', 'zh': '狂暴的{}', 'ru': 'Бешеный {}'},
    'elite_vampiric': {'ko': '흡혈의 {}', 'en': 'Vampiric {}', 'ja': '吸血の{}', 'zh': '吸血的{}', 'ru': 'Вампирический {}'},
    'elite_volatile': {'ko': '폭발하는 {}', 'en': 'Volatile {}', 'ja': '爆発する{}', 'zh': '爆炸的{}', 'ru': 'Взрывной {}'},
    'elite_appear':   {'ko': '⚡ 엘리트 출현! [{}]', 'en': '⚡ Elite appeared! [{}]',
                       'ja': '⚡ エリート出現! [{}]', 'zh': '⚡ 精英出现! [{}]', 'ru': '⚡ Элитный враг! [{}]'},
    'volatile_boom':      {'ko': '💥 {}이(가) 폭발했다! {} 피해!', 'en': '💥 {} exploded! {} damage!',
                           'ja': '💥 {}が爆発した! {}ダメージ!', 'zh': '💥 {}爆炸了! {}伤害!',
                           'ru': '💥 {} взорвался! {} урона!'},
    'volatile_boom_safe': {'ko': '💥 {}이(가) 폭발했다!', 'en': '💥 {} exploded!',
                           'ja': '💥 {}が爆発した!', 'zh': '💥 {}爆炸了!', 'ru': '💥 {} взорвался!'},

    # ── 프롭 / 보물 고블린 ────────────────────────────────────────────
    'prop_break':      {'ko': '💥 {} 파괴!', 'en': '💥 {} smashed!',
                        'ja': '💥 {}を破壊!', 'zh': '💥 打碎了{}!', 'ru': '💥 {} разбит!'},
    'prop_break_gold': {'ko': '💥 {} 파괴! +{} G', 'en': '💥 {} smashed! +{} G',
                        'ja': '💥 {}を破壊! +{} G', 'zh': '💥 打碎了{}! +{} G',
                        'ru': '💥 {} разбит! +{} G'},
    'goblin_spawn':    {'ko': '💰 보물 고블린이 나타났다! 도망치기 전에 잡아라!',
                        'en': '💰 A Treasure Goblin appeared! Catch it before it escapes!',
                        'ja': '💰 宝物ゴブリンが現れた! 逃げる前に仕留めろ!',
                        'zh': '💰 宝藏哥布林出现了! 在它逃跑前抓住它!',
                        'ru': '💰 Появился гоблин-сокровищник! Поймай его, пока не сбежал!'},
    'goblin_escape':   {'ko': '💨 보물 고블린이 도망쳤다...', 'en': '💨 The Treasure Goblin escaped...',
                        'ja': '💨 宝物ゴブリンに逃げられた...', 'zh': '💨 宝藏哥布林逃走了...',
                        'ru': '💨 Гоблин-сокровищник сбежал...'},

    # ── 마을 시스템 ───────────────────────────────────────────────────
    'npc_storage':    {'ko': '주막 주모', 'en': 'Innkeeper', 'ja': '宿屋の女将', 'zh': '酒馆老板娘', 'ru': 'Трактирщица'},
    'npc_smith':      {'ko': '대장장이', 'en': 'Blacksmith', 'ja': '鍛冶屋', 'zh': '铁匠', 'ru': 'Кузнец'},
    'town_portal_label': {'ko': '던전 포탈', 'en': 'Dungeon Portal', 'ja': 'ダンジョンポータル', 'zh': '地城传送门', 'ru': 'Портал в подземелье'},
    'interact_hint':  {'ko': '[E]', 'en': '[E]', 'ja': '[E]', 'zh': '[E]', 'ru': '[E]'},
    'portal_open':    {'ko': '✦ 마을 귀환 포탈이 열렸다! 밟으면 이동',
                       'en': '✦ A town portal opened! Step in to travel',
                       'ja': '✦ 村への帰還ポータルが開いた! 乗れば移動',
                       'zh': '✦ 回城传送门打开了! 踏入即可传送',
                       'ru': '✦ Портал в деревню открыт! Шагни внутрь'},
    'town_enter':     {'ko': '🏘 마을에 도착했다. 편히 정비하자.',
                       'en': '🏘 Arrived in town. Rest and resupply.',
                       'ja': '🏘 村に到着した。ゆっくり整えよう。',
                       'zh': '🏘 抵达村庄。好好整备吧。',
                       'ru': '🏘 Вы в деревне. Отдохните и соберитесь.'},
    'town_deposit':   {'ko': '소지품 {}개를 창고에 안전하게 보관했다.',
                       'en': 'Safely stored {} items in the stash.',
                       'ja': '持ち物{}個を倉庫に安全に保管した。',
                       'zh': '已将{}件物品安全存入仓库。',
                       'ru': 'Вещи ({}) надёжно убраны на склад.'},
    'town_return':    {'ko': '⚔ Floor {} — 사냥하던 자리로 복귀!',
                       'en': '⚔ Floor {} — back where you left off!',
                       'ja': '⚔ Floor {} — 狩り場に復帰!',
                       'zh': '⚔ 第{}层 — 回到刚才的位置!',
                       'ru': '⚔ Этаж {} — назад в бой!'},
    'storage_title':  {'ko': '창  고  (주모)', 'en': 'Stash (Innkeeper)', 'ja': '倉庫 (女将)', 'zh': '仓库 (老板娘)', 'ru': 'Склад (трактирщица)'},
    'storage_carried':{'ko': '소지품  {}/{}', 'en': 'Carried  {}/{}', 'ja': '持ち物  {}/{}', 'zh': '携带  {}/{}', 'ru': 'С собой  {}/{}'},
    'storage_stored': {'ko': '창고  {}개 (영구 보관)', 'en': 'Stash  {} (permanent)', 'ja': '倉庫  {}個 (永久保管)', 'zh': '仓库  {} (永久保存)', 'ru': 'Склад  {} (навсегда)'},
    'storage_hint':   {'ko': '←→ 패널 전환   ↑↓ 선택   Enter 옮기기   ESC 닫기',
                       'en': '←→ Switch pane   ↑↓ Select   Enter Move   ESC Close',
                       'ja': '←→ パネル切替   ↑↓ 選択   Enter 移動   ESC 閉じる',
                       'zh': '←→ 切换面板   ↑↓ 选择   Enter 转移   ESC 关闭',
                       'ru': '←→ Панель   ↑↓ Выбор   Enter Переложить   ESC Закрыть'},
    'smith_title':    {'ko': '대장간  (골드 강화)', 'en': 'Smithy (Gold Enhance)', 'ja': '鍛冶場 (ゴールド強化)', 'zh': '铁匠铺 (金币强化)', 'ru': 'Кузница (за золото)'},
    'smith_cost':     {'ko': '강화 비용 {} G', 'en': 'Cost {} G', 'ja': '強化費用 {} G', 'zh': '强化费用 {} G', 'ru': 'Цена {} G'},

    # ── 처치 연쇄 ─────────────────────────────────────────────────────
    'combo_kill': {'ko': '⚡ 처치 연쇄 x{}!  (+{} SP)', 'en': '⚡ Kill combo x{}!  (+{} SP)',
                   'ja': '⚡ 連続撃破 x{}!  (+{} SP)', 'zh': '⚡ 连杀 x{}!  (+{} SP)',
                   'ru': '⚡ Серия убийств x{}!  (+{} SP)'},

    # ── 도전과제 ──────────────────────────────────────────────────────
    'ach_unlock': {'ko': '🏆 도전과제 달성: {}', 'en': '🏆 Achievement unlocked: {}',
                   'ja': '🏆 実績解除: {}', 'zh': '🏆 成就达成: {}', 'ru': '🏆 Достижение: {}'},
    'ach_ACH_FIRST_BLOOD': {'ko': '첫 사냥감', 'en': 'First Blood', 'ja': '最初の獲物', 'zh': '第一滴血', 'ru': 'Первая кровь'},
    'ach_ACH_KILLS_500':   {'ko': '학살자', 'en': 'Slaughterer', 'ja': '殺戮者', 'zh': '屠杀者', 'ru': 'Истребитель'},
    'ach_ACH_ELITE_25':    {'ko': '변종 사냥꾼', 'en': 'Variant Hunter', 'ja': '変種ハンター', 'zh': '精英猎人', 'ru': 'Охотник на элиту'},
    'ach_ACH_BOSS_10':     {'ko': '보스의 악몽', 'en': 'Nightmare of Bosses', 'ja': 'ボスの悪夢', 'zh': '首领的噩梦', 'ru': 'Кошмар боссов'},
    'ach_ACH_FLOOR_5':     {'ko': '첫 관문', 'en': 'First Gate', 'ja': '最初の関門', 'zh': '第一道门', 'ru': 'Первые врата'},
    'ach_ACH_FLOOR_10':    {'ko': '지하 10층', 'en': 'Depth 10', 'ja': '地下10階', 'zh': '地下10层', 'ru': 'Глубина 10'},
    'ach_ACH_FLOOR_25':    {'ko': '심연을 향해', 'en': 'Into the Abyss', 'ja': '深淵へ', 'zh': '迈向深渊', 'ru': 'В бездну'},
    'ach_ACH_FLOOR_50':    {'ko': '감옥 탈출', 'en': 'Prison Break', 'ja': '監獄脱出', 'zh': '越狱', 'ru': 'Побег из тюрьмы'},
    'ach_ACH_FIRST_BOSS':  {'ko': '거인 사냥', 'en': 'Giant Slayer', 'ja': '巨人狩り', 'zh': '巨人猎手', 'ru': 'Убийца гигантов'},
    'ach_ACH_COMBO_15':    {'ko': '멈추지 않는 칼날', 'en': 'Unstoppable Blade', 'ja': '止まらぬ刃', 'zh': '不停之刃', 'ru': 'Неудержимый клинок'},
    'ach_ACH_LEVEL_20':    {'ko': '베테랑', 'en': 'Veteran', 'ja': 'ベテラン', 'zh': '老兵', 'ru': 'Ветеран'},
    'ach_ACH_ENHANCE_10':  {'ko': '대장장이의 혼', 'en': 'Soul of the Smith', 'ja': '鍛冶屋の魂', 'zh': '铁匠之魂', 'ru': 'Душа кузнеца'},
    'ach_ACH_RICH':        {'ko': '던전의 부자', 'en': 'Dungeon Tycoon', 'ja': 'ダンジョンの富豪', 'zh': '地城富豪', 'ru': 'Магнат подземелья'},
    'ach_ACH_BURNING':     {'ko': '불길에서 살아남다', 'en': 'Through the Flames', 'ja': '炎を生き延びて', 'zh': '浴火重生', 'ru': 'Сквозь пламя'},
    'ach_ACH_ULTIMATE':    {'ko': '오의 개방', 'en': 'Ultimate Unleashed', 'ja': '奥義開放', 'zh': '奥义解放', 'ru': 'Тайна раскрыта'},
    'ach_ACH_DIE':         {'ko': '던전의 세례', 'en': 'Dungeon Baptism', 'ja': 'ダンジョンの洗礼', 'zh': '地城洗礼', 'ru': 'Крещение подземельем'},

    # ── 상태이상 배지 ───────────────────────────────────────────────────
    'debuff_curse': {'ko': '저주', 'en': 'Curse', 'ja': '呪い', 'zh': '诅咒', 'ru': 'Проклятие'},
    'debuff_slow':  {'ko': '슬로우', 'en': 'Slow', 'ja': 'スロウ', 'zh': '减速', 'ru': 'Замедление'},
    'debuff_fear':  {'ko': '두려움', 'en': 'Fear', 'ja': '恐怖', 'zh': '恐惧', 'ru': 'Страх'},

    # ── 인벤토리 아이템 타입 이름 ─────────────────────────────────────
    'inv_type_weapon': {'ko': '무기', 'en': 'Weapon', 'ja': '武器', 'zh': '武器', 'ru': 'Оружие'},
    'inv_type_armor':  {'ko': '갑옷', 'en': 'Armor', 'ja': '鎧', 'zh': '护甲', 'ru': 'Броня'},
    'inv_type_head':   {'ko': '투구', 'en': 'Head', 'ja': '兜', 'zh': '头盔', 'ru': 'Шлем'},
    'inv_type_off':    {'ko': '보조무기', 'en': 'Off-Hand', 'ja': '盾・補助', 'zh': '副手', 'ru': 'Второе оружие'},
    'inv_type_acc':    {'ko': '장신구', 'en': 'Accessory', 'ja': '装飾品', 'zh': '饰品', 'ru': 'Аксессуар'},
    'inv_type_boots':  {'ko': '신발', 'en': 'Boots', 'ja': '靴', 'zh': '鞋子', 'ru': 'Обувь'},
    'inv_type_cons':   {'ko': '소비', 'en': 'Consumable', 'ja': '消費', 'zh': '消耗品', 'ru': 'Расходник'},
    'inv_type_book':   {'ko': '스킬북', 'en': 'Skill Book', 'ja': 'スキルブック', 'zh': '技能书', 'ru': 'Книга навыка'},
    'inv_discard_btn': {'ko': '🗑 버리기', 'en': '🗑 Discard', 'ja': '🗑 捨てる', 'zh': '🗑 丢弃', 'ru': '🗑 Выбросить'},
    'inv_del_hint':    {'ko': 'Del:버리기', 'en': 'Del:Discard', 'ja': 'Del:捨てる', 'zh': 'Del:丢弃', 'ru': 'Del:Выбросить'},

    # ── 스킬 도감 추가 UI ─────────────────────────────────────────────
    'arcane_ready':         {'ko': '★ 오의 발동 가능! R키를 누르세요', 'en': '★ Arcane ready! Press R',
                             'ja': '★ 奥義発動可能! Rキーを押せ', 'zh': '★ 奥义就绪! 按R键',
                             'ru': '★ Тайное искусство готово! Нажмите R'},
    'sb_equip_slot_hint':   {'ko': '↑↓ 슬롯 선택   Enter 장착   ESC 취소',
                             'en': '↑↓ Select slot   Enter Equip   ESC Cancel',
                             'ja': '↑↓ スロット選択   Enter 装備   ESC キャンセル',
                             'zh': '↑↓ 选择槽位   Enter 装备   ESC 取消',
                             'ru': '↑↓ Слот   Enter Надеть   ESC Отмена'},
    'sb_equip_skill_hint':  {'ko': '↑↓ 스킬 선택   Enter 장착   ESC 취소',
                             'en': '↑↓ Select skill   Enter Equip   ESC Cancel',
                             'ja': '↑↓ スキル選択   Enter 装備   ESC キャンセル',
                             'zh': '↑↓ 选择技能   Enter 装备   ESC 取消',
                             'ru': '↑↓ Навык   Enter Надеть   ESC Отмена'},
    'sb_equip_confirm':     {'ko': 'Enter 장착 / ESC 취소', 'en': 'Enter Equip / ESC Cancel',
                             'ja': 'Enter 装備 / ESC キャンセル', 'zh': 'Enter 装备 / ESC 取消',
                             'ru': 'Enter Надеть / ESC Отмена'},
    'sb_key_legacy':        {'ko': '[{}키]', 'en': '[{}]', 'ja': '[{}キー]', 'zh': '[{}键]', 'ru': '[{}]'},
    'sb_slot_empty':        {'ko': '[{}] 비어 있음', 'en': '[{}] Empty', 'ja': '[{}] 空き', 'zh': '[{}] 空', 'ru': '[{}] Пусто'},

    # ── 버리기 확인 대화상자 ──────────────────────────────────────────
    'discard_confirm': {'ko': '버리시겠습니까?', 'en': 'Discard item?', 'ja': '捨てますか?', 'zh': '要丢弃吗?', 'ru': 'Выбросить предмет?'},
    'discard_yes':     {'ko': '예  [Y]', 'en': 'Yes  [Y]', 'ja': 'はい  [Y]', 'zh': '是  [Y]', 'ru': 'Да  [Y]'},
    'discard_no':      {'ko': '아니오  [N]', 'en': 'No  [N]', 'ja': 'いいえ  [N]', 'zh': '否  [N]', 'ru': 'Нет  [N]'},

    # ── 스킬 스탯 포맷 ────────────────────────────────────────────────
    'fmt_tiles':     {'ko': '{}칸 전진  CD {}s', 'en': '{} tiles fwd  CD {}s',
                      'ja': '{}マス前進  CD {}s', 'zh': '前进{}格  CD {}s', 'ru': '{} кл. вперёд  КД {}с'},
    'fmt_radius_atk':{'ko': '반경 {}  공격력 {}%  CD {}s', 'en': 'Range {}  ATK {}%  CD {}s',
                      'ja': '半径{}  攻撃力{}%  CD {}s', 'zh': '半径{}  攻击{}%  CD {}s',
                      'ru': 'Радиус {}  АТК {}%  КД {}с'},
    'fmt_mul_crit':  {'ko': '{}배 강타  치명 {}%  CD {}s', 'en': '{}x Strike  Crit {}%  CD {}s',
                      'ja': '{}倍強打  会心{}%  CD {}s', 'zh': '{}倍重击  暴击{}%  CD {}s',
                      'ru': 'x{} удар  Крит {}%  КД {}с'},
}


def t(key: str, *args) -> str:
    """번역 문자열 반환. args가 있으면 .format(*args) 적용.

    폴백 순서: 현재 언어 → en → ko → key 원문.
    """
    entry = _T.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG) or entry.get('en') or entry.get('ko', key)
    return text.format(*args) if args else text
