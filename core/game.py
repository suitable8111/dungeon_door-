import os
import random
import sys
import pygame

from core.constants import *
from core.camera import Camera
from core.input_handler import InputHandler
from core.animator import (Animator, LungeAnim, SlashAnim, HitFlashAnim, BoltAnim,
                            AttackSwingAnim, DashTrailAnim, WhirlAnim, HealAnim)
from core.audio import AudioManager
from core.skills import SkillManager, SKILL_DEFS, COMBO_SKILL_DEFS, SKILL_UPGRADES, SKILL_MAX_LEVEL, SKILL_XP_REQ
from core.save_load import (save_game, load_game, has_save, delete_save,
                             load_settings, save_settings,
                             load_records, update_records)
from core.lang import t, set_lang
from map.generator import generate_dungeon
from map.tile import Tile, TileType
from entities.player import Player
from ui.hud import HUD
from data_loader import load_enemies, load_items

# ─────────────────────────────────────────────────────────────────────────────
# 색상 상수
# ─────────────────────────────────────────────────────────────────────────────
_GOLD   = (235, 185,  60); _GOLD_D = (150, 108, 18); _GOLD_L = (255, 222, 105)
_SIL    = (178, 183, 202); _SIL_D  = (118, 123, 148)
_BLUE   = ( 62, 103, 162); _BLUE_D = ( 38,  66, 115)
_BELT   = ( 95,  60,  20); _BOOT   = ( 88,  55,  25)
_BLACK  = (  0,   0,   0); _RED    = (200,  48,  48)
_PLUME  = (230,  80,  80)
_CKEY   = (  1,   2,   3)


def _r(s, c, x, y, w, h): pygame.draw.rect(s, c, (x, y, w, h))
def _p(s, c, pts):         pygame.draw.polygon(s, c, pts)

# ─────────────────────────────────────────────────────────────────────────────
# 플레이어 스프라이트
# ─────────────────────────────────────────────────────────────────────────────
def _helm(s, x, y):
    _r(s,_GOLD,  x+10,y+2,12,10); _r(s,_GOLD_L,x+10,y+2,12,2)
    _r(s,_GOLD_D,x+10,y+4,12, 8)
    _r(s,_GOLD_D,x+ 8,y+5, 2, 6); _r(s,_GOLD_D,x+22,y+5,2,6)
    _r(s,_BLACK, x+11,y+6,10, 3); _r(s,_GOLD_D,x+11,y+6,10,1)
    _r(s,_RED,   x+15,y+0, 2, 3); _r(s,_PLUME, x+14,y+1,4,2)

def _helm_back(s, x, y):
    _r(s,_GOLD,  x+10,y+2,12,10); _r(s,_GOLD_L,x+10,y+2,12,2)
    _r(s,_GOLD_D,x+10,y+4,12, 8)
    _r(s,_GOLD_D,x+ 8,y+5, 2, 6); _r(s,_GOLD_D,x+22,y+5,2,6)
    _r(s,_RED,   x+15,y+0, 2, 3); _r(s,_PLUME, x+14,y+1,4,2)

def _body(s, x, y):
    _r(s,_GOLD,  x+ 5,y+11,8,5); _r(s,_GOLD_L,x+ 5,y+11,8,1)
    _r(s,_GOLD,  x+19,y+11,8,5); _r(s,_GOLD_L,x+19,y+11,8,1)
    _r(s,_BLUE,  x+ 9,y+11,14,14)
    _r(s,_BLUE_D,x+10,y+12,12,12)
    _r(s,_SIL,   x+14,y+13, 4, 9); _r(s,_SIL_D,x+15,y+13,2,9)
    _r(s,_BELT,  x+ 9,y+25,14, 3); _r(s,_GOLD, x+14,y+25,4,3)
    _r(s,_GOLD_L,x+15,y+25, 2, 1)

def _legs_front(s, x, y, frame):
    Loff = 0 if frame == 0 else 2; Roff = 2 if frame == 0 else 0
    _r(s,_BLUE, x+10,y+28-Loff,5,3); _r(s,_BOOT,x+ 9,y+29-Loff,6,2); _r(s,_BLACK,x+ 9,y+31-Loff,6,1)
    _r(s,_BLUE, x+17,y+28-Roff,5,3); _r(s,_BOOT,x+17,y+29-Roff,6,2); _r(s,_BLACK,x+17,y+31-Roff,6,1)

def _player_down(s, x, y, frame):
    _r(s,_SIL,  x+24,y+10,3,14); _r(s,_SIL_D,x+24,y+10,1,14)
    _r(s,_GOLD_D,x+21,y+18,8,2); _r(s,_GOLD, x+24,y+20,3,5)
    _p(s,_BLUE_D,[(x+5,y+13),(x+9,y+13),(x+9,y+23),(x+7,y+27),(x+5,y+23)])
    _r(s,_SIL,  x+5,y+13,1,10)
    _body(s,x,y); _legs_front(s,x,y,frame); _helm(s,x,y)

def _player_up(s, x, y, frame):
    _r(s,_SIL,  x+7, y+11,3,14); _r(s,_SIL_D,x+8,y+11,1,14)
    _r(s,_GOLD_D,x+5,y+18,8,2);  _r(s,_GOLD, x+7,y+20,3,5)
    _p(s,_BLUE_D,[(x+23,y+13),(x+27,y+13),(x+27,y+23),(x+25,y+27),(x+23,y+23)])
    _r(s,_SIL,  x+27,y+13,1,10)
    _body(s,x,y); _r(s,_SIL,x+14,y+13,4,9); _r(s,_SIL_D,x+15,y+13,2,9)
    _legs_front(s,x,y,frame); _helm_back(s,x,y)

def _player_left_raw(s, x, y, frame):
    fl_x,bl_x = (x+9,x+16) if frame==0 else (x+16,x+9)
    fl_y,bl_y = y+29, y+27
    _r(s,_BLUE_D,bl_x,bl_y-3,4,3); _r(s,_BOOT,bl_x-1,bl_y,5,2); _r(s,_BLACK,bl_x-1,bl_y+2,5,1)
    _p(s,_BLUE_D,[(x+19,y+14),(x+23,y+14),(x+23,y+23),(x+21,y+26),(x+19,y+23)])
    _r(s,_SIL,x+22,y+14,1,9)
    _r(s,_GOLD_D,x+17,y+11,5,4); _r(s,_GOLD,x+9,y+11,7,5); _r(s,_GOLD_L,x+9,y+11,7,1)
    _r(s,_BLUE,x+10,y+11,12,14); _r(s,_BLUE_D,x+11,y+12,10,12)
    _r(s,_SIL,x+14,y+13,3,9); _r(s,_BELT,x+10,y+25,12,3); _r(s,_GOLD,x+14,y+25,4,3)
    _r(s,_GOLD,x+5,y+14,6,5); _r(s,_GOLD,x+4,y+19,5,7)
    _r(s,_SIL,x+1,y+20,9,2); _r(s,_SIL_D,x+1,y+20,9,1)
    _r(s,_GOLD_D,x+7,y+18,3,6); _r(s,_GOLD,x+8,y+19,5,4); _r(s,_GOLD_L,x+9,y+19,2,1)
    _r(s,_BLUE,fl_x,fl_y-3,5,3); _r(s,_BOOT,fl_x-1,fl_y,7,2); _r(s,_BLACK,fl_x-1,fl_y+2,7,1)
    _r(s,_GOLD,x+8,y+2,16,10); _r(s,_GOLD_L,x+8,y+2,16,2); _r(s,_GOLD_D,x+8,y+4,16,8)
    _r(s,_GOLD_D,x+7,y+5,3,6); _r(s,_BLACK,x+7,y+7,2,3); _r(s,_GOLD,x+21,y+3,5,8)
    _r(s,_GOLD_D,x+8,y+10,5,2); _r(s,_RED,x+14,y+0,2,3); _r(s,_PLUME,x+13,y+1,4,2)

def draw_player(surf, x, y, facing='down', walk_frame=0):
    ts = TILE_SIZE
    if facing in ('left', 'right'):
        tmp = pygame.Surface((ts, ts)); tmp.fill(_CKEY); tmp.set_colorkey(_CKEY)
        _player_left_raw(tmp, 0, 0, walk_frame)
        if facing == 'right':
            tmp = pygame.transform.flip(tmp, True, False); tmp.set_colorkey(_CKEY)
        surf.blit(tmp, (x, y))
    elif facing == 'up':
        _player_up(surf, x, y, walk_frame)
    else:
        _player_down(surf, x, y, walk_frame)

def draw_hp_bar(s, x, y, hp, max_hp):
    bw = TILE_SIZE - 4; ratio = max(0.0, hp / max_hp)
    _r(s,(70,20,20),x+2,y+2,bw,4)
    if ratio > 0:
        _r(s,(200+int(55*(1-ratio)),int(210*ratio),40),x+2,y+2,max(1,int(bw*ratio)),4)

