"""마을 퀘스트 정의 — 시민 NPC가 주는 스토리형 의뢰.

상태 흐름: available → (수락) active → (목표 달성) done → (보고) claimed
진행 추적: Game이 킬/층 도달 훅에서 _quest_on_kill/_quest_on_floor 호출.
텍스트는 퀘스트별 5개 언어 내장 — qtext(qid, field)로 해석.
"""
from core.lang import get_lang

# kind: kill_any(아무 몬스터 n) | kill_key(특정 몬스터 n) | reach_floor(층 도달)
QUESTS = {
    'rat_hunt': {
        'giver': 'villager_boy',
        'kind': 'kill_any', 'count': 10,
        'reward': {'gold': 100, 'items': ['repair_kit']},
        'text': {
            'name':  {'ko': '몬스터 소탕 연습', 'en': 'Monster Culling', 'ja': 'モンスター討伐の練習',
                      'zh': '怪物清剿练习', 'ru': 'Отстрел монстров'},
            'desc':  {'ko': '몬스터 10마리 사냥하기', 'en': 'Hunt 10 monsters', 'ja': 'モンスターを10体倒す',
                      'zh': '猎杀10只怪物', 'ru': 'Убейте 10 монстров'},
            'offer': {'ko': '용사님! 저도 커서 모험가가 될 거예요. 몬스터를 10마리 잡는 걸 보여주시면 안 돼요? 아빠 몰래 모은 용돈으로 보답할게요!',
                      'en': "Hero! I wanna be an adventurer too. Could you show me by hunting 10 monsters? I'll pay you with my secret allowance!",
                      'ja': '勇者さま! ぼくも大きくなったら冒険者になるんだ。モンスターを10体倒すところを見せてくれない? こっそり貯めたお小遣いでお礼するよ!',
                      'zh': '勇士！我长大也想当冒险家。能猎杀10只怪物给我看看吗？我用偷偷攒的零花钱谢你！',
                      'ru': 'Герой! Я тоже хочу стать искателем приключений. Покажешь, как бьёшь монстров? Убей 10 штук — отдам все свои карманные!'},
            'active':{'ko': '우와, 벌써 사냥 중이시죠? 힘내세요!', 'en': "You're already hunting, right? Go go!",
                      'ja': 'もう狩りに出てるんでしょ? がんばって!', 'zh': '已经在猎杀了吧？加油！',
                      'ru': 'Ты уже охотишься, да? Давай-давай!'},
            'done':  {'ko': '10마리라니 대단해요!! 약속한 보답이에요. 저도 언젠가...!',
                      'en': "Ten already?! Amazing!! Here's your reward. Someday I'll...!",
                      'ja': '10体も!? すごい!! 約束のお礼だよ。ぼくもいつか...!',
                      'zh': '居然10只了！太厉害了！！这是答应你的报酬。总有一天我也...！',
                      'ru': 'Целых десять?! Невероятно!! Вот награда. Однажды и я...!'},
            'claimed':{'ko': '용사님 최고! 나중에 꼭 제 검술도 봐주세요.', 'en': "You're the best! Check my sword skills someday.",
                       'ja': '勇者さま最高! 今度ぼくの剣術も見てね。', 'zh': '勇士最棒了！以后也看看我的剑术吧。',
                       'ru': 'Ты лучший! Как-нибудь оцени и мою технику меча.'},
        },
    },
    'centipede_menace': {
        'giver': 'villager_farmer',
        'kind': 'kill_key', 'key': 'centipede', 'count': 5,
        'reward': {'gold': 150, 'stones': 2},
        'text': {
            'name':  {'ko': '밭을 망치는 지네들', 'en': 'Centipede Menace', 'ja': '畑を荒らすムカデ',
                      'zh': '祸害田地的蜈蚣', 'ru': 'Нашествие многоножек'},
            'desc':  {'ko': '마을을 괴롭히는 지네 5마리 잡아오기', 'en': 'Slay 5 centipedes plaguing the town',
                      'ja': '村を悩ませるムカデを5匹退治', 'zh': '消灭5只骚扰村庄的蜈蚣',
                      'ru': 'Убейте 5 многоножек, донимающих деревню'},
            'offer': {'ko': '던전에서 기어 나온 지네들이 밭을 다 갉아먹고 있소! 다섯 마리만 잡아주면 아껴둔 강화석을 내드리리다.',
                      'en': 'Centipedes crawling out of the dungeon are eating my crops! Slay five and my spare enhancement stones are yours.',
                      'ja': 'ダンジョンから這い出たムカデどもが畑を食い荒らしとる! 5匹退治してくれたら、取っておきの強化石をやろう。',
                      'zh': '从地城爬出来的蜈蚣把庄稼都啃光了！干掉五只，我珍藏的强化石就归你。',
                      'ru': 'Многоножки из подземелья жрут мой урожай! Убей пятерых — отдам припасённые камни усиления.'},
            'active':{'ko': '지네는 던전 얕은 층에 우글거리니 그쪽을 뒤져보시게.', 'en': 'They swarm the shallow floors — look there.',
                      'ja': 'ムカデは浅い階にうようよおる。そっちを探すんじゃ。', 'zh': '蜈蚣在浅层成群，去那儿找找。',
                      'ru': 'Они кишат на верхних этажах — ищи там.'},
            'done':  {'ko': '오오, 이제 발 뻗고 자겠구먼! 약속한 강화석이오. 고맙소, 용사 양반!',
                      'en': 'Now I can finally sleep! Here are the stones as promised. Thank you, hero!',
                      'ja': 'おお、これで枕を高くして眠れるわい! 約束の強化石じゃ。ありがとうよ、勇者どの!',
                      'zh': '哦哦，这下能睡个安稳觉了！这是答应你的强化石。多谢了，勇士！',
                      'ru': 'Наконец-то высплюсь! Вот обещанные камни. Спасибо, герой!'},
            'claimed':{'ko': '밭이 살아났소. 언제든 들르시게!', 'en': 'The fields are recovering. Drop by anytime!',
                       'ja': '畑が息を吹き返したわい。いつでも寄ってくれ!', 'zh': '田地缓过来了。随时来坐坐！',
                       'ru': 'Поля оживают. Заходи в любое время!'},
        },
    },
    'rescue_girl': {
        'giver': 'villager_granny',
        'kind': 'reach_floor', 'floor': 10,
        'reward': {'gold': 400, 'stones': 3, 'items': ['large_health_potion']},
        'text': {
            'name':  {'ko': '지하 10층의 손녀', 'en': 'The Girl on Floor 10', 'ja': '地下10階の孫娘',
                      'zh': '地下10层的孙女', 'ru': 'Внучка на 10-м этаже'},
            'desc':  {'ko': '지하 10층을 탐험하여 소녀를 구출하기', 'en': 'Explore down to floor 10 and rescue the girl',
                      'ja': '地下10階を探索して少女を救出する', 'zh': '探索地下10层营救少女',
                      'ru': 'Спуститесь на 10-й этаж и спасите девочку'},
            'offer': {'ko': '흑흑... 약초를 캐러 간 손녀가 던전 깊은 곳까지 쓸려 갔다오. 지하 10층까지 가서 그 아이를 찾아 주시오... 부탁이오, 용사님.',
                      'en': 'Sob... my granddaughter went herb-picking and got swept deep into the dungeon. Please reach floor 10 and find her... I beg you, hero.',
                      'ja': 'うぅ... 薬草を摘みに行った孫娘がダンジョンの奥まで流されてしもうた。地下10階まで行ってあの子を捜しておくれ... 頼む、勇者さま。',
                      'zh': '呜呜...去采药草的孙女被卷进了地城深处。请到地下10层找到她...拜托了，勇士。',
                      'ru': 'Всхлип... внучка пошла за травами, и её унесло вглубь подземелья. Доберись до 10-го этажа и найди её... умоляю, герой.'},
            'active':{'ko': '부디... 그 아이가 무사하기를. 지하 10층이오.', 'en': 'Please... let her be safe. Floor 10.',
                      'ja': 'どうか... あの子が無事でありますように。地下10階じゃ。', 'zh': '但愿...那孩子平安。是地下10层。',
                      'ru': 'Лишь бы она была цела... 10-й этаж.'},
            'done':  {'ko': '손녀가 무사히 돌아왔다오!! 이 은혜를 어찌 갚아야 할지... 얼마 안 되지만 받아 주시오!',
                      'en': 'My granddaughter is home safe!! How can I ever repay you... please, take this!',
                      'ja': '孫娘が無事に帰ってきたんじゃ!! この恩をどう返せば... 少ないがこれを受け取っておくれ!',
                      'zh': '孙女平安回来了！！这份恩情该怎么还...不多，请一定收下！',
                      'ru': 'Внучка вернулась целой!! Как же тебя отблагодарить... вот, возьми, прошу!'},
            'claimed':{'ko': '손녀가 용사님 얘기만 한다오. 허허.', 'en': 'She talks about you all day. Hehe.',
                       'ja': '孫娘は勇者さまの話ばかりしとるよ。ほっほ。', 'zh': '孙女整天念叨着勇士呢。呵呵。',
                       'ru': 'Она только о тебе и говорит. Хе-хе.'},
        },
    },
}

