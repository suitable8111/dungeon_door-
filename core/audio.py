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
                'boss':   self._boss(r, ch),
                'shop':   self._shop(r, ch),
            }
            # 테마 BGM — 20개 (50층 단위)
            _builders = [
                self._theme_0,  self._theme_1,  self._theme_2,  self._theme_3,
                self._theme_4,  self._theme_5,  self._theme_6,  self._theme_7,
                self._theme_8,  self._theme_9,  self._theme_10, self._theme_11,
                self._theme_12, self._theme_13, self._theme_14, self._theme_15,
                self._theme_16, self._theme_17, self._theme_18, self._theme_19,
            ]
            for i, fn in enumerate(_builders):
                self._sounds[f'theme_{i}'] = fn(r, ch)
        except Exception:
            pass

    # ── 공통 빌더 헬퍼 ──────────────────────────────────────────────
    @staticmethod
    def _amb(r, ch, bass_s, mel_s, pad_s, bw='tri', mw='sine', pw='sine',
             bv=0.08, mv=0.05, pv=0.035):
        """베이스+멜로디+패드 3레이어 앰비언트. 각 테마 BGM용."""
        b = _seq(bass_s, bv, bw, r)
        m = _seq(mel_s,  mv, mw, r)
        p = _seq(pad_s,  pv, pw, r)
        return _wave(_mix(b, m, p), ch)

    # ── 테마 BGM (0-19) ─────────────────────────────────────────────
    # 음계 기호 (Hz): A2=110, C3=131, D3=147, E3=165, F3=175, G3=196,
    #                 A3=220, B3=247, C4=262, D4=294, E4=330, G4=392

    @staticmethod
    def _theme_0(r, ch):
        """버려진 지하 감옥 — Am 어두운 앰비언트."""
        bass = _seq([(110,500),(0,150),(110,350),(0,100),(82.4,600),(0,300),(98,400),(0,250),
                     (110,400),(0,100),(146.8,350),(0,100),(110,450),(0,150),(82.4,700),(0,300)], 0.09,'tri',r)
        mel  = _seq([(220,800),(0,300),(261.6,600),(0,500),(196,600),(0,800),
                     (261.6,500),(0,300),(220,400),(0,200),(293.7,700),(0,400),(220,900),(0,700)], 0.05,'sine',r)
        pad  = _seq([(110,5500),(0,200),(82.4,4000),(0,200),(98,3500)], 0.04,'sine',r)
        return _wave(_mix(bass, mel, pad, _seq([(55,13500)],0.03,'saw',r)), ch)

    @staticmethod
    def _theme_1(r, ch):
        """곰팡이 핀 늪지대 — Dm 끈적한 saw."""
        bass = _seq([(73.4,600),(0,200),(87.3,500),(0,200),(110,500),(0,300),(87.3,700),(0,300)]*2, 0.09,'saw',r)
        mel  = _seq([(146.8,700),(0,400),(174.6,600),(0,500),(220,500),(0,400),
                     (196,600),(0,300),(174.6,800),(0,600),(146.8,900),(0,500)], 0.05,'tri',r)
        pad  = _seq([(73.4,4000),(0,300),(110,4500),(0,300),(87.3,4000)], 0.04,'saw',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_2(r, ch):
        """서리 내린 정적의 고성 — Cm 순수 sine, 결정 같은 정적."""
        bass = _seq([(65.4,1200),(0,600),(98,800),(0,500),(65.4,1000),(0,800),(82.4,1400),(0,600)], 0.07,'sine',r)
        mel  = _seq([(261.6,1200),(0,800),(311.1,900),(0,900),(392,700),(0,1200),
                     (349.2,800),(0,600),(261.6,1100),(0,1000)], 0.04,'sine',r)
        pad  = _seq([(65.4,6000),(0,400),(130.8,6000)], 0.045,'sine',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_3(r, ch):
        """타오르는 마그마 굴 — Em 빠른 square+saw, 공격적."""
        bass = _seq([(82.4,200),(0,80),(82.4,150),(0,80),(98,200),(0,80),(123.5,300),(0,120)]*4, 0.10,'square',r)
        mel  = _seq([(164.8,300),(0,150),(196,250),(0,150),(220,200),(0,100),(246.9,400),(0,200),
                     (220,300),(0,150),(196,200),(0,100),(164.8,500),(0,300)]*2, 0.06,'saw',r)
        pad  = _seq([(82.4,2000),(0,200),(123.5,2000),(0,200),(110,2500)]*2, 0.05,'saw',r)
        drone= _seq([(41.2,12000)], 0.04,'saw',r)
        return _wave(_mix(bass, mel, pad, drone), ch)

    @staticmethod
    def _theme_4(r, ch):
        """기계 장치의 무덤 — Bm 리드미컬 square, 기계음."""
        bass = _seq([(123.5,200),(0,100),(123.5,150),(0,150),(146.8,200),(0,100),(123.5,400),(0,200)]*4, 0.09,'square',r)
        mel  = _seq([(246.9,300),(0,200),(293.7,250),(0,200),(369.9,200),(0,100),(329.6,400),(0,300),
                     (246.9,250),(0,200),(220,350),(0,250),(246.9,600),(0,400)]*2, 0.05,'square',r)
        pad  = _seq([(123.5,3000),(0,300),(185,3000),(0,300),(110,3500)]*2, 0.04,'tri',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_5(r, ch):
        """환각의 보랏빛 숲 — F#m 몽환적 sine."""
        bass = _seq([(92.5,800),(0,400),(110,700),(0,500),(138.6,600),(0,600),(110,900),(0,500)]*2, 0.07,'sine',r)
        mel  = _seq([(185,1000),(0,500),(220,800),(0,600),(277.2,700),(0,700),(329.6,900),(0,600),
                     (277.2,800),(0,500),(220,1000),(0,700)], 0.05,'sine',r)
        pad  = _seq([(92.5,5000),(0,300),(138.6,5500),(0,300)], 0.045,'sine',r)
        harm = _seq([(185,6000),(0,400),(277.2,6000)], 0.025,'sine',r)
        return _wave(_mix(bass, mel, pad, harm), ch)

    @staticmethod
    def _theme_6(r, ch):
        """몰락한 성기사의 사원 — Dm 장중한 tri."""
        bass = _seq([(73.4,700),(0,300),(87.3,600),(0,300),(110,500),(0,400),(130.8,800),(0,400)]*2, 0.09,'tri',r)
        mel  = _seq([(146.8,800),(0,400),(174.6,700),(0,500),(220,600),(0,500),(233.1,800),(0,400),
                     (220,700),(0,500),(174.6,900),(0,600),(146.8,1000),(0,600)], 0.06,'tri',r)
        pad  = _seq([(73.4,4500),(0,300),(130.8,4000),(0,300),(110,4500)], 0.05,'tri',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_7(r, ch):
        """바람 부는 절벽 요새 — Am saw, 바람 느낌."""
        bass = _seq([(110,400),(0,200),(130.8,350),(0,200),(164.8,300),(0,150),(110,500),(0,250)]*3, 0.08,'saw',r)
        mel  = _seq([(220,500),(0,300),(261.6,400),(0,300),(293.7,350),(0,250),(329.6,450),(0,350),
                     (293.7,400),(0,300),(261.6,500),(0,400),(220,600),(0,400)]*2, 0.05,'saw',r)
        pad  = _seq([(110,3000),(0,200),(164.8,3500),(0,200),(196,3000)]*2, 0.04,'sine',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_8(r, ch):
        """저주받은 도서관 — Gm 불길한 tri."""
        bass = _seq([(98,800),(0,400),(116.5,700),(0,400),(146.8,600),(0,500),(174.6,900),(0,400)]*2, 0.08,'tri',r)
        mel  = _seq([(196,900),(0,500),(233.1,800),(0,600),(293.7,700),(0,600),(349.2,1000),(0,600),
                     (293.7,800),(0,500),(233.1,900),(0,600),(196,1100),(0,700)], 0.05,'tri',r)
        pad  = _seq([(98,5000),(0,400),(146.8,5000),(0,400)], 0.045,'sine',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_9(r, ch):
        """심해의 가라앉은 도시 — Cm 매우 느린 깊은 sine."""
        bass = _seq([(65.4,1500),(0,800),(98,1200),(0,800),(65.4,1800),(0,1000),(82.4,1500),(0,900)], 0.08,'sine',r)
        mel  = _seq([(130.8,1400),(0,1000),(155.6,1200),(0,1200),(196,1000),(0,1200),
                     (174.6,1300),(0,900),(130.8,1500),(0,1100)], 0.045,'sine',r)
        pad  = _seq([(65.4,7000),(0,500),(98,7000)], 0.05,'sine',r)
        drone= _seq([(32.7,14000)], 0.03,'sine',r)
        return _wave(_mix(bass, mel, pad, drone), ch)

    @staticmethod
    def _theme_10(r, ch):
        """전기 회로의 미로 — Bm 빠른 square, 전기 스파크."""
        bass = _seq([(123.5,150),(0,100),(185,120),(0,100),(123.5,150),(0,80),(246.9,200),(0,120)]*5, 0.09,'square',r)
        mel  = _seq([(246.9,200),(0,150),(369.9,180),(0,150),(440,160),(0,100),(369.9,250),(0,180),
                     (246.9,200),(0,150),(329.6,220),(0,170),(246.9,300),(0,200)]*2, 0.06,'square',r)
        pad  = _seq([(123.5,2500),(0,200),(185,2500),(0,200),(220,2500)]*2, 0.04,'saw',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_11(r, ch):
        """거대 곤충의 군집 — Em 불규칙 saw+noise."""
        bass = _seq([(82.4,300),(0,150),(98,250),(0,120),(123.5,200),(0,100),(82.4,400),(0,200)]*4, 0.09,'saw',r)
        mel  = _seq([(164.8,350),(0,200),(196,300),(0,200),(220,250),(0,150),(246.9,350),(0,250),
                     (220,300),(0,200),(196,350),(0,200),(164.8,500),(0,350)]*2, 0.05,'saw',r)
        pad  = _seq([(82.4,2000),(0,100),(110,2000),(0,100),(82.4,2500)]*2, 0.04,'tri',r)
        clk  = _seq([(1200,30),(0,170),(1100,25),(0,175)]*35, 0.02,'square',r)
        return _wave(_mix(bass, mel, pad, clk), ch)

    @staticmethod
    def _theme_12(r, ch):
        """황량한 붉은 사막 — Dm 프리지안 이국적."""
        bass = _seq([(73.4,600),(0,200),(77.8,500),(0,200),(87.3,500),(0,300),(110,700),(0,300)]*2, 0.09,'tri',r)
        mel  = _seq([(146.8,700),(0,400),(155.6,600),(0,400),(174.6,500),(0,400),(220,600),(0,400),
                     (261.6,700),(0,500),(220,600),(0,400),(174.6,800),(0,600)]*2, 0.05,'tri',r)
        pad  = _seq([(73.4,4500),(0,300),(110,4000),(0,300),(87.3,4500)], 0.045,'sine',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_13(r, ch):
        """연금술사의 실험실 — F#m 변칙 sine+saw, 실험적."""
        bass = _seq([(92.5,500),(0,200),(110,450),(0,250),(138.6,400),(0,200),(164.8,600),(0,300)]*3, 0.08,'sine',r)
        mel  = _seq([(185,600),(0,300),(207.7,500),(0,350),(220,400),(0,300),(277.2,700),(0,400),
                     (329.6,500),(0,350),(277.2,600),(0,400),(220,700),(0,500)]*2, 0.05,'saw',r)
        pad  = _seq([(92.5,3500),(0,300),(138.6,3500),(0,300),(185,4000)], 0.045,'sine',r)
        bub  = _seq([(600,60),(0,340),(900,50),(0,350),(750,55),(0,345)]*20, 0.02,'sine',r)
        return _wave(_mix(bass, mel, pad, bub), ch)

    @staticmethod
    def _theme_14(r, ch):
        """천공의 무너진 섬 — G 장조, 밝고 쓸쓸."""
        bass = _seq([(98,600),(0,300),(146.8,500),(0,300),(196,500),(0,350),(174.6,700),(0,350)]*2, 0.08,'tri',r)
        mel  = _seq([(196,700),(0,400),(220,600),(0,400),(246.9,500),(0,400),(293.7,700),(0,400),
                     (329.6,600),(0,500),(293.7,700),(0,400),(246.9,800),(0,600)]*2, 0.06,'sine',r)
        pad  = _seq([(98,4000),(0,300),(196,4500),(0,300),(174.6,4000)], 0.04,'sine',r)
        harm = _seq([(392,3500),(0,400),(440,3500),(0,400),(392,3500)], 0.025,'sine',r)
        return _wave(_mix(bass, mel, pad, harm), ch)

    @staticmethod
    def _theme_15(r, ch):
        """그림자의 영역 — Am 극도로 어두운 드론."""
        bass = _seq([(55,2000),(0,1000),(82.4,1500),(0,1200),(55,2500),(0,1200)], 0.08,'sine',r)
        mel  = _seq([(220,1500),(0,2000),(261.6,1200),(0,2500),(196,1800),(0,2200),
                     (0,2000),(164.8,1000),(0,2500)], 0.04,'sine',r)
        pad  = _seq([(55,8000),(0,500),(82.4,8000)], 0.06,'sine',r)
        drone= _seq([(27.5,16000)], 0.03,'sine',r)
        return _wave(_mix(bass, mel, pad, drone), ch)

    @staticmethod
    def _theme_16(r, ch):
        """핏빛 달의 성소 — Dm 박동 square, 흡혈."""
        bass = _seq([(73.4,300),(0,150),(73.4,200),(0,350),(87.3,300),(0,200),(110,400),(0,200)]*4, 0.10,'square',r)
        mel  = _seq([(146.8,400),(0,250),(174.6,350),(0,250),(207.7,300),(0,200),(220,450),(0,300),
                     (207.7,350),(0,250),(174.6,400),(0,300),(146.8,550),(0,400)]*2, 0.06,'square',r)
        pad  = _seq([(73.4,2500),(0,200),(110,2500),(0,200),(87.3,3000)]*2, 0.05,'saw',r)
        return _wave(_mix(bass, mel, pad), ch)

    @staticmethod
    def _theme_17(r, ch):
        """왜곡된 시공간의 틈 — 불협화음, 뒤틀린."""
        bass = _seq([(123.5,500),(0,200),(130.8,450),(0,200),(185,400),(0,250),(174.6,600),(0,300)]*3, 0.08,'saw',r)
        mel  = _seq([(246.9,600),(0,400),(261.6,500),(0,350),(369.9,400),(0,300),(349.2,600),(0,400),
                     (440,500),(0,350),(415.3,550),(0,400),(329.6,700),(0,500)]*2, 0.05,'sine',r)
        pad  = _seq([(185,4000),(0,300),(174.6,4000),(0,300),(246.9,4500)], 0.04,'saw',r)
        dist = _seq([(55,3000),(0,500),(58.3,3000),(0,500),(51.9,3500)]*2, 0.03,'saw',r)
        return _wave(_mix(bass, mel, pad, dist), ch)

    @staticmethod
    def _theme_18(r, ch):
        """고대 신의 무덤 — Am 고대 드론, 장엄."""
        bass = _seq([(55,2500),(0,800),(82.4,2000),(0,1000),(55,3000),(0,800),(73.4,2000),(0,1200)], 0.09,'tri',r)
        mel  = _seq([(220,1800),(0,1000),(261.6,1500),(0,1200),(392,1200),(0,1500),
                     (349.2,1400),(0,1000),(261.6,1800),(0,1200)], 0.05,'tri',r)
        pad  = _seq([(55,8000),(0,500),(110,8000)], 0.06,'sine',r)
        drone= _seq([(55,16000)], 0.04,'saw',r)
        return _wave(_mix(bass, mel, pad, drone), ch)

    @staticmethod
    def _theme_19(r, ch):
        """차원의 끝 (The Void) — 허무, 코스믹 공포."""
        bass = _seq([(55,4000),(0,2000),(41.2,4000),(0,2000),(55,3000),(0,2500)], 0.07,'sine',r)
        mel  = _seq([(0,3000),(440,600),(0,4000),(523.3,500),(0,3500),(329.6,700),(0,4000)], 0.03,'sine',r)
        pad  = _seq([(55,10000),(0,1000),(41.2,10000)], 0.05,'sine',r)
        void = _seq([(27.5,21000)], 0.04,'saw',r)
        return _wave(_mix(bass, mel, pad, void), ch)

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
