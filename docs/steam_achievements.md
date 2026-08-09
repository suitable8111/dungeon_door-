# Steamworks 도전과제 등록 치트시트 (App 4718470)

파트너 사이트: **Edit Steamworks Settings → 통계 및 도전 과제 → 도전 과제 설정**
아이콘 폴더: `assets/steam/achievements/`  ·  달성=`<API>.png` / 미달성=`<API>_locked.png`

## 각 행 입력 순서
1. **새로운 도전 과제** 클릭
2. **API 이름** 붙여넣기
3. **이름/설명** 칸(작은 버튼) 클릭 → **표시 이름** + **설명** 붙여넣기
4. **진행률 통계 = 없음** · **설정자 = 클라이언트** · **비공개 = 끄기** (기본값 그대로)
5. **달성 아이콘**: 파일 선택 → `<API>.png` → 업로드
6. **미달성 아이콘**: 파일 선택 → `<API>_locked.png` → 업로드
7. 다음 행 반복 → 전부 끝나면 상단 **게시(Publish)**

> 스팀 Stat은 만들 필요 없음(게임이 로컬에서 세고 SetAchievement만 호출).

---

## 협동 신규 8

| # | API 이름 | 표시 이름 (EN) | 설명 (EN) |
|--|--|--|--|
| 1 | `ACH_COOP_KILLS_100` | Hundred Together | Defeat 100 monsters in co-op. |
| 2 | `ACH_REVIVE` | Brother in Arms | Revive a fallen ally for the first time. |
| 3 | `ACH_REVIVE_10` | Leave No One Behind | Revive fallen allies 10 times. |
| 4 | `ACH_COOP_1H` | An Hour Together | Play 1 hour in co-op. |
| 5 | `ACH_COOP_3H` | Steadfast Duo | Play 3 hours in co-op. |
| 6 | `ACH_COOP_5H` | Party Forever | Play 5 hours in co-op. |
| 7 | `ACH_COOP_QUEST` | Guild's Trust | Complete your first Mercenary Board contract. |
| 8 | `ACH_COOP_BOSS` | Giant Slayers | Defeat a boss while in co-op. |

## 기존 16

| # | API 이름 | 표시 이름 (EN) | 설명 (EN) |
|--|--|--|--|
| 9 | `ACH_FIRST_BLOOD` | First Blood | Defeat your first monster. |
| 10 | `ACH_KILLS_500` | Slaughterer | Defeat 500 monsters. |
| 11 | `ACH_ELITE_25` | Variant Hunter | Defeat 25 elite variants. |
| 12 | `ACH_BOSS_10` | Nightmare of Bosses | Defeat 10 bosses. |
| 13 | `ACH_FLOOR_5` | First Gate | Reach dungeon floor 5. |
| 14 | `ACH_FLOOR_10` | Depth 10 | Reach dungeon floor 10. |
| 15 | `ACH_FLOOR_25` | Into the Abyss | Reach dungeon floor 25. |
| 16 | `ACH_FLOOR_50` | Prison Break | Reach dungeon floor 50. |
| 17 | `ACH_FIRST_BOSS` | Giant Slayer | Defeat your first boss. |
| 18 | `ACH_COMBO_15` | Unstoppable Blade | Reach a 15-hit combo. |
| 19 | `ACH_LEVEL_20` | Veteran | Reach character level 20. |
| 20 | `ACH_ENHANCE_10` | Soul of the Smith | Enhance gear to +10. |
| 21 | `ACH_RICH` | Dungeon Tycoon | Hold 2000 gold at once. |
| 22 | `ACH_BURNING` | Through the Flames | Survive the Burning stage. |
| 23 | `ACH_ULTIMATE` | Ultimate Unleashed | Unleash an ultimate skill. |
| 24 | `ACH_DIE` | Dungeon Baptism | Fall in the dungeon for the first time. |

## 신규 14 — 레벨 심화 / 심층 / 생활 (v2.11 추가)

