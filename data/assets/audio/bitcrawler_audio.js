/**
 * BitCrawler Audio System — Web Audio API
 * All sounds procedurally generated, no external files needed.
 * Usage: import or include this script, then call BitCrawlerAudio.play('attack')
 *
 * Source: Inspired by core/audio.py (math.sin + struct.pack 8-bit procedural approach)
 * Ported to Web Audio API AudioContext equivalent.
 */

const BitCrawlerAudio = (() => {
  let ctx = null;
  let masterGain = null;
  let sfxVol = 0.8;
  let bgmVol = 0.5;
  let bgmNode = null;
  let bgmType = null;

  function getCtx() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      masterGain = ctx.createGain();
      masterGain.gain.value = 1.0;
      masterGain.connect(ctx.destination);
    }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  // ── Core synth helpers ────────────────────────────────────────────────────

  function playTone({ freq = 440, type = 'square', duration = 0.15, volume = 0.3,
                       attack = 0.005, decay = 0.05, sustain = 0.6, release = 0.1,
                       freqEnd = null, detune = 0, delay = 0 }) {
    const c = getCtx();
    const t = c.currentTime + delay;
    const osc = c.createOscillator();
    const gain = c.createGain();
    const filter = c.createBiquadFilter();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    if (freqEnd !== null) osc.frequency.exponentialRampToValueAtTime(Math.max(1, freqEnd), t + duration);
    osc.detune.value = detune;

    filter.type = 'lowpass';
    filter.frequency.value = 4000;

    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(volume * sfxVol, t + attack);
    gain.gain.linearRampToValueAtTime(volume * sfxVol * sustain, t + attack + decay);
    gain.gain.setValueAtTime(volume * sfxVol * sustain, t + duration - release);
    gain.gain.linearRampToValueAtTime(0, t + duration);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);

    osc.start(t);
    osc.stop(t + duration + 0.01);
  }

  function playNoise({ duration = 0.1, volume = 0.2, cutoff = 800, attack = 0.001,
                        release = 0.08, delay = 0 }) {
    const c = getCtx();
    const t = c.currentTime + delay;
    const bufSize = c.sampleRate * duration;
    const buf = c.createBuffer(1, bufSize, c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;

    const src = c.createBufferSource();
    src.buffer = buf;

    const filter = c.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = cutoff;
    filter.Q.value = 1.5;

    const gain = c.createGain();
    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(volume * sfxVol, t + attack);
    gain.gain.linearRampToValueAtTime(0, t + duration);

    src.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);
    src.start(t);
  }

  // ── Sound definitions ─────────────────────────────────────────────────────

  const SOUNDS = {

    // ── Combat ──────────────────────────────────────────────────────────────
    attack() {
      // Sword swing — sharp high-frequency sweep
      playTone({ freq: 800, freqEnd: 200, type: 'sawtooth', duration: 0.12, volume: 0.25, attack: 0.002, decay: 0.03, sustain: 0.4, release: 0.06 });
      playNoise({ duration: 0.08, volume: 0.15, cutoff: 1200, attack: 0.001, release: 0.07 });
    },

    hit() {
      // Impact thud
      playTone({ freq: 180, freqEnd: 60, type: 'square', duration: 0.15, volume: 0.35, attack: 0.002, decay: 0.02, sustain: 0.3, release: 0.1 });
      playNoise({ duration: 0.06, volume: 0.2, cutoff: 400, attack: 0.001 });
    },

    crit() {
      // Critical hit — extra punch + high pitched ring
      playTone({ freq: 200, freqEnd: 50, type: 'square', duration: 0.18, volume: 0.45, attack: 0.001, decay: 0.02, sustain: 0.2, release: 0.12 });
      playNoise({ duration: 0.1, volume: 0.3, cutoff: 600, attack: 0.001 });
      playTone({ freq: 1200, freqEnd: 600, type: 'sine', duration: 0.3, volume: 0.15, attack: 0.01, decay: 0.05, sustain: 0.5, release: 0.2, delay: 0.02 });
    },

    player_hit() {
      // Player takes damage — deep thud + distress
      playTone({ freq: 120, freqEnd: 40, type: 'square', duration: 0.2, volume: 0.5, attack: 0.001, decay: 0.03, sustain: 0.2, release: 0.15 });
      playTone({ freq: 300, freqEnd: 150, type: 'sawtooth', duration: 0.15, volume: 0.2, attack: 0.005, decay: 0.05, sustain: 0.3, release: 0.1, delay: 0.02 });
      playNoise({ duration: 0.12, volume: 0.25, cutoff: 300, attack: 0.001 });
    },

    death() {
      // Dramatic descending death tone
      playTone({ freq: 220, freqEnd: 40, type: 'sawtooth', duration: 0.8, volume: 0.4, attack: 0.02, decay: 0.1, sustain: 0.6, release: 0.4 });
      playTone({ freq: 330, freqEnd: 60, type: 'square', duration: 0.6, volume: 0.25, attack: 0.03, decay: 0.1, sustain: 0.5, release: 0.3, delay: 0.1 });
      playTone({ freq: 110, freqEnd: 20, type: 'sine', duration: 1.2, volume: 0.3, attack: 0.05, decay: 0.2, sustain: 0.5, release: 0.6, delay: 0.2 });
      playNoise({ duration: 0.5, volume: 0.15, cutoff: 200, attack: 0.01, delay: 0.1 });
    },

    // ── Skills ──────────────────────────────────────────────────────────────
    skill_dash() {
      // Dash — rapid whoosh
      playTone({ freq: 400, freqEnd: 900, type: 'sawtooth', duration: 0.1, volume: 0.3, attack: 0.001, decay: 0.02, sustain: 0.5, release: 0.05 });
      playTone({ freq: 600, freqEnd: 1400, type: 'sine', duration: 0.12, volume: 0.2, attack: 0.001, decay: 0.02, sustain: 0.5, release: 0.05, delay: 0.02 });
      playNoise({ duration: 0.1, volume: 0.18, cutoff: 2000, attack: 0.001, release: 0.08 });
    },

    skill_whirl() {
      // Whirlwind — spinning multi-hit
      for (let i = 0; i < 4; i++) {
        playTone({ freq: 300 + i * 80, freqEnd: 150, type: 'sawtooth', duration: 0.12, volume: 0.2, attack: 0.002, decay: 0.02, sustain: 0.4, release: 0.07, delay: i * 0.04 });
        playNoise({ duration: 0.06, volume: 0.12, cutoff: 800, attack: 0.001, delay: i * 0.04 });
      }
    },

    skill_heal() {
      // Heal — gentle rising chime
      [523, 659, 784, 1047].forEach((freq, i) => {
        playTone({ freq, type: 'sine', duration: 0.4, volume: 0.18, attack: 0.02, decay: 0.05, sustain: 0.7, release: 0.25, delay: i * 0.08 });
      });
      playTone({ freq: 1200, freqEnd: 1600, type: 'sine', duration: 0.5, volume: 0.1, attack: 0.05, decay: 0.1, sustain: 0.5, release: 0.3, delay: 0.3 });
    },

    // ── Items ────────────────────────────────────────────────────────────────
    pickup() {
      // Item pickup — bright little jingle
      playTone({ freq: 600, type: 'square', duration: 0.06, volume: 0.2, attack: 0.002, decay: 0.01, sustain: 0.6, release: 0.04 });
      playTone({ freq: 800, type: 'square', duration: 0.06, volume: 0.2, attack: 0.002, decay: 0.01, sustain: 0.6, release: 0.04, delay: 0.07 });
      playTone({ freq: 1000, type: 'sine', duration: 0.1, volume: 0.15, attack: 0.005, decay: 0.02, sustain: 0.6, release: 0.06, delay: 0.14 });
    },

    use_item() {
      // Item use — satisfying pop
      playTone({ freq: 440, freqEnd: 220, type: 'sine', duration: 0.2, volume: 0.25, attack: 0.005, decay: 0.04, sustain: 0.5, release: 0.12 });
      playNoise({ duration: 0.05, volume: 0.1, cutoff: 1000, attack: 0.001, release: 0.04 });
    },

    levelup() {
      // Level up — triumphant ascending fanfare
      [[261, 0], [329, 0.1], [392, 0.2], [523, 0.3], [659, 0.4], [784, 0.5]].forEach(([freq, delay]) => {
        playTone({ freq, type: 'square', duration: 0.25, volume: 0.22, attack: 0.005, decay: 0.05, sustain: 0.6, release: 0.15, delay });
      });
      playTone({ freq: 1047, type: 'sine', duration: 0.6, volume: 0.2, attack: 0.02, decay: 0.1, sustain: 0.7, release: 0.35, delay: 0.6 });
    },

    // ── Navigation ──────────────────────────────────────────────────────────
    stairs() {
      // Floor transition — magical descending
      [880, 698, 523, 392].forEach((freq, i) => {
        playTone({ freq, type: 'sine', duration: 0.25, volume: 0.2, attack: 0.01, decay: 0.05, sustain: 0.6, release: 0.15, delay: i * 0.1 });
      });
      playNoise({ duration: 0.3, volume: 0.08, cutoff: 300, attack: 0.02, release: 0.25, delay: 0.1 });
    },

    shop_open() {
      // Shop bell
      playTone({ freq: 880, type: 'sine', duration: 0.4, volume: 0.2, attack: 0.01, decay: 0.05, sustain: 0.7, release: 0.3 });
      playTone({ freq: 1108, type: 'sine', duration: 0.35, volume: 0.15, attack: 0.01, decay: 0.05, sustain: 0.6, release: 0.25, delay: 0.05 });
      playTone({ freq: 1318, type: 'sine', duration: 0.4, volume: 0.12, attack: 0.01, decay: 0.05, sustain: 0.6, release: 0.3, delay: 0.1 });
    },

    buy() {
      // Purchase — coins clinking
      [1047, 1319, 1568].forEach((freq, i) => {
        playTone({ freq, type: 'sine', duration: 0.15, volume: 0.18, attack: 0.002, decay: 0.03, sustain: 0.5, release: 0.1, delay: i * 0.06 });
        playNoise({ duration: 0.04, volume: 0.08, cutoff: 2000, attack: 0.001, delay: i * 0.06 });
      });
    },

    no_gold() {
      // Error buzz
      playTone({ freq: 120, type: 'square', duration: 0.15, volume: 0.3, attack: 0.001, decay: 0.02, sustain: 0.5, release: 0.1 });
      playTone({ freq: 110, type: 'square', duration: 0.15, volume: 0.3, attack: 0.001, decay: 0.02, sustain: 0.5, release: 0.1, delay: 0.12 });
    },

    teleport() {
      // Teleport — sci-fi sweep
      playTone({ freq: 200, freqEnd: 2000, type: 'sine', duration: 0.3, volume: 0.25, attack: 0.01, decay: 0.05, sustain: 0.6, release: 0.15 });
      playTone({ freq: 2000, freqEnd: 200, type: 'sine', duration: 0.3, volume: 0.2, attack: 0.01, decay: 0.05, sustain: 0.6, release: 0.15, delay: 0.25 });
      playNoise({ duration: 0.4, volume: 0.15, cutoff: 1500, attack: 0.02, release: 0.3 });
    },

    save() {
      // Save — soft confirmation
      [392, 494, 587].forEach((freq, i) => {
        playTone({ freq, type: 'sine', duration: 0.2, volume: 0.15, attack: 0.01, decay: 0.03, sustain: 0.6, release: 0.12, delay: i * 0.07 });
      });
    },

    // ── Boss ────────────────────────────────────────────────────────────────
    boss_appear() {
      // Boss entrance — dramatic low rumble + high shriek
      playTone({ freq: 60, freqEnd: 30, type: 'sawtooth', duration: 1.5, volume: 0.5, attack: 0.05, decay: 0.2, sustain: 0.5, release: 0.8 });
      playTone({ freq: 80, type: 'square', duration: 1.2, volume: 0.3, attack: 0.03, decay: 0.1, sustain: 0.5, release: 0.6, delay: 0.1 });
      playTone({ freq: 2000, freqEnd: 800, type: 'sawtooth', duration: 0.8, volume: 0.2, attack: 0.001, decay: 0.1, sustain: 0.3, release: 0.5, delay: 0.5 });
      playNoise({ duration: 1.0, volume: 0.2, cutoff: 200, attack: 0.05, release: 0.8, delay: 0.2 });
    },

    // ── Menu ────────────────────────────────────────────────────────────────
    menu_select() {
      playTone({ freq: 440, type: 'square', duration: 0.08, volume: 0.15, attack: 0.002, decay: 0.01, sustain: 0.5, release: 0.05 });
    },

    menu_confirm() {
      playTone({ freq: 523, type: 'square', duration: 0.06, volume: 0.18, attack: 0.002, decay: 0.01, sustain: 0.5, release: 0.04 });
      playTone({ freq: 659, type: 'square', duration: 0.1, volume: 0.18, attack: 0.002, decay: 0.01, sustain: 0.5, release: 0.06, delay: 0.07 });
    },

    swing() {
      // Miss / air swing
      playTone({ freq: 500, freqEnd: 250, type: 'sine', duration: 0.1, volume: 0.12, attack: 0.002, decay: 0.02, sustain: 0.4, release: 0.06 });
      playNoise({ duration: 0.07, volume: 0.1, cutoff: 1500, attack: 0.001, release: 0.06 });
    },
  };

  // ── BGM layers ──────────────────────────────────────────────────────────
  // Procedural ambient BGM using oscillators + LFO modulation
  function startBGM(type) {
    if (bgmType === type) return;
    stopBGM();
    bgmType = type;

    const c = getCtx();
    const nodes = [];

    if (type === 'menu') {
      // Slow, mysterious drone — two detuned oscillators + slow LFO
      const drone1 = c.createOscillator();
      const drone2 = c.createOscillator();
      const lfo = c.createOscillator();
      const lfoGain = c.createGain();
      const gain1 = c.createGain();
      const gain2 = c.createGain();
      const masterBgm = c.createGain();

      drone1.type = 'sine'; drone1.frequency.value = 55;
      drone2.type = 'sine'; drone2.frequency.value = 82.4; // perfect fifth
      lfo.type = 'sine'; lfo.frequency.value = 0.15;
      lfoGain.gain.value = 8;

      gain1.gain.value = 0.08 * bgmVol;
      gain2.gain.value = 0.05 * bgmVol;
      masterBgm.gain.value = bgmVol;

      lfo.connect(lfoGain);
      lfoGain.connect(drone1.frequency);
      lfoGain.connect(drone2.frequency);

      drone1.connect(gain1); drone2.connect(gain2);
      gain1.connect(masterBgm); gain2.connect(masterBgm);
      masterBgm.connect(masterGain);

      drone1.start(); drone2.start(); lfo.start();
      nodes.push(drone1, drone2, lfo, gain1, gain2, lfoGain, masterBgm);

      // Add subtle high melodic note
      const melody = c.createOscillator();
      const melGain = c.createGain();
      melody.type = 'triangle'; melody.frequency.value = 220;
      melGain.gain.value = 0.03 * bgmVol;
      melody.connect(melGain); melGain.connect(masterBgm);
      melody.start();
      nodes.push(melody, melGain);

    } else if (type === 'normal') {
      // Dungeon ambience — low pulse + tension
      const pulse = c.createOscillator();
      const pulseGain = c.createGain();
      const lfo2 = c.createOscillator();
      const lfoG2 = c.createGain();
      const masterBgm = c.createGain();

      pulse.type = 'square'; pulse.frequency.value = 40;
      lfo2.type = 'sine'; lfo2.frequency.value = 0.4;
      lfoG2.gain.value = 0.03;

      pulseGain.gain.value = 0.06 * bgmVol;
      masterBgm.gain.value = bgmVol;

      lfo2.connect(lfoG2); lfoG2.connect(pulseGain.gain);
      pulse.connect(pulseGain);
      pulseGain.connect(masterBgm);
      masterBgm.connect(masterGain);
      pulse.start(); lfo2.start();
      nodes.push(pulse, pulseGain, lfo2, lfoG2, masterBgm);

      // Mid drone
      const drone = c.createOscillator();
      const droneGain = c.createGain();
      drone.type = 'sawtooth'; drone.frequency.value = 65;
      droneGain.gain.value = 0.04 * bgmVol;
      drone.connect(droneGain); droneGain.connect(masterBgm);
      drone.start();
      nodes.push(drone, droneGain);

    } else if (type === 'boss') {
      // Boss — intense low bass + dissonant harmonics
      const bass = c.createOscillator();
      const bassGain = c.createGain();
      const harm = c.createOscillator();
      const harmGain = c.createGain();
      const trem = c.createOscillator();
      const tremGain = c.createGain();
      const masterBgm = c.createGain();

      bass.type = 'sawtooth'; bass.frequency.value = 30;
      harm.type = 'square'; harm.frequency.value = 46.25; // tritone
      trem.type = 'sine'; trem.frequency.value = 4;
      tremGain.gain.value = 0.04;

      bassGain.gain.value = 0.1 * bgmVol;
      harmGain.gain.value = 0.06 * bgmVol;
      masterBgm.gain.value = bgmVol;

      trem.connect(tremGain); tremGain.connect(bassGain.gain);
      bass.connect(bassGain); harm.connect(harmGain);
      bassGain.connect(masterBgm); harmGain.connect(masterBgm);
      masterBgm.connect(masterGain);

      bass.start(); harm.start(); trem.start();
      nodes.push(bass, bassGain, harm, harmGain, trem, tremGain, masterBgm);

    } else if (type === 'shop') {
      // Shop — lighter, pleasant major key drone
      [261.6, 329.6, 392].forEach((freq, i) => {
        const osc = c.createOscillator();
        const gain = c.createGain();
        const masterBgm = c.createGain();
        osc.type = 'sine'; osc.frequency.value = freq;
        gain.gain.value = 0.04 * bgmVol;
        masterBgm.gain.value = bgmVol;
        osc.connect(gain); gain.connect(masterBgm); masterBgm.connect(masterGain);
        osc.start();
        nodes.push(osc, gain, masterBgm);
      });
    }

    bgmNode = nodes;
  }

  function stopBGM() {
    if (bgmNode) {
      bgmNode.forEach(n => { try { if (n.stop) n.stop(); if (n.disconnect) n.disconnect(); } catch(e){} });
      bgmNode = null;
      bgmType = null;
    }
  }

  // ── Public API ────────────────────────────────────────────────────────────
  return {
    play(name) {
      const fn = SOUNDS[name];
      if (fn) { try { fn(); } catch(e) { console.warn('BitCrawlerAudio: could not play', name, e); } }
      else console.warn('BitCrawlerAudio: unknown sound', name);
    },
    bgm: { play: startBGM, stop: stopBGM },
    setSfxVolume(v) { sfxVol = Math.max(0, Math.min(1, v)); },
    setBgmVolume(v) { bgmVol = Math.max(0, Math.min(1, v)); },
    sounds: Object.keys(SOUNDS),
  };
})();

// Export for module environments
if (typeof module !== 'undefined') module.exports = BitCrawlerAudio;
