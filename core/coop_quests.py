"""협동(co-op) 전용 퀘스트 — '용병 길드 게시판'이 주는 파티 의뢰.

마을 시민 퀘스트(core/quests.py)와 구조는 같지만, 멀티플레이 세션에 접속해
있을 때만 게시판에서 수락·추적·보고할 수 있다. 진행도는 각 플레이어가 자기
클라에서 로컬 추적하며(협동 킬/부활/동반 하강), 보고 시 보상은 자기 플레이어에
지급된다.

상태 흐름: available → active → done → claimed (villager 퀘스트와 동일).
체인: 게시판이 3개 의뢰를 순서대로 제공(앞 의뢰 보고 시 다음 개방).
kind:
  coop_kill   — 협동 던전에서 파티가 몬스터 count마리 처치
  coop_revive — 파티원을 count회 부활
  coop_floor  — 협동으로 floor층까지 함께 하강
"""
from core.lang import get_lang

BOARD_ID = 'party_board'

COOP_QUESTS = {
    # 1) 파티 사냥 — 함께 50킬
    'party_hunt': {
        'kind': 'coop_kill', 'count': 50,
        'reward': {'gold': 600, 'stones': 3},
        'text': {
            'name':  {'ko': '파티 사냥 계약', 'en': 'Party Bounty', 'ja': 'パーティ狩りの契約',
                      'zh': '组队悬赏', 'ru': 'Групповой контракт'},
            'desc':  {'ko': '협동 던전에서 몬스터 50마리 처치', 'en': 'Slay 50 monsters in co-op',
                      'ja': '協力ダンジョンでモンスターを50体倒す', 'zh': '在协作地城击杀50只怪物',
                      'ru': 'Убейте 50 монстров в co-op'},
            'offer': {'ko': '용병들이여, 던전이 들끓고 있소. 둘이 힘을 합쳐 50마리를 정리해주면 길드가 두둑이 사례하지.',
                      'en': 'Mercenaries! The dungeon teems. Clear 50 together and the guild pays well.',
                      'ja': '傭兵たちよ、ダンジョンが騒がしい。二人で50体片付ければギルドが報いる。',
                      'zh': '佣兵们，地城骚动不安。你们联手清掉50只，公会重谢。',
                      'ru': 'Наёмники! Подземелье кишит. Убейте 50 вместе — гильдия щедро заплатит.'},
            'active':{'ko': '함께 사냥 중이군. 파티의 킬은 모두 계산되네.', 'en': 'Hunting together — every party kill counts.',
                      'ja': '一緒に狩ってるな。パーティのキルは全部数える。', 'zh': '在一起狩猎呢。队伍的击杀都算数。',
                      'ru': 'Охотитесь вместе — каждое убийство в счёт.'},
            'done':  {'ko': '50마리라니! 역시 손발이 맞는 파티는 다르군. 약속한 보상이오.',
                      'en': 'Fifty! A team in sync is a fearsome thing. Your reward.',
                      'ja': '50体とは! 息の合ったパーティは違うな。約束の報酬だ。',
                      'zh': '五十只！默契的队伍就是不一样。这是报酬。',
                      'ru': 'Полсотни! Слаженная команда — грозная сила. Вот награда.'},
            'claimed':{'ko': '길드는 언제나 실력 있는 파티를 환영하네.', 'en': 'The guild always welcomes a capable party.',
                       'ja': 'ギルドは腕利きのパーティをいつでも歓迎する。', 'zh': '公会随时欢迎有本事的队伍。',
                       'ru': 'Гильдия всегда рада умелой команде.'},
        },
    },
    # 2) 전우애 — 파티원 3회 부활
    'brotherhood': {
        'unlock': {'after': 'party_hunt'},
        'kind': 'coop_revive', 'count': 3,
        'reward': {'gold': 500, 'items': ['war_pendant']},
        'text': {
            'name':  {'ko': '전우애의 증표', 'en': 'Bond of Brothers', 'ja': '戦友の証',
                      'zh': '战友之证', 'ru': 'Узы товарищей'},
            'desc':  {'ko': '쓰러진 파티원을 3회 부활시키기', 'en': 'Revive fallen party members 3 times',
                      'ja': '倒れた仲間を3回蘇生する', 'zh': '复活倒下的队友3次',
                      'ru': 'Поднимите павших союзников 3 раза'},
            'offer': {'ko': '진짜 파티는 위기에서 드러나지. 쓰러진 동료를 세 번 일으켜 세우면, 이 장신구를 주겠네.',
                      'en': "A true party shows in crisis. Raise a fallen ally three times and this pendant is yours.",
                      'ja': '本物のパーティは危機で分かる。倒れた仲間を三度起こせば、この装身具をやろう。',
                      'zh': '真正的队伍在危机中显现。把倒下的同伴扶起三次，这护符就归你。',
                      'ru': 'Настоящая команда видна в беде. Подними павшего трижды — и подвеска твоя.'},
            'active':{'ko': '동료 곁에 서서 지켜주게. 부활은 저절로 진행되지.', 'en': 'Stand by your ally — the revive fills on its own.',
                      'ja': '仲間の傍に立て。蘇生はひとりでに進む。', 'zh': '守在同伴身边，复活会自动进行。',
                      'ru': 'Стой рядом с союзником — воскрешение идёт само.'},
            'done':  {'ko': '세 번이나 동료를 구했군. 이게 전우애의 증표일세.', 'en': 'Three saves. This is the mark of true camaraderie.',
                      'ja': '三度も仲間を救ったか。これが戦友の証だ。', 'zh': '救了三次同伴。这就是战友之证。',
                      'ru': 'Трижды спас товарища. Вот знак истинного братства.'},
            'claimed':{'ko': '서로를 지키는 파티는 무너지지 않네.', 'en': 'A party that guards each other never falls.',
                       'ja': '互いを守るパーティは崩れない。', 'zh': '互相守护的队伍不会崩溃。',
                       'ru': 'Команда, что бережёт друг друга, не падёт.'},
        },
    },
    # 3) 동반 하강 — 함께 5층 도달
    'deep_bond': {
        'unlock': {'after': 'brotherhood'},
        'kind': 'coop_floor', 'floor': 5,
        'reward': {'gold': 800, 'stones': 4, 'items': ['large_health_potion']},
        'text': {
            'name':  {'ko': '동반 하강', 'en': 'Descent Together', 'ja': '共に潜る',
                      'zh': '结伴深入', 'ru': 'Спуск вдвоём'},
            'desc':  {'ko': '협동으로 지하 5층까지 함께 도달', 'en': 'Reach floor 5 together in co-op',
                      'ja': '協力で地下5階まで共に到達', 'zh': '协作抵达地下5层',
                      'ru': 'Дойдите до 5-го этажа вместе'},
            'offer': {'ko': '혼자선 못 가는 깊이도 둘이면 갈 수 있지. 함께 지하 5층까지 내려가 보게. 길드의 신뢰를 증명하는 걸세.',
                      'en': "Depths one can't reach alone, two can. Descend to floor 5 together — prove your bond to the guild.",
                      'ja': '一人では届かぬ深さも二人なら行ける。共に地下5階まで潜れ。ギルドへの信頼の証だ。',
                      'zh': '一人到不了的深度，两人可以。一起下到地下5层，向公会证明你们的羁绊。',
                      'ru': 'Глубины, куда не дойти одному, покорятся двоим. Спуститесь на 5-й этаж вместе.'},
            'active':{'ko': '함께 내려가야 인정되네. 파티를 잃지 말게.', 'en': 'Only counts if you descend together — keep your party.',
                      'ja': '共に降りてこそ認められる。パーティを失うな。', 'zh': '一起下去才算数。别失散了。',
                      'ru': 'Засчитается, только если спуститесь вместе. Держитесь.'},
            'done':  {'ko': '지하 5층까지 함께라니! 이 파티라면 더 깊이도 가겠군. 자, 보상이오.',
                      'en': 'Floor 5, side by side! This party could go deeper still. Your reward.',
                      'ja': '地下5階まで共にとは! このパーティならもっと深くも行ける。さあ報酬だ。',
                      'zh': '一起到了地下5层！这队伍还能更深。来，报酬。',
                      'ru': 'Пятый этаж — плечом к плечу! Такой команде и глубже по силам. Награда.'},
            'claimed':{'ko': '더 깊은 곳에서 또 보세, 용병들.', 'en': 'See you deeper down, mercenaries.',
                       'ja': 'もっと深い所でまた会おう、傭兵たち。', 'zh': '更深处再会，佣兵们。',
                       'ru': 'Увидимся глубже, наёмники.'},
        },
    },
}