| # | API 이름 | 표시 이름 (EN) | 설명 (EN) |
|--|--|--|--|
| 25 | `ACH_LEVEL_40` | Seasoned | Reach character level 40. |
| 26 | `ACH_LEVEL_60` | Elite | Reach character level 60. |
| 27 | `ACH_LEVEL_80` | Champion | Reach character level 80. |
| 28 | `ACH_LEVEL_99` | Pinnacle | Reach max level 99. |
| 29 | `ACH_FLOOR_100` | Centurion Depth | Reach dungeon floor 100. |
| 30 | `ACH_FLOOR_250` | Deep Delver | Reach dungeon floor 250. |
| 31 | `ACH_FLOOR_500` | Halfway Down | Reach dungeon floor 500. |
| 32 | `ACH_FLOOR_999` | The Bottom | Reach dungeon floor 999. |
| 33 | `ACH_FARM_FIRST` | First Harvest | Harvest your first crop. |
| 34 | `ACH_FARM_100` | Green Thumb | Harvest 100 crops. |
| 35 | `ACH_FISH_FIRST` | First Catch | Catch your first fish. |
| 36 | `ACH_FISH_50` | Master Angler | Catch 50 fish. |
| 37 | `ACH_RANCH_FIRST` | Ranch Hand | Collect your first ranch product. |
| 38 | `ACH_LIFE_MASTER` | Homesteader | Farm, fish, and ranch at least once each. |

---

## 현지화 이름 (선택 — `core/lang.py`의 `ach_*` 키와 동일)

각 도전과제의 **이름** 다국어. 설명은 EN만으로도 충분(원하면 요청).

| API | KO | JA | ZH | RU |
|--|--|--|--|--|
| ACH_COOP_KILLS_100 | 함께라면 백 마리 | 共に百体 | 同心百杀 | Сотня на двоих |
| ACH_REVIVE | 전우를 일으키다 | 戦友を起こす | 扶起战友 | Поднять товарища |
| ACH_REVIVE_10 | 결코 두고 가지 않아 | 誰も置き去りにしない | 绝不落下一人 | Своих не бросаем |
| ACH_COOP_1H | 함께한 한 시간 | 共に一時間 | 同行一小时 | Час вместе |
| ACH_COOP_3H | 단짝 용병 | 相棒の傭兵 | 默契搭档 | Верный дуэт |
| ACH_COOP_5H | 영원한 파티 | 永遠のパーティ | 永恒队伍 | Команда навек |
| ACH_COOP_QUEST | 길드의 신뢰 | ギルドの信頼 | 公会的信任 | Доверие гильдии |
| ACH_COOP_BOSS | 둘이서 거인 사냥 | 二人で巨人狩り | 双人屠巨 | Убийцы гигантов вдвоём |
| ACH_FIRST_BLOOD | 첫 사냥감 | 最初の獲物 | 第一滴血 | Первая кровь |
| ACH_KILLS_500 | 학살자 | 殺戮者 | 屠杀者 | Истребитель |
| ACH_ELITE_25 | 변종 사냥꾼 | 変種ハンター | 精英猎人 | Охотник на элиту |
| ACH_BOSS_10 | 보스의 악몽 | ボスの悪夢 | 首领的噩梦 | Кошмар боссов |
| ACH_FLOOR_5 | 첫 관문 | 最初の関門 | 第一道门 | Первые врата |
| ACH_FLOOR_10 | 지하 10층 | 地下10階 | 地下10层 | Глубина 10 |
| ACH_FLOOR_25 | 심연을 향해 | 深淵へ | 迈向深渊 | В бездну |
| ACH_FLOOR_50 | 감옥 탈출 | 監獄脱出 | 越狱 | Побег из тюрьмы |
| ACH_FIRST_BOSS | 거인 사냥 | 巨人狩り | 巨人猎手 | Убийца гигантов |
| ACH_COMBO_15 | 멈추지 않는 칼날 | 止まらぬ刃 | 不停之刃 | Неудержимый клинок |
| ACH_LEVEL_20 | 베테랑 | ベテラン | 老兵 | Ветеран |
| ACH_ENHANCE_10 | 대장장이의 혼 | 鍛冶屋の魂 | 铁匠之魂 | Душа кузнеца |
| ACH_RICH | 던전의 부자 | ダンジョンの富豪 | 地城富豪 | Магнат подземелья |
| ACH_BURNING | 불길에서 살아남다 | 炎を生き延びて | 浴火重生 | Сквозь пламя |
| ACH_ULTIMATE | 오의 개방 | 奥義開放 | 奥义解放 | Тайна раскрыта |
| ACH_DIE | 던전의 세례 | ダンジョンの洗礼 | 地城洗礼 | Крещение подземельем |