# ─────────────────────────────────────────────────────────────────────────────
# 적 스프라이트
# ─────────────────────────────────────────────────────────────────────────────
def draw_rat(s,x,y,col):
    R,G,B=col; D=(max(0,R-55),max(0,G-55),max(0,B-40))
    PINK=(220,150,145); BLK=(0,0,0); RED=(210,50,50)
    pygame.draw.arc(s,D,(x+1,y+20,12,8),0.3,2.8,2)
    pygame.draw.ellipse(s,col,(x+5,y+15,22,13)); pygame.draw.ellipse(s,D,(x+5,y+22,22,6))
    pygame.draw.ellipse(s,col,(x+17,y+10,13,12)); pygame.draw.ellipse(s,D,(x+25,y+15,7,5))
    pygame.draw.circle(s,PINK,(x+30,y+18),2)
    pygame.draw.ellipse(s,D,(x+14,y+6,6,8)); pygame.draw.ellipse(s,PINK,(x+15,y+7,4,6))
    pygame.draw.ellipse(s,D,(x+20,y+5,6,8)); pygame.draw.ellipse(s,PINK,(x+21,y+6,4,6))
    pygame.draw.circle(s,BLK,(x+26,y+14),2); pygame.draw.circle(s,RED,(x+26,y+14),1)
    _r(s,D,x+7,y+25,4,4); _r(s,D,x+13,y+25,4,4)

def draw_goblin(s,x,y,col):
    R,G,B=col; D=(max(0,R-50),max(0,G-60),max(0,B-35)); L=(min(255,R+45),min(255,G+45),min(255,B+20))
    YEL=(230,210,30); BLK=(0,0,0); TOOTH=(225,215,200)
    _r(s,col,x+10,y+19,12,10); _r(s,D,x+10,y+19,2,10)
    _r(s,col,x+6,y+19,5,9); _r(s,col,x+21,y+19,5,9)
    pygame.draw.ellipse(s,D,(x+5,y+26,6,5)); pygame.draw.ellipse(s,D,(x+21,y+26,6,5))
    _r(s,D,x+11,y+29,4,3); _r(s,D,x+17,y+29,4,3); _r(s,D,x+10,y+30,5,2); _r(s,D,x+17,y+30,5,2)
    _r(s,col,x+7,y+5,18,15); _r(s,L,x+7,y+5,18,3)
    _p(s,col,[(x+5,y+7),(x+5,y+16),(x+9,y+12)]); _p(s,L,[(x+5,y+7),(x+6,y+8),(x+7,y+12)])
    _p(s,col,[(x+27,y+7),(x+27,y+16),(x+23,y+12)])
    _r(s,YEL,x+10,y+11,4,4); _r(s,YEL,x+18,y+11,4,4)
    _r(s,BLK,x+11,y+12,2,2); _r(s,BLK,x+19,y+12,2,2)
    _r(s,D,x+14,y+15,4,2); _r(s,BLK,x+15,y+15,1,1); _r(s,BLK,x+17,y+15,1,1)
    _r(s,BLK,x+11,y+17,10,2); _r(s,TOOTH,x+12,y+17,2,1); _r(s,TOOTH,x+18,y+17,2,1)

def draw_skeleton(s,x,y,col):
    R,G,B=col; D=(max(0,R-80),max(0,G-80),max(0,B-70)); BLK=(0,0,0); DK=(30,30,30)
    _r(s,col,x+10,y+15,12,2)
    for i in range(3):
        ry=y+18+i*4; _r(s,col,x+10,ry,12,2); _r(s,D,x+10,ry,2,2); _r(s,D,x+20,ry,2,2)
    for i in range(8): _r(s,D,x+15,y+14+i*2,2,1)
    _r(s,col,x+6,y+16,4,10); _r(s,col,x+22,y+16,4,10)
    pygame.draw.circle(s,D,(x+8,y+21),2); pygame.draw.circle(s,D,(x+24,y+21),2)
    _r(s,col,x+5,y+26,5,3); _r(s,col,x+22,y+26,5,3)
    _r(s,D,x+11,y+29,4,3); _r(s,D,x+17,y+29,4,3); _r(s,D,x+10,y+30,5,2); _r(s,D,x+17,y+30,5,2)
    pygame.draw.ellipse(s,col,(x+8,y+3,16,14)); pygame.draw.ellipse(s,D,(x+8,y+10,16,7))
    _r(s,BLK,x+10,y+7,4,4); _r(s,BLK,x+18,y+7,4,4); _r(s,DK,x+11,y+8,2,2); _r(s,DK,x+19,y+8,2,2)
    _r(s,BLK,x+15,y+12,2,2)
    for i in range(4): _r(s,col,x+10+i*3,y+15,2,3)
    _r(s,BLK,x+10,y+15,12,1)

def draw_orc(s,x,y,col):
    R,G,B=col; D=(max(0,R-50),max(0,G-55),max(0,B-35)); L=(min(255,R+35),min(255,G+35),min(255,B+15))
    RED=(215,55,55); BLK=(0,0,0); MTL=(135,135,155); TSK=(235,220,180)
    _r(s,col,x+8,y+14,16,14); _r(s,L,x+8,y+14,16,2); _r(s,D,x+8,y+22,16,6)
    _r(s,L,x+10,y+16,3,7); _r(s,L,x+19,y+16,3,7)
    pygame.draw.ellipse(s,D,(x+2,y+12,10,8)); pygame.draw.ellipse(s,D,(x+20,y+12,10,8))
    pygame.draw.ellipse(s,col,(x+3,y+12,8,6)); pygame.draw.ellipse(s,col,(x+21,y+12,8,6))
    _r(s,col,x+4,y+17,5,10); _r(s,col,x+23,y+17,5,10)
    pygame.draw.ellipse(s,D,(x+3,y+25,7,6)); pygame.draw.ellipse(s,D,(x+22,y+25,7,6))
    _r(s,MTL,x+26,y+14,3,14); _p(s,MTL,[(x+26,y+14),(x+31,y+10),(x+31,y+20),(x+26,y+20)])
    _r(s,(90,60,25),x+27,y+21,2,6)
    _r(s,D,x+10,y+28,6,4); _r(s,D,x+16,y+28,6,4); _r(s,D,x+9,y+30,7,2); _r(s,D,x+16,y+30,7,2)
    pygame.draw.ellipse(s,col,(x+7,y+3,18,14)); pygame.draw.ellipse(s,L,(x+7,y+3,18,4))
    pygame.draw.ellipse(s,D,(x+7,y+11,18,6))
    _r(s,RED,x+10,y+8,4,4); _r(s,RED,x+18,y+8,4,4); _r(s,BLK,x+11,y+9,2,2); _r(s,BLK,x+19,y+9,2,2)
    _p(s,TSK,[(x+12,y+15),(x+14,y+8),(x+15,y+15)]); _p(s,TSK,[(x+18,y+15),(x+19,y+8),(x+21,y+15)])
    _r(s,D,x+14,y+12,4,3); _r(s,BLK,x+15,y+12,1,2); _r(s,BLK,x+17,y+12,1,2)

def draw_troll(s,x,y,col):
    R,G,B=col; D=(max(0,R-45),max(0,G-50),max(0,B-35)); L=(min(255,R+30),min(255,G+30),min(255,B+15))
    BLK=(0,0,0); YEL=(215,195,30); WD=(110,75,30); WDD=(75,50,18)
    _r(s,WD,x+24,y+8,4,16); _r(s,WDD,x+25,y+8,1,16)
    pygame.draw.ellipse(s,WD,(x+22,y+4,8,8)); pygame.draw.ellipse(s,WDD,(x+23,y+5,5,5))
    _r(s,col,x+5,y+14,20,16); _r(s,L,x+5,y+14,20,3); _r(s,D,x+5,y+24,20,6)
    _r(s,D,x+5,y+17,2,10); _r(s,L,x+7,y+17,3,9); _r(s,D,x+22,y+17,2,10); _r(s,L,x+20,y+17,3,9)
    pygame.draw.ellipse(s,col,(x+1,y+12,12,8)); pygame.draw.ellipse(s,col,(x+19,y+12,12,8))
    _r(s,col,x+2,y+17,6,11); _r(s,col,x+24,y+17,6,11)
    pygame.draw.ellipse(s,D,(x+1,y+26,8,6)); pygame.draw.ellipse(s,D,(x+23,y+26,8,6))
    _r(s,D,x+8,y+29,6,3); _r(s,D,x+18,y+29,6,3); _r(s,D,x+7,y+30,8,2); _r(s,D,x+17,y+30,8,2)
    pygame.draw.ellipse(s,col,(x+5,y+2,22,14)); pygame.draw.ellipse(s,L,(x+5,y+2,22,4))
    pygame.draw.ellipse(s,D,(x+5,y+10,22,6))
    _r(s,YEL,x+8,y+6,5,5); _r(s,YEL,x+19,y+6,5,5); _r(s,BLK,x+9,y+7,3,3); _r(s,BLK,x+20,y+7,3,3)
    _r(s,D,x+13,y+10,6,4); _r(s,BLK,x+14,y+10,2,3); _r(s,BLK,x+17,y+10,2,3)
    _p(s,(230,215,175),[(x+11,y+14),(x+12,y+19),(x+14,y+14)])
    _p(s,(230,215,175),[(x+18,y+14),(x+19,y+19),(x+21,y+14)])
    _r(s,BLK,x+11,y+13,10,2)