BOARD_NAME = {'ko': '용병 길드 게시판', 'en': 'Mercenary Guild Board',
              'ja': '傭兵ギルド掲示板', 'zh': '佣兵公会告示板', 'ru': 'Доска гильдии наёмников'}


def _resolve(table: dict) -> str:
    lang = get_lang()
    return table.get(lang) or table.get('en') or table.get('ko', '')


def board_name() -> str:
    return _resolve(BOARD_NAME)


def qtext(qid: str, field: str) -> str:
    q = COOP_QUESTS.get(qid)
    return _resolve(q['text'][field]) if q else ''


def fresh_states() -> dict:
    return {qid: {'state': 'available', 'progress': 0} for qid in COOP_QUESTS}


def objective_str(qid: str, progress: int) -> str:
    q = COOP_QUESTS[qid]
    if q['kind'] == 'coop_floor':
        return f"B{progress}F/B{q['floor']}F"
    return f"{min(progress, q['count'])}/{q['count']}"


def quest_target(qid: str) -> int:
    q = COOP_QUESTS[qid]
    return q['floor'] if q['kind'] == 'coop_floor' else q['count']


def _chain() -> list:
    return list(COOP_QUESTS.keys())


def is_unlocked(qid: str, states: dict) -> bool:
    u = COOP_QUESTS[qid].get('unlock')
    if not u:
        return True
    if 'after' in u and states.get(u['after'], {}).get('state') != 'claimed':
        return False
    return True


def current_quest(states: dict):
    """게시판이 지금 제공할 협동 퀘스트 id — 체인에서 아직 안 끝난 첫 퀘스트."""
    for qid in _chain():
        st = states.get(qid, {}).get('state', 'available')
        if st == 'claimed':
            continue
        return qid if is_unlocked(qid, states) else None
    return None
