"""한/영 언어 전환 모듈."""

_LANG = 'ko'


def set_lang(lang: str):
    global _LANG
    _LANG = lang if lang in ('ko', 'en') else 'ko'


def get_lang() -> str:
    return _LANG


# ── 번역 테이블 ────────────────────────────────────────────────────────────
_T: dict[str, dict[str, str]] = {
    # ── HUD 섹션 헤더 ──────────────────────────────────────────────────────
    'sec_hp':        {'ko': 'HP',               'en': 'HP'},
    'sec_stats':     {'ko': '스탯',             'en': 'Stats'},
    'sec_inv':       {'ko': '빠른 아이템  [1-5]', 'en': 'Quick Items [1-5]'},
    'sec_equip':     {'ko': '장착 장비  [O]',    'en': 'Equipment  [O]'},
    'inv_title':     {'ko': '인  벤  토  리',     'en': 'Inventory'},
    'inv_hint':      {'ko': '↑↓←→ 이동   Enter 사용/장착   ESC 닫기',
                      'en': '↑↓←→ Move   Enter Use/Equip   ESC Close'},
    'equip_title':     {'ko': '장  비  장  착',     'en': 'Equipment'},
    'equip_hint':      {'ko': '↑↓←→ 이동   Enter 해제   ESC 닫기',
                        'en': '↑↓←→ Move   Enter Unequip   ESC Close'},
    'equip_none':      {'ko': '-- 없음 --',         'en': '-- None --'},
    'slot_weapon':     {'ko': '주  무  기',          'en': 'Weapon'},
    'slot_armor':      {'ko': '갑  옷',              'en': 'Armor'},
    'slot_head':       {'ko': '머  리',              'en': 'Head'},
    'slot_body':       {'ko': '몸  통',              'en': 'Body'},
    'slot_off_hand':   {'ko': '보조무기',             'en': 'Off-Hand'},
    'slot_accessory':  {'ko': '장신구',              'en': 'Accessory'},
    'slot_feet':       {'ko': '신  발',              'en': 'Boots'},
    'sec_skills':    {'ko': '스킬  [W/A/S/D]',  'en': 'Skills [W/A/S/D]'},
    'sec_combo':     {'ko': '강화 스킬',          'en': 'Enhanced Skills'},
    'sec_controls':  {'ko': '조작법',            'en': 'Controls'},
    'sec_minimap':   {'ko': '미니맵',            'en': 'Minimap'},
    'inv_empty':     {'ko': '---',              'en': '---'},

    # ── 조작법 힌트 ────────────────────────────────────────────────────────
    'ctrl_move':   {'ko': '↑↓←→',        'en': 'Arrows'},
    'ctrl_move_d': {'ko': '이동',          'en': 'Move'},
    'ctrl_atk':    {'ko': 'Space',         'en': 'Space'},
    'ctrl_atk_d':  {'ko': '공격',          'en': 'Attack'},
    'ctrl_skill':  {'ko': 'W/A/S/D',      'en': 'W/A/S/D'},
    'ctrl_skill_d':{'ko': '스킬',          'en': 'Skills'},
    'ctrl_combo':  {'ko': 'Ctrl+W/A/S/D',  'en': 'Ctrl+W/A/S/D'},
    'ctrl_combo_d':{'ko': '강화 스킬',    'en': 'Enhanced'},
    'ctrl_item':   {'ko': '1-5',           'en': '1-5'},
    'ctrl_item_d': {'ko': '아이템',        'en': 'Items'},
    'ctrl_inv':    {'ko': 'I',             'en': 'I'},
    'ctrl_inv_d':  {'ko': '인벤토리',     'en': 'Inventory'},
    'ctrl_equip':  {'ko': 'O',            'en': 'O'},
    'ctrl_equip_d':{'ko': '장비',         'en': 'Equipment'},
    'ctrl_esc':    {'ko': 'ESC',           'en': 'ESC'},
    'ctrl_esc_d':  {'ko': '저장/메뉴',    'en': 'Save/Menu'},

    # ── 단일 스킬 이름 / 설명 ─────────────────────────────────────────────
    'skill_w_name': {'ko': '섬광 돌진',    'en': 'Flash Dash'},
    'skill_w_desc': {'ko': '3칸+경직',     'en': '3-tile dash+stagger'},
    'skill_a_name': {'ko': '강철 회오리',  'en': 'Steel Whirl'},
    'skill_a_desc': {'ko': '8방향 휩쓸기', 'en': '8-dir sweep'},
    'skill_s_name': {'ko': '재생의 숨결',  'en': 'Regen Breath'},
    'skill_s_desc': {'ko': 'HP25%+방어',   'en': '+25% HP+DEF'},
    'skill_d_name': {'ko': '심판의 일격',  'en': 'Judgment Strike'},
    'skill_d_desc': {'ko': '2.5배 강타',   'en': '250% ATK'},
    # 이전 키 유지 (하위 호환)
    'skill_q_name': {'ko': '돌진',      'en': 'Dash'},
    'skill_q_desc': {'ko': '3칸 전진',  'en': '3-tile dash'},
    'skill_e_name': {'ko': '회오리',    'en': 'Whirl'},
    'skill_e_desc': {'ko': '8방향 공격','en': '8-dir atk'},
    'skill_f_name': {'ko': '치유',      'en': 'Heal'},
    'skill_f_desc': {'ko': 'HP 30%',    'en': '+30% HP'},

    # ── 메인 메뉴 ──────────────────────────────────────────────────────────
    'menu_new':      {'ko': '새  게  임',              'en': 'New  Game'},
    'menu_cont':     {'ko': '이어하기',                'en': 'Continue'},
    'menu_cont_f':   {'ko': '이어하기   B{}F',        'en': 'Continue  B{}F'},
    'menu_settings': {'ko': '설정',                    'en': 'Settings'},
    'menu_quit':     {'ko': '종료',                    'en': 'Quit'},
    'menu_hint':     {'ko': '↑↓ 선택   Enter 확인   ESC 종료',
                      'en': '↑↓ Select   Enter OK   ESC Quit'},

    # ── 메뉴 설정 패널 ─────────────────────────────────────────────────────
    'settings_title': {'ko': '설정',               'en': 'Settings'},
    'settings_back':  {'ko': '뒤로',               'en': 'Back'},
    'settings_hint':  {'ko': '↑↓ 선택   ◄► 조절   ESC 뒤로',
                       'en': '↑↓ Select   ◄► Adjust   ESC Back'},

    # ── 일시정지 메뉴 ──────────────────────────────────────────────────────
    'pause_title':  {'ko': '─ 일시 정지 ─',  'en': '─  Paused  ─'},
    'pause_resume': {'ko': '계속하기',        'en': 'Resume'},
    'pause_save':   {'ko': '저장하기',        'en': 'Save Game'},
    'pause_bgm':    {'ko': 'BGM 볼륨',        'en': 'BGM Volume'},
    'pause_sfx':    {'ko': 'SFX 볼륨',        'en': 'SFX Volume'},
    'pause_fs':     {'ko': '전체화면',         'en': 'Fullscreen'},
    'pause_fs_on':  {'ko': 'ON',              'en': 'ON'},
    'pause_fs_off': {'ko': 'OFF',             'en': 'OFF'},
    'pause_lang':   {'ko': '언어',            'en': 'Language'},
    'lang_ko':      {'ko': '한국어',          'en': 'Korean'},
    'lang_en':      {'ko': 'English',         'en': 'English'},
    'pause_title_': {'ko': '타이틀로',         'en': 'Title Screen'},
    'pause_quit':   {'ko': '종료',            'en': 'Quit'},
    'pause_hint':   {'ko': 'ESC 닫기    Space / Enter 선택',
                     'en': 'ESC Close   Space / Enter Select'},
    'adj_hint':     {'ko': '◄ ► 조절',       'en': '◄ ► Adjust'},
    'save_hint':    {'ko': 'Enter 저장',      'en': 'Enter Save'},

    # ── 게임 오버 ──────────────────────────────────────────────────────────
    'gameover':     {'ko': 'GAME OVER',       'en': 'GAME OVER'},
    'survived':     {'ko': 'Floor {} 까지 생존했습니다.',  'en': 'Survived to Floor {}.'},
    'best_rec':     {'ko': '최고 기록  Floor {}  킬 {}  G {}',
                     'en': 'Best  Floor {}  Kills {}  G {}'},
    'total_runs':   {'ko': '총 {}회 플레이',  'en': '{} total runs'},
    'go_hint':      {'ko': '[R] 재시작    [ESC] 종료', 'en': '[R] Restart    [ESC] Quit'},

    # ── 상점 ───────────────────────────────────────────────────────────────
    'shop_title':   {'ko': '상  점',          'en': 'Shop'},
    'shop_gold':    {'ko': '보유 골드: {} G', 'en': 'Gold: {} G'},
    'shop_empty':   {'ko': '품절입니다.',     'en': 'Sold out.'},
    'shop_hint':    {'ko': '[1-5] 구매    [ESC] 나가기',
                     'en': '[1-5] Buy    [ESC] Exit'},

    # ── 보스바 ─────────────────────────────────────────────────────────────
    'boss_bar':     {'ko': '★ BOSS  {}   {} / {}', 'en': '★ BOSS  {}   {} / {}'},

    # ── 인게임 메시지 ──────────────────────────────────────────────────────
    'welcome':      {'ko': 'Dungeon Door에 오신 걸 환영합니다!',
                     'en': 'Welcome to Dungeon Door!'},
    'wasd_hint':    {'ko': '↑↓←→ 이동 / Space 공격 / W·A·S·D 스킬 / ESC 저장·메뉴',
                     'en': 'Arrows Move / Space Attack / W·A·S·D Skills / ESC Save·Menu'},
    'floor_arrive': {'ko': 'Floor {}에 도착했습니다.',   'en': 'Arrived at Floor {}.'},
    'floor_cont':   {'ko': 'Floor {} 에서 계속합니다.', 'en': 'Continuing from Floor {}.'},
    'boss_incoming':{'ko': '★ 보스가 기다리고 있다!',   'en': '★ The boss awaits!'},
    'shop_floor':   {'ko': '상점이 있는 층입니다.',       'en': 'A shop is on this floor.'},
    'auto_saved':   {'ko': '✓ 자동 저장됨',              'en': '✓ Auto-saved'},
    'saved':        {'ko': '✓ 저장됨',                   'en': '✓ Saved'},

    # ── 전투 메시지 ────────────────────────────────────────────────────────
    'crit_hit':     {'ko': '★ 치명타! {}에게 {} 피해!', 'en': '★ Crit! {} hit for {}!'},
    'normal_hit':   {'ko': '▶ {}에게 {} 피해',          'en': '▶ {} hit for {}'},
    'kill_gold':    {'ko': '{} 처치! +{} XP  +{} G',   'en': '{} killed! +{} XP  +{} G'},
    'kill':         {'ko': '{} 처치! +{} XP',           'en': '{} killed! +{} XP'},
    'levelup':      {'ko': '레벨업! Lv.{}  HP 회복!',   'en': 'Level Up! Lv.{}  HP restored!'},
    'pickup':       {'ko': '{} 획득!',                   'en': '{} picked up!'},
    'inv_full':     {'ko': '인벤토리가 가득 찼습니다!',  'en': 'Inventory is full!'},
    'buy_ok':       {'ko': '{} 구매! -{} G',             'en': '{} bought! -{} G'},
    'no_gold':      {'ko': '골드가 부족합니다!',         'en': 'Not enough gold!'},
    'teleport':     {'ko': '✦ 텔레포트!',               'en': '✦ Teleport!'},
    'skill_cd':     {'ko': '스킬 재충전 중... ({:.1f}s)','en': 'Skill on cooldown... ({:.1f}s)'},
    'skill_dash':   {'ko': '⚡ 돌진! {}칸',             'en': '⚡ Dash! {} tiles'},
    'skill_whirl_h':{'ko': '🌀 회오리! {}마리 타격',    'en': '🌀 Whirl! Hit {}'},
    'skill_whirl_m':{'ko': '🌀 회오리 — 적 없음',       'en': '🌀 Whirl — no enemies'},
    'skill_heal':   {'ko': '✨ 치유! HP +{}',            'en': '✨ Heal! HP +{}'},
    'boss_clear':   {'ko': '★ 보스를 처치했습니다! 계단이 나타났습니다!',
                     'en': '★ Boss defeated! Stairs appeared!'},

    # ── 스킬 전투 메시지 추가 ──────────────────────────────────────────────
    'skill_power':      {'ko': '💥 강타! {}에게 {} 피해',         'en': '💥 Power! Hit {} for {}'},
    'skill_power_miss': {'ko': '💥 강타! 빗나감',                  'en': '💥 Power Strike! Miss'},
    'skill_fireball':   {'ko': '🔥 파이어볼! {}에게 {} 피해',     'en': '🔥 Fireball! Hit {} for {}'},
    'skill_fireball_m': {'ko': '🔥 파이어볼! 빗나감',              'en': '🔥 Fireball! Miss'},
    'skill_thunder':    {'ko': '⚡ 천둥격! {}마리 타격',           'en': '⚡ Thunder! Hit {}'},
    'skill_thunder_m':  {'ko': '⚡ 천둥격! 적 없음',               'en': '⚡ Thunder! No targets'},
    'skill_frost':      {'ko': '❄ 냉기 폭발! {}마리 타격',        'en': '❄ Frost! Hit {}'},
    'skill_frost_m':    {'ko': '❄ 냉기 폭발! 적 없음',             'en': '❄ Frost! No targets'},
    'skill_wind':       {'ko': '💨 바람 칼날! {}마리 관통',        'en': '💨 Wind! Pierce {}'},
    'skill_wind_m':     {'ko': '💨 바람 칼날! 빗나감',              'en': '💨 Wind Blade! Miss'},
    'skill_fortify':    {'ko': '✨ 강화술! 공속 +{} 방어 +{} ({}초)', 'en': '✨ Fortify! Spd +{} Def +{} ({}s)'},
    'skill_fortify_end':{'ko': '강화술 효과가 사라졌다.',             'en': 'Fortify faded.'},

    # ── 버닝 스테이지 ─────────────────────────────────────────────────────
    'burning_enter':    {'ko': '🔥 버닝 스테이지! 60초를 버텨라!',   'en': '🔥 Burning Stage! Survive 60 seconds!'},
    'burning_wave':     {'ko': '🔥 파도 {}!',                         'en': '🔥 Wave {}!'},
    'burning_survived': {'ko': '🏆 생존! 보스 스테이지로 이동!',      'en': '🏆 Survived! Moving to Boss Stage!'},
    'burning_failed':   {'ko': '💀 쓰러졌다. 현재 층으로 복귀.',      'en': '💀 Defeated. Returning to current floor.'},
    'burning_10sec':    {'ko': '⚠ 10초 남았다!',                      'en': '⚠ 10 seconds left!'},

    # ── 강화 스킬 해금 메시지 ─────────────────────────────────────────────
    'combo_unlock':     {'ko': '★ {} 해금!',                       'en': '★ {} unlocked!'},
    'combo_need_level': {'ko': '{} 스킬북 획득! (Lv.{} 달성 시 해금)',
                         'en': '{} skill book! (Unlock at Lv.{})'},
    'combo_no_book':    {'ko': '{} — 스킬북을 찾으세요',           'en': '{} — find the skill book'},
    'combo_no_unlock':  {'ko': '{} — 스킬북 + Lv.{} 필요',        'en': '{} — need book + Lv.{}'},

    # ── 스킬 강화 패널 ────────────────────────────────────────────────────
    'upg_title':   {'ko': '스킬  강화',                           'en': 'Skill  Upgrade'},
    'upg_sp':      {'ko': 'SP  {}',                               'en': 'SP  {}'},
    'upg_hint':    {'ko': '↑↓ 선택   Space 강화   ESC 닫기',     'en': '↑↓ Select   Space Upgrade   ESC Close'},
    'upg_confirm': {'ko': 'Space: 강화',                          'en': 'Space: Upgrade'},
    'upg_max':     {'ko': '최대 레벨',                            'en': 'MAX Level'},
    'upg_done':    {'ko': '{} 강화! Lv.{}',                       'en': '{} upgraded! Lv.{}'},
    'upg_no_sp':   {'ko': 'SP 부족!',                             'en': 'No SP!'},
    'sp_badge':    {'ko': '★ SP {}  [U] 스킬 강화',              'en': '★ SP {}  [U] Upgrade'},
    'ctrl_upg':    {'ko': 'U',                                    'en': 'U'},
    'ctrl_upg_d':  {'ko': '스킬 강화',                            'en': 'Skill Upg'},

    # ── 아이템 사용 메시지 ─────────────────────────────────────────────────
    'item_heal':    {'ko': '{} 사용! HP +{}',            'en': '{} used! HP +{}'},
    'item_atk':     {'ko': '{} 장착! ATK +{}',           'en': '{} equipped! ATK +{}'},
    'item_def':     {'ko': '{} 장착! DEF +{}',           'en': '{} equipped! DEF +{}'},
    'item_all':     {'ko': '{} 착용! ATK+{} DEF+{}',     'en': '{} worn! ATK+{} DEF+{}'},
    'item_use':     {'ko': '{} 사용',                    'en': '{} used'},

    # ── 테마 / 999층 ──────────────────────────────────────────────────
    'new_theme':    {'ko': '◆ 새로운 구역: {}',          'en': '◆ New Zone: {}'},
    'victory':      {'ko': '★★★ 축하합니다! 999층 클리어! ★★★',
                     'en': '★★★ Congratulations! Floor 999 cleared! ★★★'},
}


def t(key: str, *args) -> str:
    """번역 문자열 반환. args가 있으면 .format(*args) 적용."""
    entry = _T.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG, entry.get('ko', key))
    return text.format(*args) if args else text