# 시민 NPC 표시 이름 (마을 이름표)
GIVER_NAMES = {
    'villager_boy':    {'ko': '꼬마 한스', 'en': 'Little Hans', 'ja': 'ちびハンス', 'zh': '小汉斯', 'ru': 'Малыш Ганс'},
    'villager_farmer': {'ko': '농부 브람', 'en': 'Farmer Bram', 'ja': '農夫ブラム', 'zh': '农夫布拉姆', 'ru': 'Фермер Брам'},
    'villager_granny': {'ko': '마르타 할멈', 'en': 'Granny Marta', 'ja': 'マルタばあさん', 'zh': '玛尔塔奶奶', 'ru': 'Бабушка Марта'},
}


def _resolve(table: dict) -> str:
    lang = get_lang()
    return table.get(lang) or table.get('en') or table.get('ko', '')


def qtext(qid: str, field: str) -> str:
    """퀘스트 텍스트를 현재 언어로 해석."""
    q = QUESTS.get(qid)
    return _resolve(q['text'][field]) if q else ''


def giver_name(giver_id: str) -> str:
    return _resolve(GIVER_NAMES.get(giver_id, {'ko': giver_id}))


def fresh_states() -> dict:
    """새 런의 퀘스트 상태 테이블."""
    return {qid: {'state': 'available', 'progress': 0} for qid in QUESTS}


def objective_str(qid: str, progress: int) -> str:
    """실시간 목표 문자열 — '3/10' 또는 'B7F/B10F'."""
    q = QUESTS[qid]
    if q['kind'] == 'reach_floor':
        return f"B{progress}F/B{q['floor']}F"
    return f"{min(progress, q['count'])}/{q['count']}"
