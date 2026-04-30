"""절차적 사운드 + BGM (외부 파일·numpy 불필요)."""
import math
import random
import struct
import pygame

# ─────────────────────────────────────────────────────
#  내부 유틸리티
# ─────────────────────────────────────────────────────
_SINE_TABLE_SIZE = 2048
_SINE_TABLE = [math.sin(2 * math.pi * i / _SINE_TABLE_SIZE) for i in range(_SINE_TABLE_SIZE)]


def _wave(mono, channels=2):
    if channels == 2:
        data = [v for s in mono for v in (s, s)]
    else:
        data = list(mono)
    return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))


def _note(freq, ms, vol=0.5, wave='sine', rate=44100):
    """단일 음표 프레임 생성."""
    n = int(rate * ms / 1000)
    frames = []
    step = _SINE_TABLE_SIZE * freq / rate
    idx = 0.0
    attack  = min(int(n * 0.06), 100)
    release = min(int(n * 0.18), 200)
    for i in range(n):
        env = (i / attack) if i < attack else (1.0 if i < n - release else (n - i) / max(1, release))
        if freq == 0:
            s = 0.0
        elif wave == 'sine':
            s = _SINE_TABLE[int(idx) % _SINE_TABLE_SIZE]
        elif wave == 'tri':
            phase = (idx / _SINE_TABLE_SIZE) % 1.0
            s = 2 * abs(2 * phase - 1) - 1
        else:  # square
            s = 1.0 if _SINE_TABLE[int(idx) % _SINE_TABLE_SIZE] > 0 else -1.0
        frames.append(max(-32767, min(32767, int(32767 * vol * env * s))))
        idx += step
    return frames


def _seq(notes_ms, vol=0.12, wave='sine', rate=44100):
    """[(freq, ms), ...] 시퀀스를 이어 붙인 프레임 반환."""
    out = []
    for freq, ms in notes_ms:
        out += _note(freq, ms, vol, wave, rate)
    return out


def _mix(*layers):
    """여러 프레임 리스트를 혼합."""
    if not layers:
        return []
    n = max(len(l) for l in layers)
    return [max(-32767, min(32767, sum(l[i] if i < len(l) else 0 for l in layers))) for i in range(n)]


def _noise(ms, vol=0.3, rate=44100):
    n = int(rate * ms / 1000)
    return [max(-32767, min(32767, int(32767 * vol * (1 - i/n) * (random.random()*2-1)))) for i in range(n)]


def _square(freq, ms, vol=0.3, rate=44100):
    return _note(freq, ms, vol, 'square', rate)


def _sine(freq, ms, vol=0.5, rate=44100):
    return _note(freq, ms, vol, 'sine', rate)