def draw_wizard(s, x, y, col):
    R,G,B=col; D=(max(0,R-50),max(0,G-50),max(0,B-60)); L=(min(255,R+40),min(255,G+40),min(255,B+50))
    ORB=(100,200,255); BLK=(0,0,0); SKIN=(220,185,150); BEARD=(200,195,175)
    # 지팡이
    _r(s,(80,60,35),x+3,y+7,3,23)
    pygame.draw.circle(s,ORB,(x+4,y+7),4); pygame.draw.circle(s,(200,230,255),(x+4,y+7),2)
    # 로브
    _p(s,col,[(x+8,y+16),(x+24,y+16),(x+26,y+32),(x+6,y+32)])
    _p(s,L,  [(x+8,y+16),(x+24,y+16),(x+24,y+18),(x+8,y+18)])
    _p(s,D,  [(x+8,y+26),(x+24,y+26),(x+26,y+32),(x+6,y+32)])
    _r(s,col,x+5,y+17,4,8); _r(s,col,x+23,y+17,4,8)
    # 빛나는 손
    pygame.draw.circle(s,ORB,(x+7,y+25),3); pygame.draw.circle(s,(200,230,255),(x+7,y+25),1)
    # 얼굴
    pygame.draw.ellipse(s,SKIN,(x+10,y+9,12,9))
    _r(s,BEARD,x+10,y+14,12,4)
    _r(s,BLK,x+12,y+11,2,2); _r(s,BLK,x+18,y+11,2,2)
    _r(s,ORB,x+12,y+11,1,1); _r(s,ORB,x+18,y+11,1,1)
    # 뾰족한 모자
    _p(s,D,  [(x+16,y+0),(x+8,y+10),(x+24,y+10)])
    _p(s,col,[(x+16,y+0),(x+9,y+10),(x+23,y+10)])
    _r(s,D,x+7,y+9,18,4); _r(s,L,x+7,y+9,18,1)
    pygame.draw.circle(s,(255,255,150),(x+16,y+4),2)

def draw_dragon(s, x, y, col):
    R,G,B=col; D=(max(0,R-50),max(0,G-40),max(0,B-20)); L=(min(255,R+40),min(255,G+30),min(255,B+20))
    BLK=(0,0,0); FIRE=(255,165,0)
    # 꼬리
    _p(s,D,[(x+2,y+28),(x+7,y+22),(x+9,y+28)])
    # 날개
    _p(s,D,[(x+10,y+16),(x+2,y+8),(x+8,y+19)])
    _p(s,D,[(x+22,y+16),(x+30,y+8),(x+24,y+19)])
    _p(s,L,[(x+10,y+16),(x+3,y+10),(x+8,y+19)])
    _p(s,L,[(x+22,y+16),(x+29,y+10),(x+24,y+19)])
    # 몸통
    pygame.draw.ellipse(s,col,(x+8,y+16,18,14)); pygame.draw.ellipse(s,L,(x+9,y+16,16,5))
    pygame.draw.ellipse(s,D,(x+8,y+24,18,6))
    # 목 + 머리
    pygame.draw.ellipse(s,col,(x+10,y+7,12,11)); pygame.draw.ellipse(s,L,(x+11,y+7,10,4))
    # 뿔
    _p(s,D,[(x+11,y+7),(x+9,y+2),(x+13,y+7)])
    _p(s,D,[(x+19,y+7),(x+22,y+2),(x+23,y+7)])
    # 눈
    _r(s,FIRE,x+13,y+10,3,2); _r(s,FIRE,x+18,y+10,3,2)
    _r(s,BLK, x+14,y+10,1,2); _r(s,BLK, x+19,y+10,1,2)
    # 이빨
    _r(s,D,x+12,y+14,8,2)
    _r(s,(240,220,200),x+13,y+14,2,2); _r(s,(240,220,200),x+17,y+14,2,2)
    # 다리
    _r(s,D,x+10,y+29,4,3); _r(s,D,x+18,y+29,4,3)
    _r(s,BLK,x+9,y+31,6,1); _r(s,BLK,x+17,y+31,6,1)

def draw_dark_knight(s, x, y, col):
    draw_orc(s, x, y, col)
    DARK=(15,8,25); DH=(50,35,85); CROWN=(200,155,20)
    pygame.draw.ellipse(s,DARK,(x+7,y+2,18,14)); pygame.draw.ellipse(s,DH,(x+8,y+3,16,5))
    _r(s,(255,30,30),x+10,y+7,4,3); _r(s,(255,30,30),x+18,y+7,4,3)
    _r(s,(255,160,0),x+11,y+8,2,2); _r(s,(255,160,0),x+19,y+8,2,2)
    _r(s,CROWN,x+9,y+1,14,3)
    for cx2 in [x+10, x+14, x+19]:
        _p(s,CROWN,[(cx2,y-3),(cx2+2,y-3),(cx2+1,y+1)])
    _r(s,(20,14,40),x+8,y+14,16,14); _r(s,DH,x+9,y+15,14,2)

def draw_lich(s, x, y, col):
    draw_skeleton(s, x, y, col)
    ROBE=(18,18,55); ROBE_L=(50,50,110)
    _r(s,ROBE,  x+8, y+14,16,16); _r(s,ROBE_L,x+9, y+15,3,8); _r(s,ROBE_L,x+20,y+15,3,8)
    _r(s,(70,55,35),x+2,y+8,3,23)
    pygame.draw.circle(s,(80,180,255),(x+3,y+7),5); pygame.draw.circle(s,(180,220,255),(x+3,y+7),3)
    _r(s,(0,200,255),x+10,y+7,4,4); _r(s,(0,200,255),x+18,y+7,4,4)
    _r(s,(150,230,255),x+11,y+8,2,2); _r(s,(150,230,255),x+19,y+8,2,2)

def draw_generic(s,x,y,col):
    ts=TILE_SIZE; D=tuple(max(0,c-55)for c in col); L=tuple(min(255,c+45)for c in col)
    _r(s,col,x+5,y+7,ts-10,ts-10); pygame.draw.rect(s,L,(x+5,y+7,ts-10,2))
    _r(s,(255,255,255),x+9,y+11,3,3); _r(s,(255,255,255),x+ts-12,y+11,3,3)
    _r(s,(0,0,0),x+10,y+12,2,2); _r(s,(0,0,0),x+ts-11,y+12,2,2)

_SPRITE_FN = {
    'rat':draw_rat,'goblin':draw_goblin,'skeleton':draw_skeleton,'orc':draw_orc,'troll':draw_troll,
    'wizard':draw_wizard,'dragon':draw_dragon,'dark_knight':draw_dark_knight,'lich':draw_lich,
}


# ─────────────────────────────────────────────────────────────────────────────
# 윈도우 아이콘 (32×32 절차적 픽셀아트)
# ─────────────────────────────────────────────────────────────────────────────
def _make_icon():
    surf = pygame.Surface((32, 32))
    surf.fill((10, 10, 20))
    # 별 장식
    for pos in [(4,4),(27,3),(2,25),(29,27),(15,2)]:
        pygame.draw.rect(surf, (180,180,180), (pos[0], pos[1], 1, 1))
    # 투구
    _r(surf,(150,108,18),7,5,18,13); _r(surf,(235,185,60),7,5,18,12)
    _r(surf,(255,222,105),7,5,18,3); _r(surf,(150,108,18),7,8,18,10)
    _r(surf,(0,0,0),9,10,14,4); _r(surf,(150,108,18),9,10,14,1)
    _r(surf,(200,48,48),15,1,2,4); _r(surf,(230,80,80),14,2,4,2)
    # 검
    _r(surf,(178,183,202),13,21,6,9); _r(surf,(118,123,148),13,21,2,9)
    _r(surf,(235,185,60),10,26,12,2); _r(surf,(255,222,105),11,26,2,1)
    return surf


