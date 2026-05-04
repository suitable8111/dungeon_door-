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
    n = int(rate * ms / 1000)
    frames = []
    step = _SINE_TABLE_SIZE * freq / rate
    idx = 0.0
    attack  = min(int(n * 0.08), 150)
    release = min(int(n * 0.20), 300)
    for i in range(n):
        env = (i / attack) if i < attack else (1.0 if i < n - release else (n - i) / max(1, release))
        if freq == 0:
            s = 0.0
        elif wave == 'sine':
            s = _SINE_TABLE[int(idx) % _SINE_TABLE_SIZE]
        elif wave == 'tri':
            phase = (idx / _SINE_TABLE_SIZE) % 1.0
            s = 2 * abs(2 * phase - 1) - 1
        elif wave == 'saw':
            phase = (idx / _SINE_TABLE_SIZE) % 1.0
            s = 2 * phase - 1
        else:  # square
            s = 1.0 if _SINE_TABLE[int(idx) % _SINE_TABLE_SIZE] > 0 else -1.0
        frames.append(max(-32767, min(32767, int(32767 * vol * env * s))))
        idx += step
    return frames


def _seq(notes_ms, vol=0.12, wave='sine', rate=44100):
    out = []
    for freq, ms in notes_ms:
        out += _note(freq, ms, vol, wave, rate)
    return out


def _mix(*layers):
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


def _saw(freq, ms, vol=0.4, rate=44100):
    return _note(freq, ms, vol, 'saw', rate)


# ─────────────────────────────────────────────────────
#  BGM 플레이어
# ─────────────────────────────────────────────────────
class BGMPlayer:
    _FADE_MS = 600

    def __init__(self, rate, channels):
        self._rate    = rate
        self._ch      = channels
        self._channel = pygame.mixer.Channel(6)
        self._current = None
        self._vol     = 0.5
        self._sounds  = {}
        self._pending: str | None = None
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

    # ---- BGM 트랙 생성 (~10-13초 루프) ----------------------------------------

    @staticmethod
    def _normal(r, ch):
        # Am 펜타토닉 어두운 앰비언트 (~13초 루프)
        bass_a = [(110,500),(0,150),(110,350),(0,100),(82.4,600),(0,300),(98,400),(0,250)]
        bass_b = [(110,400),(0,100),(146.8,350),(0,100),(110,450),(0,150),(82.4,700),(0,300)]
        bass   = _seq(bass_a + bass_b + bass_a, 0.09, 'tri', r)

        mel_a  = [(220,800),(0,300),(261.6,600),(0,500),(196,600),(0,800),(0,600)]
        mel_b  = [(261.6,500),(0,300),(220,400),(0,200),(293.7,700),(0,400),(220,900),(0,700)]
        mel_c  = [(164.8,1000),(0,400),(220,600),(0,600),(196,800),(0,800)]
        mel    = _seq(mel_a + mel_b + mel_c, 0.05, 'sine', r)

        # 긴 지속 패드 + 옥타브 위 하모닉
        pad    = _seq([(110,5500),(0,200),(82.4,4000),(0,200),(98,3500)], 0.04, 'sine', r)
        harm   = _seq([(220,6000),(0,200),(196,5000),(0,200),(220,2000)], 0.025, 'sine', r)

        # 저음 드론 (saw로 따뜻함 추가)
        drone  = _seq([(55,13500)], 0.03, 'saw', r)

        return _wave(_mix(bass, mel, pad, harm, drone), ch)

    @staticmethod
    def _boss(r, ch):
        # 긴박한 보스 BGM (~8초 루프)
        pulse_a = [(110,100),(0,40),(155,100),(0,40)] * 8
        pulse_b = [(110,80),(0,30),(155,80),(0,30),(196,80),(0,30),(155,80),(0,30)] * 4
        bass    = _seq(pulse_a + pulse_b, 0.10, 'square', r)

        hrm_a   = [(220,90),(0,90),(233,90),(0,90)] * 8
        hrm_b   = [(220,70),(0,50),(261.6,70),(0,50),(220,70),(0,50),(196,70),(0,50)] * 4
        hrm     = _seq(hrm_a + hrm_b, 0.06, 'square', r)

        # saw 드론으로 위협감 강화
        drone   = _seq([(55,4000),(0,100),(58.3,4000)], 0.05, 'saw', r)

        # 고음 긴장 라인
        tens    = _seq([(440,200),(0,100),(466,200),(0,100)] * 10, 0.03, 'sine', r)

        return _wave(_mix(bass, hrm, drone, tens), ch)

    @staticmethod
    def _shop(r, ch):
        # C 장조 친근한 멜로디 (~9초 루프)
        mel_a  = [(262,400),(330,400),(392,400),(330,300),(262,600),(0,500),
                  (330,400),(392,400),(440,600),(0,400)]
        mel_b  = [(392,400),(440,400),(523,500),(0,300),(440,400),(392,400),
                  (330,600),(0,500),(262,800),(0,600)]
        mel    = _seq(mel_a + mel_b, 0.08, 'tri', r)

        bass_a = [(131,800),(0,400),(98,800),(0,400)]
        bass_b = [(131,600),(0,200),(147,600),(0,200),(131,1000),(0,400)]
        bass   = _seq(bass_a + bass_b + bass_a, 0.07, 'sine', r)

        # 따뜻한 saw 패드
        pad    = _seq([(262,2400),(0,200),(330,2400),(0,200),(392,2800),(0,200)], 0.03, 'saw', r)

        return _wave(_mix(mel, bass, pad), ch)

    @staticmethod
    def _menu(r, ch):
        # 극적인 메뉴 BGM (~12초 루프)
        mel_a  = [(220,500),(0,100),(220,350),(0,150),(262,600),(0,300),(196,800),(0,500)]
        mel_b  = [(220,400),(0,200),(261.6,400),(0,200),(293.7,500),(0,300),(220,700),(0,500)]
        mel_c  = [(246.9,600),(0,200),(220,500),(0,200),(196,700),(0,400),(165,1000),(0,600)]
        mel    = _seq(mel_a + mel_b + mel_c, 0.09, 'tri', r)

        bass_a = [(110,1200),(0,200),(82.4,1000),(0,200)]
        bass_b = [(98,1000),(0,200),(110,800),(0,200),(82.4,1200),(0,400)]
        bass   = _seq(bass_a + bass_b + bass_a, 0.08, 'sine', r)

        pad    = _seq([(165,4500),(0,200),(147,4500),(0,200),(165,3000)], 0.04, 'saw', r)

        # 고음 반짝임 레이어
        spark  = _seq([(660,300),(0,300),(660,200),(0,400),(523,500),(0,400),
                       (660,200),(0,700),(523,400),(0,900)], 0.03, 'sine', r)

        return _wave(_mix(mel, bass, pad, spark), ch)

    # ---- 공개 API ------------------------------------------------

    def play(self, name):
        # 페이드아웃 완료 시 대기 중인 트랙을 메인 스레드에서 시작
        if self._pending and not self._channel.get_busy():
            pending = self._pending
            self._pending = None
            self._current = pending
            s = self._sounds.get(pending)
            if s:
                self._channel.set_volume(self._vol)
                self._channel.play(s, loops=-1, fade_ms=self._FADE_MS)
            return

        if self._current == name or self._pending == name:
            return
        s = self._sounds.get(name)
        if not s:
            return

        if self._current is not None:
            # 현재 트랙 페이드아웃 후 대기 등록 (_update_bgm 매 프레임 호출로 완료 감지)
            self._channel.fadeout(self._FADE_MS)
            self._pending = name
            self._current = None
        else:
            self._current = name
            self._channel.set_volume(self._vol)
            self._channel.play(s, loops=-1, fade_ms=self._FADE_MS)

    def stop(self):
        self._pending = None
        self._current = None
        self._channel.fadeout(self._FADE_MS)

    def set_volume(self, vol):
        self._vol = max(0.0, min(1.0, vol))
        self._channel.set_volume(self._vol)