# ─────────────────────────────────────────────────────
#  BGM 플레이어
# ─────────────────────────────────────────────────────
class BGMPlayer:
    def __init__(self, rate, channels):
        self._rate    = rate
        self._ch      = channels
        self._channel = pygame.mixer.Channel(6)
        self._current = None
        self._vol     = 0.5
        self._sounds  = {}
        self._build()

    def _build(self):
        r, ch = self._rate, self._ch
        try:
            self._sounds = {
                'menu':   self._menu(r, ch),
                'normal': self._normal(r, ch),
                'boss':   self._boss(r, ch),
                'shop':   self._shop(r, ch),
            }
        except Exception:
            pass

    # ---- BGM 트랙 생성 ----------------------------------------
    @staticmethod
    def _normal(r, ch):
        # Am 펜타토닉 어두운 앰비언트
        bass = _seq([(110,600),(0,200),(110,400),(0,200),(82.4,600),(0,400),(98,400),(0,200)], 0.08,'tri',r)
        mel  = _seq([(220,800),(0,400),(262,600),(0,600),(196,600),(0,800),(0,800)], 0.05,'sine',r)
        pad  = _seq([(110,4800),(0,200)], 0.04,'sine',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _boss(r, ch):
        # 긴박한 트리톤 펄스
        bass = _seq([(110,120),(0,30),(155,120),(0,30)] * 12, 0.10,'square',r)
        hrm  = _seq([(220,100),(0,100),(233,100),(0,100)] * 12, 0.06,'square',r)
        return _wave(_mix(bass, hrm), ch)

    @staticmethod
    def _shop(r, ch):
        # C 장조 친근한 멜로디
        mel  = _seq([(262,400),(330,400),(392,400),(330,400),(262,600),(0,600),(330,400),(392,800)], 0.08,'tri',r)
        bass = _seq([(131,800),(0,400),(98,800),(0,400),(131,1200)], 0.06,'sine',r)
        return _wave(_mix(mel, bass), ch)

    @staticmethod
    def _menu(r, ch):
        # 극적인 오픈 5도
        mel  = _seq([(220,400),(0,100),(220,300),(0,200),(262,500),(0,300),(196,700),(0,500)], 0.09,'tri',r)
        bass = _seq([(110,1200),(0,200),(82.4,1000),(0,200)], 0.07,'sine',r)
        pad  = _seq([(165,3800)], 0.04,'sine',r)
        return _wave(_mix(mel, bass, pad), ch)

    # ---- 공개 API ------------------------------------------------
    def play(self, name):
        if self._current == name:
            return
        self._current = name
        s = self._sounds.get(name)
        if s:
            self._channel.stop()
            self._channel.set_volume(self._vol)
            self._channel.play(s, loops=-1)

    def stop(self):
        self._channel.fadeout(400)
        self._current = None

    def set_volume(self, vol):
        self._vol = max(0.0, min(1.0, vol))
        self._channel.set_volume(self._vol)


# ─────────────────────────────────────────────────────
#  SFX 매니저
# ─────────────────────────────────────────────────────
class AudioManager:
    def __init__(self):
        self.enabled   = False
        self._sounds   = {}
        self._sfx_vol  = 0.8
        self._rate     = 44100
        self._channels = 2
        self.bgm: BGMPlayer | None = None
        try:
            info = pygame.mixer.get_init()
            if not info:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                info = pygame.mixer.get_init()
            if info:
                self._rate, _, self._channels = info
                self._build_sfx()
                self.bgm = BGMPlayer(self._rate, self._channels)
                self.enabled = True
        except Exception:
            pass

    def _build_sfx(self):
        r, ch = self._rate, self._channels
        try:
            defs = {
                'attack':      _square(440,70,rate=r) + _square(330,50,rate=r),
                'enemy_hit':   _noise(60, 0.2, rate=r),
                'player_hit':  _noise(90, 0.4, rate=r),
                'pickup':      _sine(700,50,rate=r) + _sine(1050,70,rate=r),
                'levelup':     _sine(440,70,rate=r)+_sine(550,70,rate=r)+_sine(660,100,rate=r),
                'use_item':    _sine(500,100,rate=r),
                'stairs':      _sine(330,50,rate=r)+_sine(440,50,rate=r)+_sine(550,80,rate=r),
                'boss_appear': _noise(220,0.5,rate=r),
                'shop_open':   _sine(800,50,rate=r)+_sine(1200,70,rate=r),
                'buy':         _sine(600,60,rate=r)+_sine(900,80,rate=r),
                'no_gold':     _square(200,120,rate=r),
                'skill_dash':  _square(880,50,rate=r)+_square(660,40,rate=r),
                'skill_whirl': _noise(120,0.35,rate=r),
                'skill_heal':  _sine(528,100,rate=r)+_sine(660,120,rate=r),
                'death':       _noise(80,0.5,rate=r)+_sine(200,100,rate=r)+_sine(150,150,rate=r),
                'save':        _sine(440,40,rate=r)+_sine(550,40,rate=r),
                'teleport':    _square(880,60,rate=r)+_square(660,60,rate=r)+_square(440,80,rate=r),
                'swing':       _square(440,30,0.15,rate=r)+_square(330,40,0.10,rate=r),
            }
            for k, v in defs.items():
                self._sounds[k] = _wave(v, ch)
        except Exception:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        s = self._sounds.get(name)
        if s:
            try:
                ch = s.play()
                if ch:
                    ch.set_volume(self._sfx_vol)
            except Exception:
                pass

    def set_sfx_volume(self, vol):
        self._sfx_vol = max(0.0, min(1.0, vol))
        for s in self._sounds.values():
            if s:
                try:
                    s.set_volume(self._sfx_vol)
                except Exception:
                    pass
