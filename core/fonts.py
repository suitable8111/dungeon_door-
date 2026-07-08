"""언어별 UI 폰트 로더.

- ko / en / ru : 번들 픽셀 폰트(DungGeunMo — 한글·라틴·키릴 지원)
- ja / zh      : 시스템 CJK 폰트 폴백 (macOS: Hiragino, Windows: Yu Gothic/YaHei)

load_font(size)는 (언어, 크기)별로 캐시된다. 언어 변경 시 clear_cache() 호출.
"""
import os
import sys

import pygame

from core.lang import get_lang


def _assets_root():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


_BUNDLED_PIXEL = os.path.normpath(
    os.path.join(_assets_root(), 'assets', 'fonts', 'DungGeunMo.ttf'))

# 번들 픽셀 폰트가 커버하는 언어 (DungGeunMo: 한글 + 라틴 + 키릴)
_PIXEL_LANGS = frozenset(('ko', 'en', 'ru'))

# 언어별 시스템 폰트 후보: (파일 경로 목록, SysFont 이름 목록)
_LANG_FONTS: dict[str, tuple[list[str], list[str]]] = {
    'ko': (
        ['/System/Library/Fonts/AppleSDGothicNeo.ttc',
         '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
         'C:/Windows/Fonts/malgun.ttf',
         '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'],
        ['applesdgothicneo', 'applegothic', 'malgungothic', 'nanumgothic'],
    ),
    'ja': (
        ['/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
         '/System/Library/Fonts/Hiragino Sans GB.ttc',
         'C:/Windows/Fonts/YuGothM.ttc',
         'C:/Windows/Fonts/meiryo.ttc',
         'C:/Windows/Fonts/msgothic.ttc',
         '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'],
        ['hiraginosansgb', 'yugothicmedium', 'yugothic', 'meiryo',
         'msgothic', 'notosanscjkjp'],
    ),
    'zh': (
        ['/System/Library/Fonts/Hiragino Sans GB.ttc',
         '/System/Library/Fonts/Supplemental/Songti.ttc',
         'C:/Windows/Fonts/msyh.ttc',
         'C:/Windows/Fonts/msyh.ttf',
         'C:/Windows/Fonts/simhei.ttf',
         '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'],
        ['microsoftyahei', 'simhei', 'hiraginosansgb', 'notosanscjksc'],
    ),
}
_LANG_FONTS['en'] = _LANG_FONTS['ko']
_LANG_FONTS['ru'] = _LANG_FONTS['ko']

_cache: dict[tuple, pygame.font.Font] = {}


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """현재 언어에 맞는 UI 폰트 반환 (언어·크기별 캐시)."""
    lang = get_lang()
    key = (lang, size, bold)
    f = _cache.get(key)
    if f is not None:
        return f
    f = _build(lang, size, bold)
    _cache[key] = f
    return f


def _build(lang: str, size: int, bold: bool) -> pygame.font.Font:
    # 1) 픽셀 폰트 지원 언어 → 번들 폰트 우선 (기존 룩 유지)
    if lang in _PIXEL_LANGS and os.path.exists(_BUNDLED_PIXEL):
        try:
            return pygame.font.Font(_BUNDLED_PIXEL, size)
        except Exception:
            pass
    # 2) 시스템 폰트 경로 순회
    paths, sys_names = _LANG_FONTS.get(lang, _LANG_FONTS['ko'])
    for path in paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    # 3) SysFont 이름 매칭 (pygame이 시스템 폰트 스캔)
    for name in sys_names:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.SysFont('sans-serif', size, bold=bold)


def clear_cache():
    """언어 변경 후 호출 — 다음 load_font부터 새 언어 폰트 생성."""
    _cache.clear()
