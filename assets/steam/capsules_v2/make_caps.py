#!/usr/bin/env python3
"""capsules_v2: Gemini WIDE 키아트(1376x768)에서 Steam 캡슐 규격을 커버-크롭으로 생성.
로고가 상단에 박혀 있어 세로 크롭 시 로고가 살아남도록 vy(수직 앵커)를 조절한다.
  vy=0.0 → 위쪽 우선(로고 보존), 0.5 → 중앙(영웅/폭발 중심).
사용: python3 make_caps.py [메인소스파일명]  (기본 keyart_main_ultimate.png)
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'src', sys.argv[1] if len(sys.argv) > 1 else 'keyart_main_ultimate.png')

# (파일명, 폭, 높이, 수직앵커)  — Steam 현행 요구 규격(레티나 2배). 앵커는 로고 보존/영웅 강조 균형
TARGETS = [
    ('main_capsule.png',    1232, 706, 0.50),  # 1.745:1 ≈ 소스, 거의 안 잘림
    ('header_capsule.png',   920, 430, 0.32),  # 스토어 상단·위시리스트·라이브러리 격자
    ('small_capsule.png',    462, 174, 0.10),  # 검색 목록 — 로고 최대 보존(위쪽)
    ('page_background.png', 1438, 810, 0.50),  # 상점 페이지 배경(소스 대비 소폭 업스케일)
    # 수직 캡슐(748x896, 세로)은 WIDE 크롭 시 상단 로고가 잘려 제외 — 기존 자산 유지.
    # 필요하면 Gemini에서 PORTRAIT(768x1376) 키아트를 별도 생성해 뽑을 것.
]


def cover_crop(img, tw, th, vy):
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = round(sw * scale), round(sh * scale)
    im = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = round((nh - th) * vy)
    y = max(0, min(nh - th, y))
    return im.crop((x, y, x + tw, y + th))


def main():
    src = Image.open(SRC).convert('RGB')
    print(f"src: {SRC}  {src.size}")
    for name, tw, th, vy in TARGETS:
        out = cover_crop(src, tw, th, vy)
        p = os.path.join(HERE, name)
        out.save(p, 'PNG')
        print(f"  {name:22s} {tw}x{th}")
    print("done ->", HERE)


if __name__ == '__main__':
    main()
