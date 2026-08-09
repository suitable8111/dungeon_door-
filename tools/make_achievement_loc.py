"""Steam 도전과제 현지화 VDF 생성기.

Steamworks 도전과제는 '현지화 토큰'(NEW_ACHIEVEMENT_1_N_NAME/DESC)에 번역을
매핑하는 방식이다. 이 스크립트는:
  1) 파트너 사이트에서 읽어온 토큰↔API 매핑(TOKENS)
  2) docs/steam_achievements_localized.md 의 KO/JA/ZH/RU 번역표
를 결합해 언어별 VDF 파일을 assets/steam/loc/ 에 생성한다.

업로드: Steamworks → 앱 → 현지화(Localization) 파일 업로드에 언어별로 올린다.

사용: python3 tools/make_achievement_loc.py
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(BASE, "docs", "steam_achievements_localized.md")
OUT = os.path.join(BASE, "assets", "steam", "loc")
os.makedirs(OUT, exist_ok=True)

# ── 토큰↔API 매핑 (파트너 사이트 '현지화 토큰' 뷰에서 확인) ─────────────
TOKENS = {
    "ACH_COOP_KILLS_100": "NEW_ACHIEVEMENT_1_0",
    "ACH_REVIVE":         "NEW_ACHIEVEMENT_1_1",
    "ACH_REVIVE_10":      "NEW_ACHIEVEMENT_1_2",
    "ACH_COOP_1H":        "NEW_ACHIEVEMENT_1_3",
    "ACH_COOP_3H":        "NEW_ACHIEVEMENT_1_4",
    "ACH_COOP_5H":        "NEW_ACHIEVEMENT_1_5",
    "ACH_COOP_QUEST":     "NEW_ACHIEVEMENT_1_6",
    "ACH_COOP_BOSS":      "NEW_ACHIEVEMENT_1_7",
    "ACH_FIRST_BLOOD":    "NEW_ACHIEVEMENT_1_8",
    "ACH_KILLS_500":      "NEW_ACHIEVEMENT_1_9",
    "ACH_ELITE_25":       "NEW_ACHIEVEMENT_1_10",
    "ACH_BOSS_10":        "NEW_ACHIEVEMENT_1_11",
    "ACH_FLOOR_5":        "NEW_ACHIEVEMENT_1_12",
    "ACH_FLOOR_10":       "NEW_ACHIEVEMENT_1_13",
    "ACH_FLOOR_25":       "NEW_ACHIEVEMENT_1_14",
    "ACH_FLOOR_50":       "NEW_ACHIEVEMENT_1_15",
    "ACH_FIRST_BOSS":     "NEW_ACHIEVEMENT_1_16",
    "ACH_COMBO_15":       "NEW_ACHIEVEMENT_1_17",
    "ACH_LEVEL_20":       "NEW_ACHIEVEMENT_1_18",
    "ACH_ENHANCE_10":     "NEW_ACHIEVEMENT_1_19",
    "ACH_RICH":           "NEW_ACHIEVEMENT_1_20",
    "ACH_BURNING":        "NEW_ACHIEVEMENT_1_21",
    "ACH_ULTIMATE":       "NEW_ACHIEVEMENT_1_22",
    "ACH_DIE":            "NEW_ACHIEVEMENT_1_23",
    "ACH_LEVEL_40":       "NEW_ACHIEVEMENT_1_24",
    "ACH_LEVEL_60":       "NEW_ACHIEVEMENT_1_25",
    "ACH_LEVEL_80":       "NEW_ACHIEVEMENT_1_26",
    "ACH_LEVEL_99":       "NEW_ACHIEVEMENT_1_27",
    "ACH_FLOOR_100":      "NEW_ACHIEVEMENT_1_28",
    "ACH_FLOOR_250":      "NEW_ACHIEVEMENT_1_29",
    "ACH_FLOOR_500":      "NEW_ACHIEVEMENT_1_30",
    "ACH_FLOOR_999":      "NEW_ACHIEVEMENT_1_31",
    "ACH_FARM_FIRST":     "NEW_ACHIEVEMENT_2_0",
    "ACH_FARM_100":       "NEW_ACHIEVEMENT_2_1",
    "ACH_FISH_FIRST":     "NEW_ACHIEVEMENT_2_2",
    "ACH_FISH_50":        "NEW_ACHIEVEMENT_2_3",
    "ACH_RANCH_FIRST":    "NEW_ACHIEVEMENT_2_4",
    "ACH_LIFE_MASTER":    "NEW_ACHIEVEMENT_2_5",
}

# 문서 섹션 헤더 → Steam 언어 코드
SECTIONS = {
    "한국어": "koreana",
    "日本語": "japanese",
    "简体中文": "schinese",
    "Русский": "russian",
}


def parse_doc():
    """localized.md 를 {lang_code: {API: (name, desc)}} 로 파싱."""
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    data = {}
    cur = None
    for line in text.splitlines():
        h = line.strip()
        if h.startswith("## "):
            cur = None
            for key, code in SECTIONS.items():
                if key in h:
                    cur = code
                    data[cur] = {}
                    break
            continue
        if cur and line.strip().startswith("| ACH_"):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 3:
                api, name, desc = cols[0], cols[1], cols[2]
                data[cur][api] = (name, desc)
    return data


def vdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def write_vdf(code: str, entries: dict):
    """entries: {API: (name, desc)} → 언어별 VDF."""
    lines = ['"lang"', "{", f'\t"Language"\t"{code}"', '\t"Tokens"', "\t{"]
    for api, tok in TOKENS.items():
        if api not in entries:
            print(f"  ! [{code}] 번역 누락: {api}")
            continue
        name, desc = entries[api]
        lines.append(f'\t\t"{tok}_NAME"\t"{vdf_escape(name)}"')
        lines.append(f'\t\t"{tok}_DESC"\t"{vdf_escape(desc)}"')
    lines += ["\t}", "}", ""]
    path = os.path.join(OUT, f"achievements_{code}.vdf")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def run():
    data = parse_doc()
    for key, code in SECTIONS.items():
        entries = data.get(code, {})
        path = write_vdf(code, entries)
        print(f"OK {code}: {len(entries)} achievements → {os.path.relpath(path, BASE)}")


if __name__ == "__main__":
    run()