# ═════════════════════════════════════════════════════════════════════════════
#  Game class
# ═════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        # 아이콘은 set_mode 전에 설정
        try:
            pygame.display.set_icon(_make_icon())
        except Exception:
            pass

        self._settings = load_settings()
        set_lang(self._settings.get('language', 'ko'))
        flags = (pygame.FULLSCREEN | pygame.SCALED) if self._settings.get('fullscreen') else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption("Dungeon Door")

        self.clock    = pygame.time.Clock()
        self.input    = InputHandler()
        self.hud      = HUD()
        self.animator = Animator()
        self.audio    = AudioManager()
        self.skills   = SkillManager()

        # 오디오 볼륨 적용
        if self.audio.bgm:
            self.audio.bgm.set_volume(self._settings['bgm_vol'])
        self.audio.set_sfx_volume(self._settings['sfx_vol'])

        self._game_surf  = pygame.Surface((GAME_W, GAME_H))
        self._enemy_data = load_enemies()
        self._item_data  = load_items()
        self._load_sprites()

        self.messages = []
        self.floor    = 1
        self._facing     = 'down'
        self._walk_frame = 0

        # 화면 흔들림
        self._shake_timer     = 0
        self._shake_intensity = 0
        self._shake_max       = 1

        # 층 전환 페이드
        self._fade_alpha    = 0
        self._fade_dir      = 0   # 1=fade to black, -1=fade from black
        self._fade_speed    = 12
        self._fade_callback = None

        # 이동 슬라이딩 애니메이션 (지수 감쇠)
        self._move_anim_offset = [0.0, 0.0]

        # 공격 스프라이트 애니메이션
        # phase: 0=idle, 1=ready(백스윙), 2=strike(전진)
        self._atk_phase = 0
        self._atk_timer = 0

        # 스킬 XP (hit 수 누적 → 자동 레벨업)
        self._skill_xp: dict[str, int] = {'W': 0, 'A': 0, 'S': 0, 'D': 0}

        # 조합 스킬 해금 상태
        self._unlocked_combos: set = set()
        self._skill_books: set     = set()   # 스킬북 소지 여부 (레벨 달성 전)

        # 일시정지
        self._pause_sel = 0

        # 기록
        self._run_kills = 0
        self._records   = load_records()

        # 저장파일 확인 후 메뉴로
        self._save_data         = load_game()
        self._menu_sel          = 0
        self._menu_page         = 'main'
        self._menu_settings_sel = 0
        self._menu_buttons      = []
        self.state  = 'menu'
        self.player  = None
        self.dungeon = None
        self.camera  = None

    # ------------------------------------------------------------------ #
    @staticmethod
    def _scale_fit(surf: pygame.Surface, size: int) -> pygame.Surface:
        """종횡비를 유지하며 size×size 캔버스에 letterbox 배치."""
        sw, sh = surf.get_size()
        ratio  = min(size / sw, size / sh)
        nw, nh = max(1, int(sw * ratio)), max(1, int(sh * ratio))
        scaled  = pygame.transform.scale(surf, (nw, nh))
        canvas  = pygame.Surface((size, size), pygame.SRCALPHA)
        canvas.blit(scaled, ((size - nw) // 2, (size - nh) // 2))
        return canvas

    def _load_sprites(self):
        """assets/sprites/*.png 로드. 없으면 빈 딕셔너리."""
        self._sprites: dict[str, pygame.Surface] = {}
        base    = os.path.join(os.path.dirname(__file__), '..', 'assets')
        spr_dir = os.path.join(base, 'sprites')

        # 종횡비 유지 letterbox: 영웅 + 공격 스프라이트
        fit_names = [
            'hero', 'hero_up', 'hero_back', 'hero_hurt',
            'hero_attack_ready_left',  'hero_attack_end_left',
            'hero_attack_ready_right', 'hero_attack_end_right',
            'hero_attack_ready_up',    'hero_attack_end_up',
            'hero_attack_ready_down',  'hero_attack_end_down',
        ]
        for name in fit_names:
            path = os.path.join(spr_dir, f'{name}.png')
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path).convert_alpha()
                    self._sprites[name] = self._scale_fit(surf, TILE_SIZE)
                except Exception:
                    pass

        # 적 스프라이트: 단순 스케일
        enemy_names = [
            'enemy_rat', 'enemy_goblin', 'enemy_skeleton',
            'enemy_orc', 'enemy_troll',
            'boss_dark_knight', 'boss_lich',
        ]
        for name in enemy_names:
            path = os.path.join(spr_dir, f'{name}.png')
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path).convert_alpha()
                    self._sprites[name] = pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))
                except Exception:
                    pass

    # ── 적 key → 스프라이트 key 매핑 ─────────────────────────────────
    _ENEMY_SPRITE_KEY = {
        'rat':         'enemy_rat',
        'goblin':      'enemy_goblin',
        'skeleton':    'enemy_skeleton',
        'orc':         'enemy_orc',
        'troll':       'enemy_troll',
        'dark_knight': 'boss_dark_knight',
        'lich':        'boss_lich',
    }

    # ------------------------------------------------------------------ #
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._update_fade(dt)
            self._update_shake(dt)
            self._update_move_anim(dt)
            if not self._is_fading:
                self._handle_events(dt)
            self.animator.update(dt)
            self._update_atk_anim(dt)
            if self.state == 'playing':
                self.skills.update(dt)
            if self.state == 'playing':
                self._update_enemies(dt)
            self._update_bgm()
            self._render()

    # ─────────────── 화면 흔들림 ──────────────────────────────────────
    def _start_shake(self, intensity=4, duration_ms=250):
        self._shake_intensity = intensity
        self._shake_timer     = duration_ms
        self._shake_max       = duration_ms

    def _update_shake(self, dt):
        self._shake_timer = max(0, self._shake_timer - dt)

    _ATK_READY_MS  = 90    # 백스윙 유지 시간
    _ATK_STRIKE_MS = 140   # 전진 타격 유지 시간

    def _update_atk_anim(self, dt):
        if self._atk_timer <= 0:
            return
        self._atk_timer -= dt
        if self._atk_timer <= 0:
            if self._atk_phase == 1:
                self._atk_phase = 2
                self._atk_timer = self._ATK_STRIKE_MS
            else:
                self._atk_phase = 0

    def _trigger_atk_anim(self):
        self._atk_phase = 1
        self._atk_timer = self._ATK_READY_MS

    def _update_move_anim(self, dt):
        if self._move_anim_offset[0] == 0.0 and self._move_anim_offset[1] == 0.0:
            return
        factor = 0.982 ** dt
        self._move_anim_offset[0] *= factor
        self._move_anim_offset[1] *= factor
        if abs(self._move_anim_offset[0]) < 0.5:
            self._move_anim_offset[0] = 0.0
        if abs(self._move_anim_offset[1]) < 0.5:
            self._move_anim_offset[1] = 0.0

    @property
    def _shake_offset(self):
        if self._shake_timer <= 0:
            return (0, 0)
        mag = max(0, int(self._shake_intensity * self._shake_timer / self._shake_max))
        return (random.randint(-mag, mag), random.randint(-mag, mag)) if mag > 0 else (0, 0)

    # ─────────────── 층 전환 페이드 ──────────────────────────────────
    def _start_fade(self, callback):
        self._fade_alpha    = 0
        self._fade_dir      = 1
        self._fade_callback = callback

    def _update_fade(self, dt):
        if self._fade_dir == 0:
            return
        self._fade_alpha = max(0, min(255, self._fade_alpha + self._fade_dir * self._fade_speed))
        if self._fade_dir == 1 and self._fade_alpha >= 255:
            if self._fade_callback:
                self._fade_callback()
                self._fade_callback = None
            self._fade_dir = -1
        elif self._fade_dir == -1 and self._fade_alpha <= 0:
            self._fade_dir = 0

    @property
    def _is_fading(self):
        return self._fade_dir != 0

    # ─────────────── BGM 제어 ─────────────────────────────────────────
    def _update_bgm(self):
        if not self.audio.bgm:
            return
        if self.state == 'menu':
            self.audio.bgm.play('menu')
        elif self.state in ('playing', 'shop', 'paused', 'dead'):
            if self.dungeon is None:
                return
            if self.dungeon.is_boss_floor:
                self.audio.bgm.play('boss')
            elif self.dungeon.has_shop:
                self.audio.bgm.play('shop')
            else:
                self.audio.bgm.play('normal')

    # ─────────────── 새 게임 / 불러오기 ──────────────────────────────
    def _new_game(self):
        delete_save()
        self._save_data       = None
        self.floor            = 1
        self._facing          = 'down'
        self._walk_frame      = 0
        self.messages         = []
        self.skills           = SkillManager()
        self._run_kills       = 0
        self._unlocked_combos = set()
        self._skill_books     = set()
        self._skill_levels    = {'W': 1, 'A': 1, 'S': 1, 'D': 1}
        self._skill_xp        = {'W': 0, 'A': 0, 'S': 0, 'D': 0}
        self._load_floor(is_new_game=True)
        self.state = 'playing'

    def _continue_game(self):
        data = self._save_data
        if not data:
            self._new_game(); return
        self.floor       = data['floor']
        self._facing     = 'down'
        self._walk_frame = 0
        self.messages    = []
        self.skills           = SkillManager()
        self.skills.from_dict(data.get('skills', {}))
        self._unlocked_combos = set(data.get('unlocked_combos', []))
        self._skill_books     = set(data.get('skill_books', []))
        self._skill_levels    = data.get('skill_levels', {'W': 1, 'A': 1, 'S': 1, 'D': 1})
        self._skill_xp        = data.get('skill_xp', {'W': 0, 'A': 0, 'S': 0, 'D': 0})
        self._apply_skill_level_cds()
        self._run_kills       = 0
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon = dungeon
        self.player  = Player.from_save(start[0], start[1], data['player'], self._item_data)
        self.camera  = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        self.dungeon.update_visibility(self.player.x, self.player.y)
        self.messages.append((t('floor_cont', self.floor), 'good'))
        self.state = 'playing'

    def _load_floor(self, is_new_game=False):
        dungeon, start = generate_dungeon(MAP_WIDTH, MAP_HEIGHT, self.floor,
                                          self._enemy_data, self._item_data)
        self.dungeon = dungeon
        if is_new_game:
            self.player = Player(*start)
            self.messages.append((t('welcome'), 'good'))
            self.messages.append((t('wasd_hint'), 'info'))
        else:
            self.player.x, self.player.y = start
            self.messages.append((t('floor_arrive', self.floor), 'good'))
            if dungeon.is_boss_floor:
                self.messages.append((t('boss_incoming'), 'bad'))
                self.audio.play('boss_appear')
            elif dungeon.has_shop:
                self.messages.append((t('shop_floor'), 'info'))
            save_game(self.player, self.floor, self.skills, self._unlocked_combos, self._skill_books,
                          self._skill_levels, self._skill_xp)
            self.messages.append((t('auto_saved'), 'info'))
            self.audio.play('save')
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.camera.center_on(self.player.x, self.player.y)
        self.dungeon.update_visibility(self.player.x, self.player.y)

    # ─────────────── 이벤트 / 입력 ───────────────────────────────────
    def _handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == 'menu':
                    self._handle_menu_click(event.pos)

        for action in self.input.update(dt):
            t = action['type']

            if t == 'escape':
                if self.state == 'shop':
                    self.state = 'playing'
                elif self.state == 'paused':
                    self.state = 'playing'
                elif self.state == 'playing':
                    self._pause_sel = 0
                    self.state = 'paused'
                elif self.state == 'menu':
                    if self._menu_page == 'settings':
                        self._menu_page = 'main'
                    else:
                        pygame.quit(); sys.exit()
                elif self.state == 'dead':
                    pygame.quit(); sys.exit()
                continue

            if self.state == 'menu':
                self._handle_menu_action(action)
            elif self.state == 'paused':
                self._handle_pause_action(action)
            elif self.state == 'shop':
                self._handle_shop_action(action)
            elif self.state == 'playing':
                if t in ('move', 'wait', 'attack', 'use_item', 'skill', 'combo_skill'):
                    self._process(action)
            elif self.state == 'dead':
                if t == 'restart':
                    self._new_game()

    def _handle_menu_action(self, action):
        if self._menu_page == 'settings':
            self._handle_menu_settings_action(action)
            return
        typ = action['type']
        n_main = 2 if self._save_data else 1
        total  = n_main + 2  # + settings + quit
        if typ == 'move':
            dy = action.get('dy', 0)
            if dy != 0:
                self._menu_sel = (self._menu_sel + dy) % total
                self.audio.play('menu_select')
        elif typ in ('wait', 'confirm'):
            if self._menu_sel == 0:
                self.audio.play('menu_confirm')
                self._new_game()
            elif self._menu_sel == 1 and self._save_data:
                self.audio.play('menu_confirm')
                self._continue_game()
            elif self._menu_sel == n_main:
                self.audio.play('menu_select')
                self._menu_page = 'settings'
                self._menu_settings_sel = 0
            elif self._menu_sel == n_main + 1:
                pygame.quit(); sys.exit()
        elif typ == 'load' and self._save_data:
            self.audio.play('menu_confirm')
            self._continue_game()

    def _handle_menu_settings_action(self, action):
        typ = action['type']
        if typ == 'move':
            dy = action.get('dy', 0)
            dx = action.get('dx', 0)
            if dy != 0:
                self._menu_settings_sel = (self._menu_settings_sel + dy) % 5
                self.audio.play('menu_select')
            elif dx != 0:
                self._adjust_menu_setting(dx)
        elif typ in ('wait', 'confirm'):
            self.audio.play('menu_select')
            self._confirm_menu_setting()

    def _adjust_menu_setting(self, dx):
        step = 0.1
        if self._menu_settings_sel == 0:
            self._settings['bgm_vol'] = max(0.0, min(1.0, self._settings['bgm_vol'] + dx * step))
            if self.audio.bgm:
                self.audio.bgm.set_volume(self._settings['bgm_vol'])
            save_settings(self._settings)
        elif self._menu_settings_sel == 1:
            self._settings['sfx_vol'] = max(0.0, min(1.0, self._settings['sfx_vol'] + dx * step))
            self.audio.set_sfx_volume(self._settings['sfx_vol'])
            save_settings(self._settings)
        elif self._menu_settings_sel == 2:
            self._toggle_language()
        elif self._menu_settings_sel == 3:
            self._toggle_fullscreen()

    def _confirm_menu_setting(self):
        if self._menu_settings_sel == 2:
            self._toggle_language()
        elif self._menu_settings_sel == 3:
            self._toggle_fullscreen()
        elif self._menu_settings_sel == 4:
            self._menu_page = 'main'

    def _handle_menu_click(self, pos):
        if self._menu_page == 'settings':
            for rect, tag in self._menu_buttons:
                if rect.collidepoint(pos):
                    self._handle_menu_settings_click(tag)
                    break
            return
        for rect, action in self._menu_buttons:
            if rect.collidepoint(pos):
                if action == 'new':
                    self._new_game()
                elif action == 'continue' and self._save_data:
                    self._continue_game()
                elif action == 'settings':
                    self._menu_page = 'settings'
                    self._menu_settings_sel = 0
                elif action == 'quit':
                    pygame.quit(); sys.exit()
                break

    def _handle_menu_settings_click(self, tag):
        tag_to_idx = {'bgm': 0, 'sfx': 1, 'lang': 2, 'fs': 3, 'back': 4}
        if tag == 'back':
            self._menu_page = 'main'
        elif tag == 'lang':
            self._toggle_language()
        elif tag == 'fs':
            self._toggle_fullscreen()
        elif tag in tag_to_idx:
            self._menu_settings_sel = tag_to_idx[tag]

    def _handle_pause_action(self, action):
        act = action['type']
        if act == 'move':
            dy = action.get('dy', 0)
            dx = action.get('dx', 0)
            if dy != 0:
                self._pause_sel = (self._pause_sel + dy) % 8
            elif dx != 0:
                self._adjust_pause_setting(dx)
        elif act in ('wait', 'confirm'):
            self._confirm_pause()

    def _adjust_pause_setting(self, dx):
        step = 0.1
        if self._pause_sel == 2:   # BGM
            self._settings['bgm_vol'] = max(0.0, min(1.0, self._settings['bgm_vol'] + dx*step))
            if self.audio.bgm:
                self.audio.bgm.set_volume(self._settings['bgm_vol'])
            save_settings(self._settings)
        elif self._pause_sel == 3:  # SFX
            self._settings['sfx_vol'] = max(0.0, min(1.0, self._settings['sfx_vol'] + dx*step))
            self.audio.set_sfx_volume(self._settings['sfx_vol'])
            save_settings(self._settings)
        elif self._pause_sel == 4:  # 전체화면
            self._toggle_fullscreen()
        elif self._pause_sel == 5:  # 언어
            self._toggle_language()

    def _confirm_pause(self):
        if self._pause_sel == 0:
            self.state = 'playing'
        elif self._pause_sel == 1:   # 저장하기
            if self.player:
                save_game(self.player, self.floor, self.skills, self._unlocked_combos, self._skill_books,
                          self._skill_levels, self._skill_xp)
                self.messages.append((t('saved'), 'good'))
                self.audio.play('save')
            self.state = 'playing'
        elif self._pause_sel == 4:
            self._toggle_fullscreen()
        elif self._pause_sel == 5:
            self._toggle_language()
        elif self._pause_sel == 6:
            self.state           = 'menu'
            self._menu_sel       = 0
            self._menu_page      = 'main'
            self._save_data      = load_game()
        elif self._pause_sel == 7:
            pygame.quit(); sys.exit()

    def _toggle_language(self):
        cur = self._settings.get('language', 'ko')
        self._settings['language'] = 'en' if cur == 'ko' else 'ko'
        set_lang(self._settings['language'])
        save_settings(self._settings)

    def _toggle_fullscreen(self):
        self._settings['fullscreen'] = not self._settings['fullscreen']
        if self._settings['fullscreen']:
            flags = pygame.FULLSCREEN | pygame.SCALED
        else:
            flags = 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        save_settings(self._settings)

    def _handle_shop_action(self, action):
        t = action['type']
        if t == 'use_item':
            self._buy_item(action['slot'])
        elif t in ('move', 'wait', 'confirm'):
            self.state = 'playing'
            if t == 'move':
                self._process(action)

    # ------------------------------------------------------------------ #
    def _process(self, action):
        acted = False
        if   action['type'] == 'move':     acted = self._player_move(action['dx'], action['dy'])
        elif action['type'] == 'wait':     acted = True
        elif action['type'] == 'attack':   acted = self._player_basic_attack()
        elif action['type'] == 'use_item': acted = self._use_item(action['slot'])
        elif action['type'] == 'skill':       acted = self._use_skill(action['skill'])
        elif action['type'] == 'combo_skill': acted = self._use_combo_skill(action['combo'])
        if acted:
            self.dungeon.update_visibility(self.player.x, self.player.y)
            self.camera.center_on(self.player.x, self.player.y)

    def _player_move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if   dx > 0: self._facing = 'right'
        elif dx < 0: self._facing = 'left'
        elif dy > 0: self._facing = 'down'
        elif dy < 0: self._facing = 'up'
        self._walk_frame ^= 1

        enemy = self.dungeon.get_enemy_at(nx, ny)
        if enemy:
            self._trigger_atk_anim()
            self._player_attack(enemy); return True
        if not self.dungeon.is_walkable(nx, ny):
            return False

        # 이동 슬라이딩: 현재 오프셋에 새 방향을 누적 (클램프)
        self._move_anim_offset[0] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[0] - dx * TILE_SIZE))
        self._move_anim_offset[1] = max(-TILE_SIZE, min(TILE_SIZE, self._move_anim_offset[1] - dy * TILE_SIZE))

        self.player.x, self.player.y = nx, ny
        item = self.dungeon.get_item_at(nx, ny)
        if item:
            self._pickup(item)

        tile = self.dungeon.tiles[ny][nx]
        if tile.tile_type == TileType.SHOP and self.dungeon.has_shop:
            self.state = 'shop'
            self.audio.play('shop_open')
            return True

        if (nx, ny) == self.dungeon.stairs_pos:
            self.floor += 1
            self._start_fade(self._load_floor)
        return True

    def _player_basic_attack(self):
        """Space bar: 바라보는 방향 인접 타일 공격. 적 없으면 허공 스윙."""
        self._trigger_atk_anim()
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0,1))
        tx, ty = self.player.x + dx, self.player.y + dy
        enemy = self.dungeon.get_enemy_at(tx, ty)
        if enemy:
            self._player_attack(enemy)
        else:
            self.audio.play('swing')
        return True

    def _player_attack(self, enemy):
        crit = random.random() < 0.1
        dmg  = max(1, self.player.attack - enemy.defense + random.randint(0, 3))
        if crit:
            dmg *= 2
            self.messages.append((t('crit_hit', enemy.name, dmg), 'warn'))
        else:
            self.messages.append((t('normal_hit', enemy.name, dmg), 'warn'))
        enemy.take_damage(dmg)
        self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (255, 80, 80)))
        self.audio.play('crit' if crit else 'attack')
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)

    def _on_enemy_killed(self, enemy):
        gold = enemy.gold_drop
        self._run_kills += 1
        if gold:
            self.player.gold += gold
            self.messages.append((t('kill_gold', enemy.name, enemy.xp_value, gold), 'good'))
        else:
            self.messages.append((t('kill', enemy.name, enemy.xp_value), 'good'))
        if self.player.gain_xp(enemy.xp_value):
            self.messages.append((t('levelup', self.player.level), 'good'))
            self.audio.play('levelup')
            for cid, cdef in COMBO_SKILL_DEFS.items():
                if (cid in self._skill_books and
                        cid not in self._unlocked_combos and
                        self.player.level >= cdef['level_req']):
                    self._unlocked_combos.add(cid)
                    self.messages.append((t('combo_unlock', cdef['name']), 'good'))
        self.dungeon.enemies.remove(enemy)
        self._check_boss_cleared()

    def _pickup(self, item):
        if item.effect == 'unlock_combo':
            combo_id = str(item.value)
            cdef = COMBO_SKILL_DEFS.get(combo_id)
            self.dungeon.remove_item(item)
            self.audio.play('pickup')
            if cdef:
                self._skill_books.add(combo_id)
                if self.player.level >= cdef['level_req']:
                    self._unlocked_combos.add(combo_id)
                    self.messages.append((t('combo_unlock', cdef['name']), 'good'))
                else:
                    self.messages.append((t('combo_need_level', item.name, cdef['level_req']), 'warn'))
            return
        if len(self.player.inventory) < self.player.max_inventory:
            self.player.inventory.append(item)
            self.dungeon.remove_item(item)
            self.messages.append((t('pickup', item.name), 'good'))
            self.audio.play('pickup')
        else:
            self.messages.append((t('inv_full'), 'warn'))

    def _use_item(self, slot):
        if slot >= len(self.player.inventory):
            return False
        item = self.player.inventory[slot]
        if item.effect == 'teleport':
            self.player.inventory.pop(slot)
            self._use_teleport()
        elif item.effect == 'whirlwind':
            self.player.inventory.pop(slot)
            self._skill_whirl(no_cooldown=True)
        else:
            self.player.inventory.pop(slot)
            self.messages.append((item.use(self.player), 'good'))
            self.audio.play('use_item')
        return True

    def _buy_item(self, slot):
        if slot >= len(self.dungeon.shop_items):
            return
        item, price = self.dungeon.shop_items[slot]
        if self.player.gold < price:
            self.messages.append((t('no_gold'), 'warn')); self.audio.play('no_gold'); return
        if len(self.player.inventory) >= self.player.max_inventory:
            self.messages.append((t('inv_full'), 'warn')); return
        self.player.gold -= price
        self.player.inventory.append(item)
        self.dungeon.shop_items.pop(slot)
        self.messages.append((t('buy_ok', item.name, price), 'good'))
        self.audio.play('buy')

    def _use_teleport(self):
        candidates = [(x, y)
                      for y in range(self.dungeon.height)
                      for x in range(self.dungeon.width)
                      if (self.dungeon.tiles[y][x].explored and
                          not self.dungeon.tiles[y][x].blocked and
                          not self.dungeon.get_enemy_at(x, y) and
                          (x, y) != (self.player.x, self.player.y))]
        if candidates:
            self.player.x, self.player.y = random.choice(candidates)
            self.messages.append((t('teleport'), 'warn'))
            self.audio.play('teleport')
            self._start_shake(3, 150)

    # ─────────────── 스킬 ─────────────────────────────────────────────
    def _use_skill(self, key):
        if not self.skills.ready(key):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(key)), 'info'))
            return False
        if key == 'W': return self._skill_dash()
        if key == 'A': return self._skill_whirl()
        if key == 'S': return self._skill_heal()
        if key == 'D': return self._skill_power_attack()
        return False

    def _skill_dash(self):
        lvl   = self._skill_levels['W']
        tiles = SKILL_UPGRADES['W'][lvl - 1]['tiles']
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        moved = 0
        for _ in range(tiles):
            nx, ny = self.player.x + dx, self.player.y + dy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if enemy:
                self._player_attack(enemy); break
            if not self.dungeon.is_walkable(nx, ny): break
            self.player.x, self.player.y = nx, ny; moved += 1
        self._trigger_atk_anim()
        self._gain_skill_xp('W')
        self.skills.trigger('W')
        self.audio.play('skill_dash')
        self.messages.append((t('skill_dash', moved), 'warn'))
        return True

    def _skill_whirl(self, no_cooldown=False):
        lvl    = self._skill_levels['A']
        stats  = SKILL_UPGRADES['A'][lvl - 1]
        radius = stats['radius']
        mul    = stats['mul']
        dirs = [(ddx, ddy) for ddx in range(-radius, radius+1)
                for ddy in range(-radius, radius+1)
                if not (ddx == 0 and ddy == 0)]
        hits = 0
        for ddx, ddy in dirs:
            nx, ny = self.player.x+ddx, self.player.y+ddy
            enemy = self.dungeon.get_enemy_at(nx, ny)
            if not enemy: continue
            crit = random.random() < 0.1
            dmg  = max(1, int(self.player.attack * mul) - enemy.defense + random.randint(0,3))
            if crit: dmg *= 2
            enemy.take_damage(dmg)
            self.animator.add(SlashAnim(self.player.x, self.player.y, nx, ny, (255,180,60)))
            self.animator.add(HitFlashAnim(nx, ny, dmg, (255,80,80)))
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(self.player.x, self.player.y))
        if not no_cooldown:
            self._gain_skill_xp('A', hits)
            self.skills.trigger('A')
        self.audio.play('skill_whirl')
        self.messages.append((t('skill_whirl_h', hits) if hits else t('skill_whirl_m'),
                               'warn' if hits else 'info'))
        return True

    def _skill_heal(self):
        lvl      = self._skill_levels['S']
        heal_pct = SKILL_UPGRADES['S'][lvl - 1]['heal_pct']
        amt = max(1, int(self.player.max_hp * heal_pct))
        self.player.heal(amt)
        self.animator.add(HealAnim(self.player.x, self.player.y))
        self._gain_skill_xp('S')
        self.skills.trigger('S')
        self.audio.play('skill_heal')
        self.messages.append((t('skill_heal', amt), 'good'))
        return True

    def _skill_power_attack(self):
        lvl   = self._skill_levels['D']
        stats = SKILL_UPGRADES['D'][lvl - 1]
        mul   = stats['mul']
        crit_chance = stats['crit']
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        tx, ty = self.player.x + dx, self.player.y + dy
        enemy  = self.dungeon.get_enemy_at(tx, ty)
        self._trigger_atk_anim()
        self.animator.add(AttackSwingAnim(self.player.x, self.player.y, self._facing, hit=bool(enemy)))
        if not enemy:
            self.audio.play('swing')
            self.skills.trigger('D')
            self.messages.append((t('skill_power_miss'), 'info'))
            return True
        crit = random.random() < crit_chance
        dmg  = max(1, int(self.player.attack * mul) - enemy.defense)
        if crit: dmg = int(dmg * 1.5)
        enemy.take_damage(dmg)
        self.animator.add(HitFlashAnim(tx, ty, dmg, (255, 120, 50)))
        if crit:
            self.audio.play('crit')
            self.messages.append((t('crit_hit', enemy.name, dmg), 'bad'))
        else:
            self.audio.play('attack')
            self.messages.append((t('skill_power', enemy.name, dmg), 'warn'))
        if not enemy.is_alive():
            self._on_enemy_killed(enemy)
        self._gain_skill_xp('D')
        self.skills.trigger('D')
        return True

    # ─────────────── 스킬 강화 ───────────────────────────────────────
    def _apply_skill_level_cds(self):
        for key, lvl in self._skill_levels.items():
            cd_ms = SKILL_UPGRADES[key][lvl - 1]['cd_ms']
            self.skills.set_cd_override(key, cd_ms)

    def _gain_skill_xp(self, key: str, amount: int = 1):
        lvl = self._skill_levels.get(key, 1)
        if lvl >= SKILL_MAX_LEVEL:
            return
        self._skill_xp[key] = self._skill_xp.get(key, 0) + amount
        req = SKILL_XP_REQ[key][lvl - 1]
        if self._skill_xp[key] >= req:
            self._skill_xp[key] -= req
            self._skill_levels[key] = lvl + 1
            self._apply_skill_level_cds()
            name_key = {'W': 'skill_w_name', 'A': 'skill_a_name',
                        'S': 'skill_s_name', 'D': 'skill_d_name'}.get(key, key)
            self.messages.append((t('upg_done', t(name_key), self._skill_levels[key]), 'good'))
            self.audio.play('levelup')


    # ─────────────── 조합 스킬 ───────────────────────────────────────
    def _use_combo_skill(self, combo_id):
        cdef = COMBO_SKILL_DEFS.get(combo_id)
        if not cdef:
            return False
        if combo_id not in self._unlocked_combos:
            if combo_id in self._skill_books:
                self.messages.append((t('combo_need_level', cdef['name'], cdef['level_req']), 'warn'))
            else:
                self.messages.append((t('combo_no_unlock', cdef['name'], cdef['level_req']), 'warn'))
            return False
        if not self.skills.ready(combo_id):
            self.messages.append((t('skill_cd', self.skills.remaining_sec(combo_id)), 'info'))
            return False
        if combo_id == 'WS': return self._skill_fireball()
        if combo_id == 'AD': return self._skill_thunder()
        if combo_id == 'WA': return self._skill_frost()
        if combo_id == 'WD': return self._skill_wind()
        return False

    def _skill_fireball(self):
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hit = False
        for step in range(1, 6):
            tx, ty = px + dx * step, py + dy * step
            if not self.dungeon.is_walkable(tx, ty) and not self.dungeon.get_enemy_at(tx, ty):
                self.animator.add(BoltAnim(px, py, tx, ty, (255, 140, 40)))
                break
            enemy = self.dungeon.get_enemy_at(tx, ty)
            if enemy:
                crit = random.random() < 0.3
                dmg  = max(1, int(self.player.attack * 2.2) - enemy.defense)
                if crit: dmg = int(dmg * 1.5)
                enemy.take_damage(dmg)
                self.animator.add(BoltAnim(px, py, tx, ty, (255, 140, 40)))
                self.animator.add(HitFlashAnim(tx, ty, dmg, (255, 100, 30)))
                if crit:
                    self.messages.append((t('crit_hit', enemy.name, dmg), 'bad'))
                else:
                    self.messages.append((t('skill_fireball', enemy.name, dmg), 'warn'))
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
                hit = True
                break
        if not hit:
            self.messages.append((t('skill_fireball_m'), 'info'))
        self.audio.play('skill_dash')
        self.skills.trigger('WS')
        return True

    def _skill_thunder(self):
        hits = 0
        for enemy in list(self.dungeon.enemies):
            if not (enemy.is_alive() and self.dungeon.tiles[enemy.y][enemy.x].visible):
                continue
            dmg = max(1, int(self.player.attack * 0.85) - enemy.defense)
            enemy.take_damage(dmg)
            self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (200, 160, 255)))
            hits += 1
            if not enemy.is_alive():
                self._on_enemy_killed(enemy)
        if hits:
            self._start_shake(4, 350)
            self.messages.append((t('skill_thunder', hits), 'warn'))
        else:
            self.messages.append((t('skill_thunder_m'), 'info'))
        self.audio.play('skill_whirl')
        self.skills.trigger('AD')
        return True

    def _skill_frost(self):
        px, py = self.player.x, self.player.y
        hits = 0
        for enemy in list(self.dungeon.enemies):
            if not enemy.is_alive():
                continue
            if max(abs(enemy.x - px), abs(enemy.y - py)) <= 2:
                dmg = max(1, int(self.player.attack * 1.3) - enemy.defense)
                enemy.take_damage(dmg)
                self.animator.add(HitFlashAnim(enemy.x, enemy.y, dmg, (100, 220, 255)))
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        self.animator.add(WhirlAnim(px, py))
        if hits:
            self.messages.append((t('skill_frost', hits), 'good'))
        else:
            self.messages.append((t('skill_frost_m'), 'info'))
        self.audio.play('skill_heal')
        self.skills.trigger('WA')
        return True

    def _skill_wind(self):
        dirs = {'right':(1,0),'left':(-1,0),'down':(0,1),'up':(0,-1)}
        dx, dy = dirs.get(self._facing, (0, 1))
        px, py = self.player.x, self.player.y
        hits = 0
        for step in range(1, 7):
            tx, ty = px + dx * step, py + dy * step
            if not (0 <= tx < self.dungeon.width and 0 <= ty < self.dungeon.height):
                break
            if not self.dungeon.is_walkable(tx, ty) and not self.dungeon.get_enemy_at(tx, ty):
                break
            enemy = self.dungeon.get_enemy_at(tx, ty)
            if enemy and enemy.is_alive():
                dmg = max(1, int(self.player.attack * 1.5) - enemy.defense)
                enemy.take_damage(dmg)
                self.animator.add(SlashAnim(px, py, tx, ty, (160, 255, 160)))
                self.animator.add(HitFlashAnim(tx, ty, dmg, (160, 255, 160)))
                hits += 1
                if not enemy.is_alive():
                    self._on_enemy_killed(enemy)
        if hits:
            self.messages.append((t('skill_wind', hits), 'warn'))
        else:
            self.messages.append((t('skill_wind_m'), 'info'))
        self.audio.play('skill_dash')
        self.skills.trigger('WD')
        return True

    # ─────────────── 보스 처치 ────────────────────────────────────────
    def _check_boss_cleared(self):
        if (self.dungeon.is_boss_floor and
                self.dungeon.boss and
                not self.dungeon.boss.is_alive() and
                self.dungeon.stairs_pos is None):
            bx, by = self.dungeon.boss.x, self.dungeon.boss.y
            self.dungeon.tiles[by][bx] = Tile.stairs_down()
            self.dungeon.stairs_pos = (bx, by)
            self.messages.append((t('boss_clear'), 'good'))
            self.audio.play('stairs')
            self._start_shake(6, 400)

    # ─────────────── 실시간 적 AI ─────────────────────────────────────
    def _update_enemies(self, dt):
        for enemy in list(self.dungeon.enemies):
            if not (enemy.is_alive() and self.player.is_alive()):
                continue
            prev_hp = self.player.hp
            enemy.update(dt, self.dungeon, self.player, self.messages)
            if self.player.hp < prev_hp:
                dmg = prev_hp - self.player.hp
                self.animator.add(HitFlashAnim(self.player.x, self.player.y, dmg, (255,50,50)))
                self.audio.play('player_hit')
                self._start_shake(4 if enemy.is_boss else 2, 200)
                # 원거리 공격 볼트 연출
                dist = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
                if dist > 1:
                    self.animator.add(BoltAnim(enemy.x, enemy.y,
                                               self.player.x, self.player.y,
                                               (100,180,255) if enemy.key=='wizard' else (255,140,0)))

        if not self.player.is_alive() and self.state == 'playing':
            self._records = update_records(self.floor, self._run_kills, self.player.gold)
            delete_save()
            self.audio.play('death')
            self.state = 'dead'

    # ─────────────── 렌더링 ───────────────────────────────────────────
    def _render(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            sf = self._save_data['floor'] if self._save_data else None
            self._menu_buttons = self.hud.render_menu(
                self.screen, bool(self._save_data), sf,
                self._menu_sel, pygame.mouse.get_pos(),
                page=self._menu_page,
                settings=self._settings,
                settings_sel=self._menu_settings_sel,
            )
            pygame.display.flip()
            return

        self._render_dungeon()
        self.hud.render(self.screen, self.player, self.messages, self.floor,
                        self.dungeon, self.skills,
                        unlocked_combos=self._unlocked_combos,
                        skill_books=self._skill_books,
                        skill_levels=self._skill_levels,
                        skill_xp=self._skill_xp)

        if self.dungeon.is_boss_floor and self.dungeon.boss and self.dungeon.boss.is_alive():
            self.hud.render_boss_bar(self.screen, self.dungeon.boss)

        # 층 전환 페이드 오버레이
        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((GAME_W, GAME_H))
            fade_surf.fill(BLACK)
            fade_surf.set_alpha(self._fade_alpha)
            self.screen.blit(fade_surf, (GAME_X, GAME_Y))

        if self.state == 'shop':
            self.hud.render_shop(self.screen, self.dungeon.shop_items, self.player.gold)
        elif self.state == 'paused':
            self.hud.render_paused(self.screen, self._settings, self._pause_sel)
        elif self.state == 'dead':
            self.hud.render_game_over(self.screen, self.floor, self._records)

        pygame.display.flip()

    def _render_dungeon(self):
        self._game_surf.fill(BLACK)
        cx, cy = self.camera.x, self.camera.y

        for ty in range(VIEWPORT_TILES_Y + 1):
            for tx in range(VIEWPORT_TILES_X + 1):
                wx, wy = cx+tx, cy+ty
                if not self.dungeon.in_bounds(wx, wy): continue
                tile = self.dungeon.tiles[wy][wx]
                sx, sy = tx*TILE_SIZE, ty*TILE_SIZE
                if tile.visible:    self._draw_tile(tile, sx, sy, True)
                elif tile.explored: self._draw_tile(tile, sx, sy, False)

        for item in self.dungeon.items:
            if self.dungeon.tiles[item.y][item.x].visible:
                self._draw_item(item, (item.x-cx)*TILE_SIZE, (item.y-cy)*TILE_SIZE)

        for enemy in self.dungeon.enemies:
            if enemy.is_alive() and self.dungeon.tiles[enemy.y][enemy.x].visible:
                self._draw_enemy(enemy, (enemy.x-cx)*TILE_SIZE, (enemy.y-cy)*TILE_SIZE)

        ox, oy = self.animator.player_offset
        ox += int(self._move_anim_offset[0])
        oy += int(self._move_anim_offset[1])
        px = (self.player.x - cx) * TILE_SIZE + ox
        py = (self.player.y - cy) * TILE_SIZE + oy
        self._draw_player_sprite(px, py)

        self.animator.draw(self._game_surf, cx, cy)

        # 화면 흔들림 오프셋 적용
        sox, soy = self._shake_offset
        self.screen.blit(self._game_surf, (GAME_X + sox, GAME_Y + soy))

    def _draw_tile(self, tile, x, y, lit):
        ts = TILE_SIZE; s = self._game_surf; tt = tile.tile_type
        if tt == TileType.WALL:
            col = WALL_LIT if lit else WALL_DIM
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit:
                pygame.draw.line(s,WALL_TOP,(x,y),(x+ts-1,y))
                pygame.draw.line(s,WALL_TOP,(x,y),(x,y+ts-1))
                pygame.draw.line(s,WALL_BOT,(x,y+ts-1),(x+ts-1,y+ts-1))
        elif tt == TileType.SHOP:
            col = (25,55,30) if lit else (12,28,15)
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit:
                pygame.draw.rect(s, SHOP_COLOR, (x,y,ts,ts), 1)
                ccx, ccy = x+ts//2, y+ts//2
                pygame.draw.circle(s, SHOP_COLOR, (ccx, ccy), 6, 2)
                _r(s, SHOP_COLOR, ccx, ccy-1, 5, 2)
        else:
            col = FLOOR_LIT if lit else FLOOR_DIM
            pygame.draw.rect(s, col, (x,y,ts,ts))
            if lit: pygame.draw.rect(s, FLOOR_EDGE, (x,y,ts,ts), 1)
            if tt == TileType.STAIRS_DOWN:
                sc = STAIRS_LIT if lit else STAIRS_DIM
                ccx, ccy = x+ts//2, y+ts//2
                pygame.draw.polygon(s, sc, [(ccx,ccy+7),(ccx-6,ccy-3),(ccx+6,ccy-3)])
                pygame.draw.line(s, sc, (ccx-4,ccy-3),(ccx+4,ccy-3), 2)

    def _draw_player_sprite(self, x, y):
        facing = self._facing
        phase  = self._atk_phase
        ts  = TILE_SIZE
        spr = None

        if facing in ('left', 'right'):
            side = 'left' if facing == 'left' else 'right'
            if phase == 1:
                spr = self._sprites.get(f'hero_attack_ready_{side}')
            elif phase == 2:
                spr = self._sprites.get(f'hero_attack_end_{side}')
            if spr is None:
                spr = self._sprites.get('hero')
                if spr and facing == 'left':
                    spr = pygame.transform.flip(spr, True, False)

        elif facing == 'up':
            if phase == 1:
                spr = self._sprites.get('hero_attack_ready_up')
            elif phase == 2:
                spr = self._sprites.get('hero_attack_end_up')
            if spr is None:
                spr = self._sprites.get('hero_up') or self._sprites.get('hero')

        else:  # down
            if phase == 1:
                spr = self._sprites.get('hero_attack_ready_down')
            elif phase == 2:
                spr = self._sprites.get('hero_attack_end_down')
            if spr is None:
                spr = self._sprites.get('hero')

        if spr:
            self._game_surf.blit(spr, (x, y))
        else:
            draw_player(self._game_surf, x, y, facing, self._walk_frame)

    def _draw_enemy(self, enemy, x, y):
        spr_key = self._ENEMY_SPRITE_KEY.get(enemy.key)
        spr     = self._sprites.get(spr_key) if spr_key else None
        if spr:
            self._game_surf.blit(spr, (x, y))
        else:
            fn = _SPRITE_FN.get(enemy.key, draw_generic)
            fn(self._game_surf, x, y, enemy.color)
        draw_hp_bar(self._game_surf, x, y, enemy.hp, enemy.max_hp)

    def _draw_item(self, item, x, y):
        ts=TILE_SIZE; s=self._game_surf
        ccx, ccy = x+ts//2, y+ts//2
        col = item.color
        pygame.draw.polygon(s, col, [(ccx,ccy-7),(ccx+6,ccy),(ccx,ccy+7),(ccx-6,ccy)])
        pygame.draw.polygon(s, WHITE, [(ccx,ccy-7),(ccx+6,ccy),(ccx,ccy+7),(ccx-6,ccy)], 1)
        if item.item_type == 'consumable':
            _r(s,(255,100,100),ccx-1,ccy-3,2,6); _r(s,(255,100,100),ccx-3,ccy-1,6,2)
        elif item.item_type == 'weapon':
            pygame.draw.line(s, WHITE, (ccx-3,ccy+3),(ccx+3,ccy-3), 2)
        elif item.item_type == 'armor':
            pygame.draw.rect(s, WHITE, (ccx-2,ccy-2,4,4), 1)
