"""마을 퀘스트 정의 — 시민 NPC가 주는 스토리형 의뢰.

상태 흐름: available → (수락) active → (목표 달성) done → (보고) claimed
개방(unlock): 층 도달(floor) 또는 선행 퀘스트 완료(after) 조건.
체인: 한 시민(giver)이 여러 퀘스트를 순서대로 제공 — 앞 퀘를 완료하면
      다음 퀘가 열린다. 깊이 내려갈수록 새 시민이 마을에 등장한다.
추적: Game이 킬/층 도달 훅에서 _quest_on_kill/_quest_on_floor 호출.
텍스트는 퀘스트별 5개 언어 내장 — qtext(qid, field)로 해석.
"""
from core.lang import get_lang

# kind: kill_any(아무 n) | kill_key(특정 몬스터 n) | kill_elite(엘리트 n) | reach_floor
# unlock: 없음 | {'floor': N} | {'after': 'qid'}
QUESTS = {
    # ── 꼬마 한스 (villager_boy) — 1층부터 ─────────────────────────────
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
    'boy_veteran': {
        'giver': 'villager_boy', 'unlock': {'after': 'rat_hunt'},
        'kind': 'kill_any', 'count': 30,
        'reward': {'gold': 250, 'stones': 1, 'items': ['large_health_potion']},
        'text': {
            'name':  {'ko': '진짜 모험가의 증표', 'en': "A True Adventurer's Proof", 'ja': '本物の冒険者の証',
                      'zh': '真正冒险家的证明', 'ru': 'Знак настоящего героя'},
            'desc':  {'ko': '몬스터 30마리 사냥하기', 'en': 'Hunt 30 monsters', 'ja': 'モンスターを30体倒す',
                      'zh': '猎杀30只怪物', 'ru': 'Убейте 30 монстров'},
            'offer': {'ko': '용사님 덕에 저도 결심했어요! 이번엔 30마리… 아니 100마리라도 보고 싶어요! 제 저금통을 통째로 드릴게요!',
                      'en': "You inspired me! This time 30 monsters — no, a hundred! I'll give you my whole piggy bank!",
                      'ja': '勇者さまのおかげで決心したんだ! 今度は30体…いや100体でも見たい! 貯金箱ごとあげる!',
                      'zh': '因为勇士我下定决心了！这次30只…不，一百只我都想看！我把存钱罐都给你！',
                      'ru': 'Ты меня вдохновил! На этот раз 30… нет, сотню! Отдам всю копилку!'},
            'active':{'ko': '30마리! 셀 수 있어요, 저 산수 잘해요!', 'en': "Thirty! I can count that, I'm good at math!",
                      'ja': '30体! ぼく算数得意だから数えられるよ!', 'zh': '30只！我数学好，数得过来！',
                      'ru': 'Тридцать! Я умею считать, я молодец в математике!'},
            'done':  {'ko': '와아아 진짜 영웅이다!! 저금통 전부 받으세요!', 'en': 'Whoaaa a real hero!! Take the whole bank!',
                      'ja': 'うわああ本物の英雄だ!! 貯金箱まるごとどうぞ!', 'zh': '哇啊啊真正的英雄！！存钱罐全给你！',
                      'ru': 'Ого-о настоящий герой!! Забирай всю копилку!'},
            'claimed':{'ko': '저도 언젠가 용사님처럼!', 'en': "Someday I'll be just like you!",
                       'ja': 'ぼくもいつか勇者さまみたいに!', 'zh': '总有一天我也要像勇士一样！',
                       'ru': 'Однажды я стану таким, как ты!'},
        },
    },

    # ── 농부 브람 (villager_farmer) — 1층부터 ──────────────────────────
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
    'farmer_slimes': {
        'giver': 'villager_farmer', 'unlock': {'after': 'centipede_menace'},
        'kind': 'kill_key', 'key': 'slime', 'count': 8,
        'reward': {'gold': 220, 'stones': 2},
        'text': {
            'name':  {'ko': '우물을 더럽히는 슬라임', 'en': 'Slime in the Well', 'ja': '井戸を汚すスライム',
                      'zh': '污染水井的史莱姆', 'ru': 'Слизь в колодце'},
            'desc':  {'ko': '슬라임 8마리 처치하기', 'en': 'Defeat 8 slimes', 'ja': 'スライムを8体倒す',
                      'zh': '击败8只史莱姆', 'ru': 'Убейте 8 слизней'},
            'offer': {'ko': '이번엔 슬라임 놈들이 우물까지 스며들었소! 여덟 마리만 처리해주면 또 사례하리다.',
                      'en': "Now slimes have oozed into our well! Clear out eight and I'll pay you again.",
                      'ja': '今度はスライムどもが井戸まで入り込んどる! 8体片付けてくれたらまた礼をするぞ。',
                      'zh': '这次史莱姆连水井都渗进去了！清掉八只，我再谢你。',
                      'ru': 'Теперь слизни забрались в колодец! Убери восьмерых — снова отблагодарю.'},
            'active':{'ko': '슬라임은 물기 있는 곳을 좋아하지.', 'en': 'Slimes love the damp corners.',
                      'ja': 'スライムは湿ったところが好きじゃ。', 'zh': '史莱姆喜欢潮湿的角落。',
                      'ru': 'Слизни любят сырые углы.'},
            'done':  {'ko': '물맛이 돌아왔소! 자, 받으시게.', 'en': 'The water tastes clean again! Here, take this.',
                      'ja': '水の味が戻った! さあ、受け取れ。', 'zh': '水又变清了！来，收下吧。',
                      'ru': 'Вода снова чистая! Вот, держи.'},
            'claimed':{'ko': '용사 양반은 우리 마을 은인이오.', 'en': "You're this town's savior, hero.",
                       'ja': '勇者どのは村の恩人じゃ。', 'zh': '勇士是我们村的恩人。',
                       'ru': 'Ты — спаситель нашей деревни, герой.'},
        },
    },

    # ── 마르타 할멈 (villager_granny) — 3층 개방 ───────────────────────
    'rescue_girl': {
        'giver': 'villager_granny', 'unlock': {'floor': 3},
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

    # ── 사냥꾼 가로 (villager_hunter) — 5층에서 등장 ───────────────────
    'hunter_elites': {
        'giver': 'villager_hunter', 'unlock': {'floor': 5},
        'kind': 'kill_elite', 'count': 3,
        'reward': {'gold': 350, 'stones': 2, 'items': ['repair_kit']},
        'text': {
            'name':  {'ko': '변종 사냥 계약', 'en': 'Elite Bounty', 'ja': '変種狩りの契約',
                      'zh': '精英悬赏', 'ru': 'Контракт на элиту'},
            'desc':  {'ko': '엘리트 변종 3마리 처치하기', 'en': 'Slay 3 elite variants', 'ja': 'エリート変種を3体倒す',
                      'zh': '击杀3只精英变种', 'ru': 'Убейте 3 элитных монстров'},
            'offer': {'ko': '오라를 두른 변종 놈들이 부쩍 늘었어. 나 혼자론 벅차. 세 놈만 처리해주면 사냥꾼의 보수를 두둑이 쳐주지.',
                      'en': "Aura-cloaked variants are multiplying, and I'm outmatched. Take down three and I'll pay a hunter's bounty.",
                      'ja': 'オーラをまとった変種が増えてきた。俺一人じゃ手に負えん。3体片付けてくれたら狩人の報酬をたっぷり払う。',
                      'zh': '带光环的变种越来越多，我一个人应付不来。干掉三只，我给你猎人的丰厚赏金。',
                      'ru': 'Мутантов в аурах всё больше, мне одному не справиться. Убей троих — заплачу как охотник.'},
            'active':{'ko': '변종은 색색의 오라로 티가 나지. 깊은 층일수록 많아.', 'en': 'Elites glow with colored auras — deeper floors have more.',
                      'ja': '変種は色付きのオーラで分かる。深い階ほど多い。', 'zh': '精英会发出彩色光环——越深越多。',
                      'ru': 'Элита светится цветной аурой. Чем глубже — тем больше.'},
            'done':  {'ko': '역시 실력자군. 약속대로 보수와 강화석일세.', 'en': 'You\'ve got the skill. Your bounty and stones, as promised.',
                      'ja': 'さすがの腕前だ。約束通り報酬と強化石だ。', 'zh': '果然有本事。这是约定的赏金和强化石。',
                      'ru': 'Мастерски. Вот награда и камни, как договорились.'},
            'claimed':{'ko': '다음에 큰 놈이 나오면 또 부르지.', 'en': "I'll call you when a big one shows up.",
                       'ja': 'でかいのが出たらまた呼ぶよ。', 'zh': '下次出大家伙了再叫你。',
                       'ru': 'Позову, когда объявится крупная добыча.'},
        },
    },

    # ── 사냥꾼의 펫 계약 (villager_hunter) — 20층 도달 후 ──────────────
    'pet_companion': {
        'giver': 'villager_hunter', 'unlock': {'floor': 20},
        'kind': 'kill_any', 'count': 20,
        'reward': {'gold': 500, 'stones': 3, 'pet': 'attack'},
        'text': {
            'name':  {'ko': '길들일 동반자', 'en': 'A Loyal Companion', 'ja': '相棒の契約',
                      'zh': '忠诚的伙伴', 'ru': 'Верный спутник'},
            'desc':  {'ko': '몬스터 20마리 처치 → 펫 해금', 'en': 'Slay 20 monsters → unlock a pet',
                      'ja': 'モンスター20体撃破 → ペット解禁', 'zh': '击杀20只怪物 → 解锁宠物',
                      'ru': 'Убейте 20 монстров → питомец'},
            'offer': {'ko': '20층까지 살아남았다니 대단해. 이 정도면 동반자 한 마리 맡겨도 되겠군. 몬스터 20마리만 잡아오면 길들인 정령을 붙여주지.',
                      'en': "Survived to floor 20? Impressive. You've earned a companion. Cull 20 monsters and I'll bond a tamed spirit to you.",
                      'ja': '20階まで生き延びたか、大したもんだ。相棒を一匹任せてもいい。モンスターを20体狩ってくれば、飼いならした精霊をつけてやる。',
                      'zh': '能活到20层，了不起。够格带个伙伴了。猎杀20只怪物，我就把驯服的精灵交给你。',
                      'ru': 'Дожил до 20 этажа? Впечатляет. Заслужил спутника. Убей 20 монстров — привяжу к тебе прирученного духа.'},
            'active':{'ko': '아무 몬스터나 좋아. 20마리를 채워오게.', 'en': 'Any monster counts — bring me 20 kills.',
                      'ja': 'どんなモンスターでもいい。20体分だ。', 'zh': '什么怪物都行，凑够20只。',
                      'ru': 'Любые монстры сойдут — набей 20.'},
            'done':  {'ko': '훌륭해! 자, 이 녀석이 이제 네 동반자다. B 키로 상태를 볼 수 있어.',
                      'en': "Well done! This one's your companion now. Press B to check its status.",
                      'ja': '見事だ! こいつが相棒だ。Bキーで状態を見られる。',
                      'zh': '干得好！它现在是你的伙伴了。按B查看状态。',
                      'ru': 'Отлично! Теперь он твой спутник. Нажми B для статуса.'},
            'claimed':{'ko': '녀석을 잘 키워보게. 강화석은 사냥 중에 나올 걸세.',
                       'en': "Raise it well. Upgrade stones drop as you hunt.",
                       'ja': 'よく育ててやれ。強化石は狩りの最中に出る。',
                       'zh': '好好养它。强化石会在狩猎中掉落。',
                       'ru': 'Расти его. Камни выпадают на охоте.'},
        },
    },

    # ── 학자 이졸데 (villager_scholar) — 8층에서 등장 ─────────────────
    'scholar_depths': {
        'giver': 'villager_scholar', 'unlock': {'floor': 8},
        'kind': 'reach_floor', 'floor': 20,
        'reward': {'gold': 700, 'stones': 4, 'items': ['large_health_potion', 'repair_kit']},
        'text': {
            'name':  {'ko': '심층의 비문 조사', 'en': 'Inscriptions of the Deep', 'ja': '深層の碑文調査',
                      'zh': '深层碑文调查', 'ru': 'Письмена глубин'},
            'desc':  {'ko': '지하 20층까지 탐험하기', 'en': 'Descend to floor 20', 'ja': '地下20階まで探索する',
                      'zh': '探索至地下20层', 'ru': 'Спуститесь на 20-й этаж'},
            'offer': {'ko': '지하 20층 벽에 고대 비문이 있다는 기록을 찾았습니다. 저는 도저히 그 깊이를 감당 못 해요. 대신 봐 주신다면 연구비를 통째로 드리죠.',
                      'en': "Records speak of ancient inscriptions on floor 20's walls. I could never survive that deep. Reach it for me and my entire research grant is yours.",
                      'ja': '地下20階の壁に古代の碑文があるという記録を見つけました。私にはとても無理な深さ。代わりに見てきてくだされば研究費を丸ごと差し上げます。',
                      'zh': '我找到记载，说地下20层的墙上有古代碑文。那深度我绝对撑不住。你替我去看，我把全部研究经费都给你。',
                      'ru': 'В записях сказано о древних письменах на стенах 20-го этажа. Мне туда не дойти. Дойди за меня — отдам весь исследовательский грант.'},
            'active':{'ko': '20층은 위험합니다. 부디 조심히… 비문의 형태를 꼭 기억해 주세요.', 'en': 'Floor 20 is perilous. Be careful… and remember the inscription\'s shape.',
                      'ja': '20階は危険です。どうか慎重に…碑文の形を覚えてきてください。', 'zh': '20层很危险。务必小心…请记住碑文的形状。',
                      'ru': '20-й этаж опасен. Осторожнее… и запомни форму письмён.'},
            'done':  {'ko': '드디어! 이 발견이면 학회가 뒤집힐 겁니다! 연구비 전부, 받아 마땅합니다!',
                      'en': 'At last! This discovery will shake the academy! Every coin of my grant — you\'ve earned it!',
                      'ja': 'ついに! この発見で学会がひっくり返ります! 研究費のすべて、受け取ってください!',
                      'zh': '终于！这一发现会震动学会！全部研究经费，你当之无愧！',
                      'ru': 'Наконец-то! Это открытие потрясёт академию! Весь грант — ты его заслужил!'},
            'claimed':{'ko': '당신은 학문의 은인입니다. 언제든 찾아오세요.', 'en': 'You are a patron of knowledge. Come by anytime.',
                       'ja': 'あなたは学問の恩人です。いつでもお越しを。', 'zh': '你是学问的恩人。随时欢迎再来。',
                       'ru': 'Ты — покровитель науки. Заходи в любое время.'},
        },
    },
}

# 시민 NPC 표시 이름
GIVER_NAMES = {
    'villager_boy':     {'ko': '꼬마 한스', 'en': 'Little Hans', 'ja': 'ちびハンス', 'zh': '小汉斯', 'ru': 'Малыш Ганс'},
    'villager_farmer':  {'ko': '농부 브람', 'en': 'Farmer Bram', 'ja': '農夫ブラム', 'zh': '农夫布拉姆', 'ru': 'Фермер Брам'},
    'villager_granny':  {'ko': '마르타 할멈', 'en': 'Granny Marta', 'ja': 'マルタばあさん', 'zh': '玛尔塔奶奶', 'ru': 'Бабушка Марта'},
    'villager_hunter':  {'ko': '사냥꾼 가로', 'en': 'Garo the Hunter', 'ja': '狩人ガロ', 'zh': '猎人加洛', 'ru': 'Охотник Гаро'},
    'villager_scholar': {'ko': '학자 이졸데', 'en': 'Scholar Isolde', 'ja': '学者イゾルデ', 'zh': '学者伊索尔德', 'ru': 'Учёная Изольда'},
}


# ── 잡담 대사 (퀘스트와 무관, 말 걸면 랜덤) ──────────────────────────────────
CHAT = {
    'villager_boy': [
        {'ko': '용사님 검은 진짜 반짝여요! 저도 만져봐도 돼요?',
         'en': "Your sword's so shiny! Can I touch it? Just once?",
         'ja': '勇者さまの剣ピカピカ! ぼくも触っていい?',
         'zh': '勇士的剑好闪！我能摸一下吗？就一下！',
         'ru': 'Твой меч блестит! Можно потрогать? Ну разок!'},
        {'ko': '아빠는 던전이 위험하대요. 근데 용사님은 안 무섭죠?',
         'en': 'Dad says the dungeon is scary. But you\'re not scared, right?',
         'ja': 'パパはダンジョンは危ないって。でも勇者さまは怖くないよね?',
         'zh': '爸爸说地城很危险。但勇士不怕对吧？',
         'ru': 'Папа говорит, подземелье страшное. Но ты ведь не боишься?'},
        {'ko': '나중에 저랑 같이 모험 가요! 약속!',
         'en': "Let's go adventuring together someday! Promise!",
         'ja': 'いつかぼくと一緒に冒険に行こう! 約束だよ!',
         'zh': '以后带我一起去冒险吧！拉钩！',
         'ru': 'Когда-нибудь пойдём в поход вместе! Обещаешь?'},
    ],
    'villager_farmer': [
        {'ko': '올해는 순무가 잘 됐어. 저녁에 국 끓여 먹게.',
         'en': "Turnips came in well this year. Good for a stew tonight.",
         'ja': '今年はカブがよく育った。夜は汁物じゃな。',
         'zh': '今年萝卜长得好。晚上炖汤喝。',
         'ru': 'Репа в этом году удалась. Вечером сварю похлёбку.'},
        {'ko': '던전만 잠잠하면 이 마을도 살 만하지.',
         'en': "As long as the dungeon stays quiet, this town's a fine place.",
         'ja': 'ダンジョンさえ静かなら、この村も住みやすいわい。',
         'zh': '只要地城安分，这村子还是挺宜居的。',
         'ru': 'Пока подземелье тихое — жить в деревне можно.'},
        {'ko': '허리가 예전 같지 않아. 젊음이 부럽구먼.',
         'en': "My back isn't what it was. I envy your youth.",
         'ja': '腰が昔のようにいかん。若さがうらやましいわい。',
         'zh': '腰不如从前了。真羡慕你年轻。',
         'ru': 'Спина уже не та. Завидую твоей молодости.'},
    ],
    'villager_granny': [
        {'ko': '따뜻할 때 차 한잔 하고 가려무나.',
         'en': "Have a cup of tea while it's warm, dear.",
         'ja': '温かいうちにお茶でも飲んでおいき。',
         'zh': '趁热喝杯茶再走吧。',
         'ru': 'Выпей чайку, пока горячий, милок.'},
        {'ko': '이 늙은이 눈에도 넌 참 좋은 아이야.',
         'en': "Even these old eyes can see you're a good soul.",
         'ja': 'この年寄りの目にも、あんたはいい子じゃよ。',
         'zh': '就算老眼昏花，也看得出你是好孩子。',
         'ru': 'Даже мои старые глаза видят: ты добрая душа.'},
        {'ko': '무리하지 말고, 꼭 살아 돌아오렴.',
         'en': "Don't overdo it — come back alive, always.",
         'ja': '無理はせんで、必ず生きて帰るんじゃよ。',
         'zh': '别逞强，一定要活着回来。',
         'ru': 'Не геройствуй попусту — возвращайся живым.'},
    ],
    'villager_hunter': [
        {'ko': '발소리를 죽이는 법을 알면 반은 이긴 거야.',
         'en': "Learn to silence your footsteps and you\'re half-won.",
         'ja': '足音を消す術を覚えれば、半分は勝ちだ。',
         'zh': '学会隐去脚步声，就赢了一半。',
         'ru': 'Научись ходить бесшумно — считай, полдела сделано.'},
        {'ko': '오라를 두른 놈은 무리에서 먼저 노려. 나머진 흩어지지.',
         'en': "Hit the aura-cloaked one first — the rest scatter.",
         'ja': 'オーラをまとった奴を先に狙え。残りは散る。',
         'zh': '先打带光环的，其余的就散了。',
         'ru': 'Бей того, что в ауре, — остальные разбегутся.'},
        {'ko': '내 활은 은퇴했지만 눈은 아직 살아있지.',
         'en': "My bow's retired, but my eyes are still sharp.",
         'ja': '俺の弓は引退したが、目はまだ生きてる。',
         'zh': '我的弓退役了，可眼力还在。',
         'ru': 'Лук мой на покое, а глаз ещё зоркий.'},
    ],
    'villager_scholar': [
        {'ko': '이 마을 지하엔 아직 해독 못 한 비문이 잔뜩입니다.',
         'en': "The depths below hold inscriptions I still can't read.",
         'ja': 'この村の地下には未解読の碑文が山ほどあります。',
         'zh': '这村子地下还有许多我读不懂的碑文。',
         'ru': 'В глубинах под нами — письмена, что мне не прочесть.'},
        {'ko': '지식은 검보다 느리지만, 더 멀리 갑니다.',
         'en': "Knowledge is slower than a blade, but travels farther.",
         'ja': '知識は剣より遅いが、より遠くまで届きます。',
         'zh': '知识比剑慢，却走得更远。',
         'ru': 'Знание медленнее клинка, но летит дальше.'},
        {'ko': '당신의 여정을 기록으로 남기고 싶군요. 언젠가.',
         'en': "I'd love to chronicle your journey. Someday.",
         'ja': 'あなたの旅を記録に残したい。いつか。',
         'zh': '真想把你的旅程记录下来。总有一天。',
         'ru': 'Хотел бы записать твой путь. Когда-нибудь.'},
    ],
}


def _resolve(table: dict) -> str:
    lang = get_lang()
    return table.get(lang) or table.get('en') or table.get('ko', '')


def random_chat(giver_id: str) -> str:
    """말 걸기 잡담 — 해당 시민의 대사 풀에서 랜덤 (현재 언어)."""
    import random
    lines = CHAT.get(giver_id)
    return _resolve(random.choice(lines)) if lines else ''


def qtext(qid: str, field: str) -> str:
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


def quest_target(qid: str) -> int:
    q = QUESTS[qid]
    return q['floor'] if q['kind'] == 'reach_floor' else q['count']


# ── 체인 / 개방 로직 ────────────────────────────────────────────────────────
def giver_chain(giver_id: str) -> list:
    """등장 순서대로 해당 시민의 퀘스트 id 목록."""
    return [qid for qid, q in QUESTS.items() if q['giver'] == giver_id]


def all_givers() -> list:
    seen = []
    for q in QUESTS.values():
        if q['giver'] not in seen:
            seen.append(q['giver'])
    return seen


def is_unlocked(qid: str, states: dict, max_floor: int) -> bool:
    """개방 조건(층/선행) 충족 여부."""
    u = QUESTS[qid].get('unlock')
    if not u:
        return True
    if 'floor' in u and max_floor < u['floor']:
        return False
    if 'after' in u and states.get(u['after'], {}).get('state') != 'claimed':
        return False
    return True


def unlock_hint(qid: str) -> str:
    """미개방 퀘스트 티저 조건 문자열."""
    u = QUESTS[qid].get('unlock') or {}
    if 'floor' in u:
        return f"B{u['floor']}F"
    if 'after' in u:
        return qtext(u['after'], 'name')
    return ''


def giver_current_quest(giver_id: str, states: dict, max_floor: int):
    """시민이 지금 제공할 퀘스트 id — 체인에서 아직 안 끝난 첫 퀘스트.

    None = 제공할 게 없음(전부 완료했거나, 다음 퀘가 아직 미개방)."""
    for qid in giver_chain(giver_id):
        st = states.get(qid, {}).get('state', 'available')
        if st == 'claimed':
            continue
        return qid if is_unlocked(qid, states, max_floor) else None
    return None


def giver_present(giver_id: str, states: dict, max_floor: int) -> bool:
    """시민이 마을에 등장했는가 — 첫 퀘스트가 개방되면 이후 상주."""
    for qid in giver_chain(giver_id):
        st = states.get(qid, {}).get('state', 'available')
        if st == 'claimed':
            return True
        return is_unlocked(qid, states, max_floor)
    return False