# ─────────────────────────────────────────────────────
#  SFX 매니저
# ─────────────────────────────────────────────────────
class AudioManager:
    # 각 SFX를 3가지 피치로 미리 생성해 재생 시 랜덤 선택
    _PITCH_VARIANTS = (0.92, 1.0, 1.08)

    def __init__(self):
        self.enabled   = False
        self._sounds: dict[str, list] = {}  # name -> [Sound, Sound, Sound]
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
            # 람다에 pitch factor p 전달 → freq 스케일링으로 피치 변형
            defs: dict[str, any] = {
                'attack':      lambda p: _square(440*p,70,rate=r) + _square(330*p,50,rate=r),
                'enemy_hit':   lambda p: _noise(60, 0.2, rate=r),
                'player_hit':  lambda p: _noise(90, 0.4, rate=r),
                'pickup':      lambda p: _sine(700*p,50,rate=r) + _sine(1050*p,70,rate=r),
                'levelup':     lambda p: _sine(440*p,70,rate=r)+_sine(550*p,70,rate=r)+_sine(660*p,100,rate=r),
                'use_item':    lambda p: _sine(500*p,100,rate=r),
                'stairs':      lambda p: _sine(330*p,50,rate=r)+_sine(440*p,50,rate=r)+_sine(550*p,80,rate=r),
                'boss_appear': lambda p: _noise(220,0.5,rate=r),
                'shop_open':   lambda p: _sine(800*p,50,rate=r)+_sine(1200*p,70,rate=r),
                'buy':         lambda p: _sine(600*p,60,rate=r)+_sine(900*p,80,rate=r),
                'no_gold':     lambda p: _square(200*p,120,rate=r),
                'skill_dash':  lambda p: _square(880*p,50,rate=r)+_square(660*p,40,rate=r),
                'skill_whirl': lambda p: _noise(120,0.35,rate=r),
                'skill_heal':  lambda p: _sine(528*p,100,rate=r)+_sine(660*p,120,rate=r),
                'death':       lambda p: _noise(80,0.5,rate=r)+_sine(200*p,100,rate=r)+_sine(150*p,150,rate=r),
                'save':        lambda p: _sine(440*p,40,rate=r)+_sine(550*p,40,rate=r),
                'teleport':    lambda p: _square(880*p,60,rate=r)+_square(660*p,60,rate=r)+_square(440*p,80,rate=r),
                'swing':       lambda p: _square(440*p,30,0.15,rate=r)+_square(330*p,40,0.10,rate=r),
                'crit':        lambda p: _square(200*p,40,0.40,rate=r)+_noise(60,0.25,rate=r)+_sine(1200*p,120,0.12,rate=r),
                'menu_select': lambda p: _square(440*p,50,0.12,rate=r),
                'menu_confirm':lambda p: _square(523*p,50,0.15,rate=r)+_square(659*p,80,0.15,rate=r),
            }
            for k, fn in defs.items():
                self._sounds[k] = [_wave(fn(p), ch) for p in self._PITCH_VARIANTS]
        except Exception:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        variants = self._sounds.get(name)
        if variants:
            try:
                s = random.choice(variants)
                ch = s.play()
                if ch:
                    ch.set_volume(self._sfx_vol)
            except Exception:
                pass

    def set_sfx_volume(self, vol):
        self._sfx_vol = max(0.0, min(1.0, vol))
        for variants in self._sounds.values():
            for s in variants:
                if s:
                    try:
                        s.set_volume(self._sfx_vol)
                    except Exception:
                        pass
