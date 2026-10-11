#!/usr/bin/env python3
"""
YouTube Timer – Professional Countdown Timer with Synthesized Sounds
Designed for YouTube Videos, Shorts, and Streams
Features:
- Live 16:9 Video Preview with animated overlay
- Comprehensive Timer Presets (3s to 3hrs)
- 4 Sound Themes: Default, Psychedelic, Cosmic Space, Cyberpunk Glitch
Install:  pip install PySide6 numpy
Run:      python app.py
"""
import sys, os, shutil, tempfile, wave, math
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QGroupBox, QGridLayout, QCheckBox,
    QSizePolicy, QSlider, QComboBox,
)
from PySide6.QtCore import QTimer, Qt, QUrl, QRect, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QShortcut, QKeySequence, QLinearGradient, QConicalGradient
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# ═══════════════════════════════════════════════════════════════════
#  SOUND SYNTHESIZER — Pure Math → WAV (Multi-Theme)
# ═══════════════════════════════════════════════════════════════════
class SoundEngine:
    SR = 44100
    _dir = None
    _files = {}
    current_theme = "default"

    @classmethod
    def init(cls, theme="default"):
        cls._dir = tempfile.mkdtemp(prefix="yt_timer_")
        cls.set_theme(theme)

    @classmethod
    def set_theme(cls, theme):
        cls.current_theme = theme
        generators = cls.THEMES.get(theme, cls.THEMES["default"])
        for name, gen in generators.items():
            p = os.path.join(cls._dir, f"{name}.wav")
            cls._wav(p, gen())
            cls._files[name] = p

    @classmethod
    def path(cls, name): return cls._files.get(name)

    @classmethod
    def cleanup(cls):
        if cls._dir and os.path.isdir(cls._dir):
            shutil.rmtree(cls._dir, ignore_errors=True)

    @staticmethod
    def _wav(path, data):
        with wave.open(path, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SoundEngine.SR)
            w.writeframes(data.tobytes())

    @staticmethod
    def _to16(sig): return (np.clip(sig, -1, 1) * 32767).astype(np.int16)

    @staticmethod
    def _chirp(t, f0, f1):
        k = (f1 - f0) / (t[-1] - t[0] + 1e-9)
        return 2 * np.pi * (f0 * t + 0.5 * k * t**2)

    @staticmethod
    def _fm(t, fc, fm, idx): return 2 * np.pi * fc * t + idx * np.sin(2 * np.pi * fm * t)

    @staticmethod
    def _noise(duration): return np.random.randn(int(SoundEngine.SR * duration))

    @staticmethod
    def _bitcrush(sig, levels=4): return np.round(sig * levels) / levels

    @staticmethod
    def _normalize(sig, peak=0.90):
        """Normalize signal to a target peak amplitude."""
        mx = np.max(np.abs(sig))
        if mx < 1e-9: return sig
        return sig * (peak / mx)

    @staticmethod
    def _flanger(sig, rate_hz=0.4, max_delay_sec=0.003, feedback=0.35):
        """Feedback flanger — modulated comb filter for psychedelic phasing."""
        sr = SoundEngine.SR; n = len(sig)
        t = np.linspace(0, n / sr, n, False)
        delay_n = (max_delay_sec * sr * (0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t))).astype(int)
        delay_n = np.maximum(delay_n, 1)  # avoid zero-delay feedback
        out = sig.copy()
        start = int(np.max(delay_n)) + 1
        for i in range(start, n):
            d = delay_n[i]
            if i - d >= 0:
                out[i] += out[i - d] * feedback
        return np.clip(out, -1, 1)

    @staticmethod
    def _echo(sig, delays_amps=None):
        """Add discrete echoes (simple multi-tap delay)."""
        sr = SoundEngine.SR; n = len(sig)
        out = sig.copy()
        if delays_amps is None:
            delays_amps = [(0.05, 0.35), (0.11, 0.25), (0.19, 0.15), (0.31, 0.08)]
        for delay_s, amp in delays_amps:
            dn = int(delay_s * sr)
            if dn < n:
                out[dn:] += sig[:-dn] * amp
        return np.clip(out, -1, 1)

    # ── DEFAULT THEME ──────────────────────────────────────────────
    @staticmethod
    def _def_tick():
        sr, d = SoundEngine.SR, 0.04; t = np.linspace(0, d, int(sr*d), False)
        sig = (0.50*np.sin(2*np.pi*2000*t) + 0.30*np.sin(2*np.pi*4000*t) + 0.15*np.sin(2*np.pi*6000*t))
        return SoundEngine._to16(sig * np.exp(-t*200)*0.35)

    @staticmethod
    def _def_minute():
        sr, d = SoundEngine.SR, 0.50; t = np.linspace(0, d, int(sr*d), False)
        sig = (0.40*np.sin(2*np.pi*1047*t) + 0.30*np.sin(2*np.pi*1319*t) + 0.20*np.sin(2*np.pi*1568*t))
        env = np.exp(-t*6); env[:int(0.003*sr)] = np.linspace(0,1,int(0.003*sr))
        return SoundEngine._to16(sig * env * 0.45)

    @staticmethod
    def _def_hour():
        sr, d = SoundEngine.SR, 1.0; t = np.linspace(0, d, int(sr*d), False)
        sig = (0.35*np.sin(2*np.pi*262*t) + 0.25*np.sin(2*np.pi*330*t) + 0.20*np.sin(2*np.pi*392*t) + 0.15*np.sin(2*np.pi*523*t))
        env = np.exp(-t*2.5); env[:int(0.005*sr)] = np.linspace(0,1,int(0.005*sr))
        return SoundEngine._to16(sig * env * 0.50)

    @staticmethod
    def _def_complete():
        sr, d = SoundEngine.SR, 2.0; t = np.linspace(0, d, int(sr*d), False); sig = np.zeros_like(t)
        beep, gap = int(0.15*sr), int(0.12*sr)
        for i, f in enumerate([880, 1109, 1319, 1760]):
            p = i*(beep+gap)
            if p+beep > len(t): break
            bt = t[p:p+beep]; b = np.sin(2*np.pi*f*bt)*np.exp(-bt*12)*0.55
            b[:int(0.005*sr)] *= np.linspace(0,1,int(0.005*sr)); sig[p:p+beep] = b
        return SoundEngine._to16(sig)

    @staticmethod
    def _def_warning():
        sr, d = SoundEngine.SR, 0.08; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(np.sin(2*np.pi*880*t)*np.exp(-t*30)*0.40)

    @staticmethod
    def _def_last3():
        sr, d = SoundEngine.SR, 0.12; t = np.linspace(0, d, int(sr*d), False)
        sig = (np.sin(2*np.pi*1175*t) + 0.3*np.sin(2*np.pi*2350*t))
        return SoundEngine._to16(sig * np.exp(-t*15)*0.50)

    # ── PSYCHEDELIC THEME (dramatically improved) ──────────────────
    @staticmethod
    def _psy_tick():
        """Crystal Sparkle — cascaded FM bell with beating shimmer."""
        sr = SoundEngine.SR; d = 0.10; t = np.linspace(0, d, int(sr*d), False)
        # Three-stage cascaded FM → rich inharmonic bell spectrum
        mod1 = np.sin(2*np.pi*67.3*t) * 7.0
        mod2 = np.sin(2*np.pi*131.6*t + mod1) * 4.0
        carrier = np.sin(2*np.pi*1046.5*t + mod2)            # ≈C6
        # Beating high pair for crystalline shimmer (2 Hz beat)
        shimmer = 0.25*(np.sin(2*np.pi*2093*t) + np.sin(2*np.pi*2095*t))
        # Inharmonic partial (≈10:7 ratio → metallic)
        metal = 0.15 * np.sin(2*np.pi*1496*t + mod1*0.3)
        env = np.exp(-t*50)
        sig = (carrier + shimmer + metal) * env * 0.38
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.85))

    @staticmethod
    def _psy_minute():
        """Phase Morph — detuned harmonic stack with flanger & waveshaping."""
        sr = SoundEngine.SR; d = 1.5; n = int(sr*d); t = np.linspace(0, d, n, False)
        # Detuned harmonic stack → beating across all partials
        base = np.zeros(n)
        for f, a in [(110,.25),(110.6,.23),(165,.18),(165.8,.16),
                      (220,.13),(221.2,.11),(330,.07),(331.5,.05)]:
            base += a * np.sin(2*np.pi*f*t)
        # Time-varying FM for timbre morphing
        fm_idx = 5*np.sin(2*np.pi*0.35*t)
        fm = np.sin(2*np.pi*110*t + fm_idx*np.sin(2*np.pi*7.3*t))
        combined = 0.6*base + 0.4*fm
        # Waveshaping (tanh soft-clip) → harmonic enrichment
        shaped = np.tanh(combined * 2.0) * 0.5
        # Flanger for psychedelic phasing
        flanged = SoundEngine._flanger(shaped, rate_hz=0.4, max_delay_sec=0.003, feedback=0.35)
        # Envelope
        env = np.ones(n)
        att = int(0.06*sr); env[:att] = np.linspace(0,1,att)**2
        rel = int(0.4*sr);  env[-rel:] = np.linspace(1,0,rel)**0.7
        # Filtered-noise texture
        noise = np.convolve(SoundEngine._noise(d), np.ones(120)/120, mode='same')
        sig = flanged * env * 0.40 + noise * env * 0.03
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.85))

    @staticmethod
    def _psy_hour():
        """Sacred Drone — deep subharmonic beating, overtone series & pitch drift."""
        sr = SoundEngine.SR; d = 4.0; n = int(sr*d); t = np.linspace(0, d, n, False)
        # Layer 1 — deep beating sub-bass (0.25 Hz pulse)
        sub = 0.35*(np.sin(2*np.pi*55*t) + np.sin(2*np.pi*55.25*t))
        # Layer 2 — natural harmonic series with detuned beating pairs
        harmonics = np.zeros(n)
        for h, (f, a) in enumerate([(110,.30),(220,.22),(330,.15),(440,.10),
                                      (550,.07),(660,.05),(880,.03)]):
            det = 0.3*(h+1)
            harmonics += a * np.sin(2*np.pi*(f+det)*t)
            harmonics += a * 0.6 * np.sin(2*np.pi*(f-det*0.5)*t)
        # Layer 3 — slowly wandering pitch via LFO
        drift_f = 220 + 25*np.sin(2*np.pi*0.07*t) + 12*np.sin(2*np.pi*0.19*t)
        drift = 0.18 * np.sin(2*np.pi*np.cumsum(drift_f)/sr)
        sig = sub + harmonics + drift
        # Flanger for slow psychedelic sweep
        sig = SoundEngine._flanger(sig, rate_hz=0.12, max_delay_sec=0.005, feedback=0.30)
        # Envelope — long fade in/out
        env = np.ones(n)
        att = int(0.8*sr);  env[:att] = np.linspace(0,1,att)**1.5
        rel = int(1.5*sr);  env[-rel:] = np.linspace(1,0,rel)**1.5
        sig = np.tanh(sig * 1.5) * env * 0.40
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.88))

    @staticmethod
    def _psy_warning():
        """Kaleidoscope Alert — rising FM chirp with ring-mod edge."""
        sr = SoundEngine.SR; d = 0.25; t = np.linspace(0, d, int(sr*d), False)
        # Ascending FM chirp
        phase = SoundEngine._chirp(t, 500, 1800)
        fm = 10*np.sin(2*np.pi*30*t) * np.exp(-t*8)
        sig = np.sin(phase + fm)
        # Ring modulation for metallic bite
        ring = sig * np.sin(2*np.pi*415*t)
        sig = 0.55*sig + 0.45*ring
        # Secondary FM layer
        sig += 0.2 * np.sin(SoundEngine._fm(t, 2500, 18, 6)) * np.exp(-t*12)
        env = (1 - np.exp(-t*500)) * np.exp(-t*6)
        sig = sig * env * 0.45
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.85))

    @staticmethod
    def _psy_last3():
        """Reverse Descent — backwards-feeling spectral warp with rotating harmonics."""
        sr = SoundEngine.SR; d = 0.30; n = int(sr*d); t = np.linspace(0, d, n, False)
        # Descending chirp
        phase = SoundEngine._chirp(t, 2800, 300)
        # Spectral rotation: harmonic amplitudes spin at different rates
        spin1 = np.sin(2*np.pi*14*t)
        spin2 = np.cos(2*np.pi*14*t)
        sig = (np.sin(phase)        * (0.5 + 0.5*spin1) +
               0.4*np.sin(2*phase)  * (0.5 - 0.5*spin1) +
               0.2*np.sin(3*phase)  * (0.5 + 0.5*spin2) +
               0.1*np.sin(4*phase)  * (0.5 - 0.5*spin2))
        # Reverse-attack envelope — builds up then cuts (psychedelic backwards feel)
        env_rev = (t/d)**2.5                         # ramps UP
        env_rev *= (1 - np.exp(-t*400))              # tiny click-prevention
        # Small fade-out at the very end to avoid clip
        fade = int(0.008*sr)
        env_rev[-fade:] *= np.linspace(1, 0, fade)
        # Blend 60% reverse + 40% normal decay for body
        env_norm = np.exp(-t*8) * (1 - np.exp(-t*300))
        env = 0.6*env_rev + 0.4*env_norm
        sig = sig * env * 0.48
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.88))

    @staticmethod
    def _psy_complete():
        """Ego Dissolution — Shepard-Risset glissando, FM droplets & shimmer."""
        sr = SoundEngine.SR; d = 5.0; n = int(sr*d); t = np.linspace(0, d, n, False)
        sig = np.zeros(n)

        # ── Layer 1: Shepard-Risset rising glissando ──
        shepard_fund = 55.0
        for octave in range(6):
            f = shepard_fund * (2**octave)
            phase = SoundEngine._chirp(t, f, 2*f)
            freq_at_t = f + f * t / d   # current frequency
            # Gaussian loudness centred on mid-range
            amp = np.exp(-0.5*((np.log2(np.maximum(freq_at_t,1)) - np.log2(440))/1.3)**2)
            sig += 0.10 * np.sin(phase) * amp

        # ── Layer 2: Beating harmonic shimmer (delayed onset) ──
        for f_base, beat_hz in [(880,1.5),(1320,2.0),(1760,2.5),(660,1.0)]:
            shimmer_env = np.sin(np.pi*t/d)**0.5
            onset = int(0.5*sr); shimmer_env[:onset] *= np.linspace(0,1,onset)**2
            sig += 0.05*(np.sin(2*np.pi*f_base*t) + np.sin(2*np.pi*(f_base+beat_hz)*t)) * shimmer_env

        # ── Layer 3: Cascading FM droplets ──
        for i in range(12):
            delay = 0.2 + i*0.32; delay_s = int(delay*sr)
            tone_len = int(0.9*sr)
            if delay_s + tone_len > n: break
            tt = np.linspace(0, 0.9, tone_len, False)
            fc = 250 + i*55; fm_f = 4 + i*1.5; fm_i = 3 + i*0.6
            droplet = np.sin(SoundEngine._fm(tt, fc, fm_f, fm_i))
            droplet += 0.5*np.sin(SoundEngine._chirp(tt, fc*2, fc*0.8))
            drop_env = np.exp(-tt*2.5) * (1 - np.exp(-tt*40))
            sig[delay_s:delay_s+tone_len] += 0.06*droplet*drop_env

        # ── Layer 4: Reverse-cymbal noise swell (first 0.6s) ──
        cym_len = int(0.6*sr)
        cym_noise = np.diff(SoundEngine._noise(0.6), prepend=0)  # high-pass
        cym_env = (np.linspace(0, 1, cym_len))**3
        sig[:cym_len] += cym_noise * cym_env * 0.12

        # Master envelope
        env = np.ones(n)
        att = int(0.15*sr); env[:att] = np.linspace(0,1,att)**2
        rel = int(1.5*sr);  env[-rel:] = np.linspace(1,0,rel)**2

        sig = np.tanh(sig * env * 2.0) * 0.50
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.92))

    # ── COSMIC SPACE THEME (improved) ──────────────────────────────
    @staticmethod
    def _cos_tick():
        sr, d = SoundEngine.SR, 0.07; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16((np.sin(2*np.pi*4500*t) + 0.5*np.sin(2*np.pi*6000*t))*np.exp(-t*80)*0.3)

    @staticmethod
    def _cos_minute():
        sr, d = SoundEngine.SR, 0.7; t = np.linspace(0, d, int(sr*d), False)
        phase = SoundEngine._chirp(t, 300, 1200)
        return SoundEngine._to16(np.sin(SoundEngine._fm(t,0,8,6)+phase)*np.exp(-t*3)*0.5)

    @staticmethod
    def _cos_hour():
        sr, d = SoundEngine.SR, 2.0; t = np.linspace(0, d, int(sr*d), False)
        base = np.sin(2*np.pi*220*t)*np.exp(-t*4); sig = base.copy()
        for ds, v in [(0.15,0.6),(0.35,0.3),(0.6,0.15),(0.9,0.05)]:
            sh = int(ds*sr); sig[sh:] += base[:-sh]*v
        return SoundEngine._to16(sig*0.5)

    @staticmethod
    def _cos_warning():
        sr, d = SoundEngine.SR, 0.2; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(np.sin(2*np.pi*1200*t)*np.exp(-t*10)*0.4)

    @staticmethod
    def _cos_last3():
        sr, d = SoundEngine.SR, 0.15; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(np.sin(2*np.pi*80*t)*(0.5+0.5*np.sin(2*np.pi*20*t))*np.exp(-t*10)*0.5)

    @staticmethod
    def _cos_complete():
        """Vast cosmic expanse — rising sweep with deep echo/reverb space."""
        sr = SoundEngine.SR; d = 3.0; n = int(sr*d); t = np.linspace(0, d, n, False)
        # Rising sweep
        sweep = np.sin(SoundEngine._chirp(t, 80, 3000)) * (1-t/d) * 0.45
        # Deep sub-bass pad
        sub = 0.3 * np.sin(2*np.pi*40*t) * np.exp(-t*0.8)
        # Shimmering high overtones
        shimmer = 0.08*(np.sin(2*np.pi*6000*t) + 0.7*np.sin(2*np.pi*8000*t)) * np.exp(-t*1.5)
        sig = sweep + sub + shimmer
        # Add noise texture
        noise = SoundEngine._noise(d)
        noise_lp = np.convolve(noise, np.ones(200)/200, mode='same')
        sig += noise_lp * np.exp(-t*2) * 0.20
        # Echo for vast space feel
        sig = SoundEngine._echo(sig, [(0.08,0.35),(0.17,0.25),(0.30,0.18),(0.48,0.10),(0.72,0.06)])
        # Envelope
        env = np.ones(n)
        att = int(0.1*sr); env[:att] = np.linspace(0,1,att)
        rel = int(0.8*sr); env[-rel:] = np.linspace(1,0,rel)**1.5
        sig = sig * env
        return SoundEngine._to16(SoundEngine._normalize(sig, 0.88))

    # ── CYBERPUNK GLITCH THEME (improved) ──────────────────────────
    @staticmethod
    def _gl_tick():
        sr, d = SoundEngine.SR, 0.03; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(SoundEngine._bitcrush(np.sin(2*np.pi*1500*t), 3)*np.exp(-t*100)*0.4)

    @staticmethod
    def _gl_minute():
        sr, d = SoundEngine.SR, 0.4; t = np.linspace(0, d, int(sr*d), False); sig = np.zeros_like(t)
        step = int(0.1*sr)
        for i, f in enumerate([440, 550, 660, 880]):
            st = i*step
            if st+step > len(t): break
            sig[st:st+step] = np.sign(np.sin(2*np.pi*f*t[st:st+step]))
        return SoundEngine._to16(sig*0.3)

    @staticmethod
    def _gl_hour():
        sr, d = SoundEngine.SR, 1.0; t = np.linspace(0, d, int(sr*d), False)
        snip = np.sin(2*np.pi*300*t[:int(0.1*sr)])*np.exp(-t[:int(0.1*sr)]*15); sig = np.zeros_like(t)
        for i in range(10):
            st = int(i*0.1*sr)
            if st+len(snip) > len(t): break
            sig[st:st+len(snip)] += snip*(1.0-(i*0.05))
        return SoundEngine._to16(sig*0.4)

    @staticmethod
    def _gl_warning():
        sr, d = SoundEngine.SR, 0.1; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(np.sign(np.sin(2*np.pi*1000*t))*np.exp(-t*30)*0.3)

    @staticmethod
    def _gl_last3():
        sr, d = SoundEngine.SR, 0.12; t = np.linspace(0, d, int(sr*d), False)
        return SoundEngine._to16(SoundEngine._bitcrush(SoundEngine._noise(d)*np.exp(-t*15)*0.3, 6))

    @staticmethod
    def _gl_complete():
        """Glitchstorm — rhythmic digital stutters with bitcrush & data corruption."""
        sr = SoundEngine.SR; d = 2.5; n = int(sr*d); t = np.linspace(0, d, n, False)
        sig = np.zeros(n)
        # Rhythmic square-wave stutters at increasing density
        for i in range(20):
            st = int(i*0.12*sr); ln = int((0.06 + 0.02*np.random.random())*sr)
            if st+ln > n: break
            tt = t[st:st+ln]; f = np.random.choice([200,300,500,800,1200,1600,2000])
            burst = np.sign(np.sin(2*np.pi*f*tt))
            # Some bursts are pitch-shifted copies
            if np.random.random() > 0.5:
                burst = np.sign(np.sin(2*np.pi*f*1.5*tt))
            env = np.exp(-tt*20) * (1-np.exp(-tt*200))
            sig[st:st+ln] += burst * env * 0.3
        # Add corrupted noise stutters
        for i in range(8):
            st = int((0.5+i*0.22)*sr); ln = int(0.04*sr)
            if st+ln > n: break
            sig[st:st+ln] += SoundEngine._bitcrush(np.random.randn(ln), 3) * 0.2
        # Bitcrush the whole thing
        sig = SoundEngine._bitcrush(sig, 10) * (1-t/d)**0.5
        return SoundEngine._to16(SoundEngine._normalize(sig * 0.5, 0.85))

    THEMES = {
        "default": {"tick": _def_tick, "minute": _def_minute, "hour": _def_hour, "complete": _def_complete, "warning": _def_warning, "last3": _def_last3},
        "psychedelic": {"tick": _psy_tick, "minute": _psy_minute, "hour": _psy_hour, "complete": _psy_complete, "warning": _psy_warning, "last3": _psy_last3},
        "cosmic": {"tick": _cos_tick, "minute": _cos_minute, "hour": _cos_hour, "complete": _cos_complete, "warning": _cos_warning, "last3": _cos_last3},
        "glitch": {"tick": _gl_tick, "minute": _gl_minute, "hour": _gl_hour, "complete": _gl_complete, "warning": _gl_warning, "last3": _gl_last3},
    }


# ═══════════════════════════════════════════════════════════════════
#  WIDGETS: Circular Timer, Video Preview, Presentation
# ═══════════════════════════════════════════════════════════════════
class CircularTimer(QWidget):
    COLORS = {"idle": QColor(120,120,120), "running": QColor(46,204,113), "warning": QColor(243,156,18), "critical": QColor(231,76,60), "done": QColor(52,152,219)}
    LABELS = {"idle": "READY", "running": "RUNNING", "warning": "WARNING", "critical": "FINAL", "done": "COMPLETE"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress, self.time_text, self.state, self.pulse_on = 1.0, "00:00", "idle", False
        self.visual_theme = "default"
        self._hue_counter = 0
        self.setMinimumSize(240, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._anim = QTimer(self); self._anim.timeout.connect(self._animate); self._anim.start(50)

    def _animate(self):
        self._hue_counter = (self._hue_counter + 3) % 360
        if self.visual_theme == "psychedelic" and self.state in ("running","warning","critical"):
            self.update()

    def paintEvent(self, event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height(); side = min(w, h)
            ox, oy = (w-side)//2, (h-side)//2

            # Choose arc colour (rainbow for psychedelic)
            if self.visual_theme == "psychedelic" and self.state in ("running","warning","critical","done"):
                hue = self._hue_counter
                color = QColor.fromHsv(hue % 360, 255, 230)
            else:
                color = QColor(self.COLORS.get(self.state, self.COLORS["idle"]))
            if self.state == "done" and self.pulse_on: color.setAlpha(140)

            pen1 = QPen(QColor(55, 55, 55), 10); pen1.setCapStyle(Qt.RoundCap)
            p.setPen(pen1)
            m = 22; r = QRect(ox+m, oy+m, side-2*m, side-2*m); p.drawArc(r, 0, 360*16)

            # For psychedelic: draw rainbow arc segments
            if self.visual_theme == "psychedelic" and self.state in ("running","warning","critical","done"):
                total_deg = int(self.progress * 360)
                seg = max(1, total_deg // 36)
                for i in range(0, total_deg, seg):
                    hue = (self._hue_counter + i * 4) % 360
                    seg_color = QColor.fromHsv(hue, 255, 230)
                    pen_r = QPen(seg_color, 10); pen_r.setCapStyle(Qt.RoundCap)
                    p.setPen(pen_r)
                    start_angle = 90*16 - i*16
                    p.drawArc(r, start_angle, -seg*16)
            else:
                pen2 = QPen(color, 10); pen2.setCapStyle(Qt.RoundCap); p.setPen(pen2)
                p.drawArc(r, 90*16, -int(self.progress*360*16))

            im = m + 12; p.setPen(Qt.NoPen); p.setBrush(QColor(32,32,32))
            p.drawEllipse(QRect(ox+im, oy+im, side-2*im, side-2*im))

            # Text colour follows theme
            if self.visual_theme == "psychedelic" and self.state in ("running","warning","critical"):
                text_color = QColor.fromHsv((self._hue_counter + 180) % 360, 200, 255)
            else:
                text_color = color
            p.setFont(QFont("Consolas", max(18, side//8), QFont.Bold)); p.setPen(text_color)
            p.drawText(self.rect(), Qt.AlignCenter, self.time_text)
            p.setFont(QFont("Segoe UI", max(8, side//36))); p.setPen(QColor(140,140,140))
            p.drawText(QRect(0, oy+side//2+side//7, w, 28), Qt.AlignCenter, self.LABELS.get(self.state, ""))


class VideoPreviewWidget(QWidget):
    COLORS = {"idle": QColor(120,120,120), "running": QColor(46,204,113), "warning": QColor(243,156,18), "critical": QColor(231,76,60), "done": QColor(52,152,219)}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 180)
        self.progress, self.time_text, self.state = 1.0, "00:00", "idle"
        self.visual_theme = "default"
        self.anim_step = 0
        self.timer = QTimer(self); self.timer.timeout.connect(self._animate); self.timer.start(33)

    def showEvent(self, event):
        self.timer.start(33); super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop(); super().hideEvent(event)

    def update_display(self, time_text, state, progress):
        self.time_text, self.state, self.progress = time_text, state, progress

    def _animate(self):
        self.anim_step += 1; self.update()

    def paintEvent(self, event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.Antialiasing)
            hue = (self.anim_step * 2) % 360
            grad = QLinearGradient(0, 0, self.width(), self.height())
            if self.visual_theme == "psychedelic":
                # Vivid shifting rainbow background
                grad.setColorAt(0, QColor.fromHsv(hue, 255, 130))
                grad.setColorAt(0.33, QColor.fromHsv((hue+90)%360, 255, 110))
                grad.setColorAt(0.66, QColor.fromHsv((hue+180)%360, 255, 120))
                grad.setColorAt(1, QColor.fromHsv((hue+270)%360, 255, 100))
            elif self.visual_theme == "cosmic":
                grad.setColorAt(0, QColor.fromHsv(240, 120, 50))
                grad.setColorAt(1, QColor.fromHsv(270, 140, 30))
            elif self.visual_theme == "glitch":
                v = 40 + int(20*np.sin(self.anim_step*0.3))
                grad.setColorAt(0, QColor(0, v, 0))
                grad.setColorAt(1, QColor(v, 0, v))
            else:
                grad.setColorAt(0, QColor.fromHsv(hue, 100, 60))
                grad.setColorAt(1, QColor.fromHsv((hue+90)%360, 100, 40))
            p.fillRect(self.rect(), grad)

            # Floating orb
            p.setPen(Qt.NoPen); p.setBrush(QColor(255,255,255, 40))
            cx = (self.anim_step * 2) % (self.width() + 100) - 50
            p.drawEllipse(QRectF(cx, 40, 60, 100))

            # Psychedelic: extra floating orbs
            if self.visual_theme == "psychedelic":
                for offset, size, alpha in [(150, 40, 30), (-80, 80, 20), (200, 30, 35)]:
                    p.setBrush(QColor.fromHsv((hue+offset)%360, 200, 255, alpha))
                    cx2 = (self.anim_step * 3 + offset*5) % (self.width() + 120) - 60
                    cy2 = 30 + 60*np.sin(self.anim_step*0.05 + offset)
                    p.drawEllipse(QRectF(cx2, cy2, size, size*1.6))

            # Chat text
            p.setPen(QColor(0,0,0,80)); p.setFont(QFont("Segoe UI", 7))
            p.drawText(10, self.height()-30, "Awesome stream! 🔥")
            p.drawText(10, self.height()-15, "How did you do that?")

            # Timer pill overlay
            color = self.COLORS.get(self.state, QColor(120,120,120))
            if self.visual_theme == "psychedelic" and self.state in ("running","warning","critical"):
                color = QColor.fromHsv((self.anim_step*4)%360, 255, 230)
            pill_w, pill_h = 110, 36
            pill_rect = QRect(self.width()-pill_w-10, 10, pill_w, pill_h)
            p.setBrush(QColor(0, 0, 0, 180)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(pill_rect, 8, 8)
            bar_rect = QRect(pill_rect.x()+4, pill_rect.y()+pill_rect.height()-8, pill_rect.width()-8, 4)
            p.setBrush(QColor(80,80,80)); p.drawRoundedRect(bar_rect, 2, 2)
            p.setBrush(color)
            p.drawRoundedRect(QRect(bar_rect.x(), bar_rect.y(), int(bar_rect.width()*self.progress), bar_rect.height()), 2, 2)
            p.setPen(Qt.white); p.setFont(QFont("Consolas", 14, QFont.Bold))
            p.drawText(pill_rect.adjusted(0,0,0,-6), Qt.AlignCenter, self.time_text)

            if self.state in ["running", "warning", "critical"]:
                p.setBrush(QColor(231, 76, 60, 200)); p.setPen(Qt.NoPen)
                p.drawEllipse(QRectF(15, 18, 12, 12))


class PresentationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background:#1a1a1a;")
        self.time_text, self.state, self.progress = "00:00", "idle", 1.0

    def update_display(self, time_text, state, progress):
        self.time_text, self.state, self.progress = time_text, state, progress
        if self.isVisible(): self.update()

    def paintEvent(self, event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.Antialiasing)
            p.fillRect(self.rect(), QColor(26, 26, 26))
            color = CircularTimer.COLORS.get(self.state, QColor(120,120,120))
            font = QFont("Consolas", min(self.width(), self.height())//6, QFont.Bold)
            p.setFont(font); p.setPen(color)
            p.drawText(self.rect(), Qt.AlignCenter, self.time_text)
            bh = 8
            p.fillRect(QRect(0, self.height()-bh, self.width(), bh), QColor(55,55,55))
            p.fillRect(QRect(0, self.height()-bh, int(self.width()*self.progress), bh), color)
            p.setFont(QFont("Segoe UI", 12)); p.setPen(QColor(70,70,70))
            p.drawText(QRect(0, 10, self.width(), 25), Qt.AlignCenter, "ESC to exit  |  Space = Start/Pause")

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape: self.hide()

    def mousePressEvent(self, e):
        self.hide()


# ═══════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════
class TimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChronoTube: Synth Timer")
        self.setMinimumSize(680, 750)
        self.resize(700, 780)

        self.total_seconds, self.remaining = 0, 0
        self.running, self.paused = False, False

        self.clock = QTimer(self); self.clock.setInterval(1000); self.clock.timeout.connect(self._tick)
        self.pulse = QTimer(self); self.pulse.setInterval(500); self.pulse.timeout.connect(self._do_pulse)

        self.tick_player = QMediaPlayer(self)
        self.tick_out = QAudioOutput(self)
        self.tick_player.setAudioOutput(self.tick_out)

        self.alert_player = QMediaPlayer(self)
        self.alert_out = QAudioOutput(self)
        self.alert_player.setAudioOutput(self.alert_out)

        self.pres = PresentationWidget()

        self._build_ui()
        self._wire()
        self._set_volume(70)
        self._refresh()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root); lay.setSpacing(8); lay.setContentsMargins(16, 12, 16, 12)

        t = QLabel("🎬  ChronoTube: Synth Timer")
        t.setFont(QFont("Segoe UI", 22, QFont.Bold)); t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("color:#e74c3c;"); lay.addWidget(t)

        top_layout = QHBoxLayout()
        self.ring = CircularTimer()
        top_layout.addWidget(self.ring, 2)

        preview_container = QVBoxLayout()
        pl = QLabel("🖥  Live Video Preview")
        pl.setAlignment(Qt.AlignCenter); pl.setStyleSheet("color:#888; font-size:11px; font-weight:bold;")
        preview_container.addWidget(pl)
        self.vid_preview = VideoPreviewWidget()
        preview_container.addWidget(self.vid_preview, 0, Qt.AlignCenter)
        preview_container.addStretch()
        top_layout.addLayout(preview_container, 1)
        lay.addLayout(top_layout)

        g_presets = QGroupBox("⏳  Timer Presets")
        gl = QGridLayout(g_presets); gl.setSpacing(4)
        presets = [
            ("3s", 3), ("5s", 5), ("7s", 7), ("10s", 10),
            ("15s", 15), ("30s", 30), ("45s", 45), ("60s", 60),
            ("90s", 90), ("2 min", 120), ("3 min", 180), ("5 min", 300),
            ("7 min", 420), ("10 min", 600), ("12 min", 720), ("15 min", 900),
            ("20 min", 1200), ("25 min", 1500), ("30 min", 1800), ("45 min", 2700),
            ("1 hour", 3600), ("1.5 hrs", 5400), ("2 hrs", 7200), ("3 hrs", 10800)
        ]
        cols = 6
        for i, (label, secs) in enumerate(presets):
            b = QPushButton(label); b.setObjectName("presetBtn"); b.setProperty("secs", secs)
            b.setFixedHeight(28)
            gl.addWidget(b, i // cols, i % cols)
        lay.addWidget(g_presets)

        g3 = QGroupBox("⏱  Custom Time"); h3 = QHBoxLayout(g3)
        self.sp_h = QSpinBox(); self.sp_h.setRange(0, 23); self.sp_h.setPrefix("H: ")
        self.sp_m = QSpinBox(); self.sp_m.setRange(0, 59); self.sp_m.setPrefix("M: "); self.sp_m.setValue(10)
        self.sp_s = QSpinBox(); self.sp_s.setRange(0, 59); self.sp_s.setPrefix("S: ")
        for sb in (self.sp_h, self.sp_m, self.sp_s):
            sb.setFont(QFont("Consolas", 14, QFont.Bold)); sb.setAlignment(Qt.AlignCenter); h3.addWidget(sb)
        b_set = QPushButton("Set"); b_set.setObjectName("presetBtn"); b_set.clicked.connect(self._set_custom); h3.addWidget(b_set)
        lay.addWidget(g3)

        hc = QHBoxLayout()
        self.btn_start = QPushButton("▶  Start"); self.btn_start.setObjectName("startBtn")
        self.btn_pause = QPushButton("⏸  Pause"); self.btn_pause.setObjectName("pauseBtn"); self.btn_pause.setEnabled(False)
        self.btn_reset = QPushButton("⏹  Reset"); self.btn_reset.setObjectName("resetBtn")
        hc.addWidget(self.btn_start); hc.addWidget(self.btn_pause); hc.addWidget(self.btn_reset)
        lay.addLayout(hc)

        g4 = QGroupBox("🔊  Sound Options"); gl4 = QGridLayout(g4)
        gl4.addWidget(QLabel("Theme:"), 0, 0)
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["Default", "Psychedelic", "Cosmic Space", "Cyberpunk Glitch"])
        self.cmb_theme.setObjectName("themeCombo"); gl4.addWidget(self.cmb_theme, 0, 1)

        self.chk_tick = QCheckBox("Second tick"); self.chk_tick.setChecked(True)
        self.chk_min = QCheckBox("Minute alert"); self.chk_min.setChecked(True)
        self.chk_hr = QCheckBox("Hour chime"); self.chk_hr.setChecked(True)
        self.chk_warn = QCheckBox("10s warning"); self.chk_warn.setChecked(True)
        self.chk_done = QCheckBox("Timer complete"); self.chk_done.setChecked(True)
        self.chk_loop = QCheckBox("Loop timer")

        gl4.addWidget(self.chk_tick, 1, 0); gl4.addWidget(self.chk_min, 1, 1)
        gl4.addWidget(self.chk_hr, 2, 0); gl4.addWidget(self.chk_warn, 2, 1)
        gl4.addWidget(self.chk_done, 3, 0); gl4.addWidget(self.chk_loop, 3, 1)

        vl = QLabel("Volume:"); self.vol = QSlider(Qt.Horizontal); self.vol.setRange(0, 100); self.vol.setValue(70)
        gl4.addWidget(vl, 4, 0); gl4.addWidget(self.vol, 4, 1)
        lay.addWidget(g4)

        g5 = QGroupBox("🎵  Preview Sounds"); h5 = QHBoxLayout(g5)
        for name, label in [("tick", "Tick"), ("minute", "Minute"), ("hour", "Hour"), ("complete", "Done")]:
            b = QPushButton(label); b.setObjectName("presetBtn"); b.setProperty("preview", name); h5.addWidget(b)
        lay.addWidget(g5)

        he = QHBoxLayout()
        self.btn_pres = QPushButton("🖥  Presentation Mode"); self.btn_pres.setObjectName("presetBtn")
        self.btn_top = QPushButton("📌  Always on Top"); self.btn_top.setObjectName("presetBtn"); self.btn_top.setCheckable(True)
        he.addWidget(self.btn_pres); he.addWidget(self.btn_top)
        lay.addLayout(he)

        self.status = QLabel("Set a time and press Start")
        self.status.setAlignment(Qt.AlignCenter); self.status.setStyleSheet("color:#666;font-size:11px;")
        lay.addWidget(self.status)

    def _wire(self):
        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_reset.clicked.connect(self._on_reset)
        self.vol.valueChanged.connect(self._set_volume)
        self.btn_pres.clicked.connect(self._show_pres)
        self.btn_top.toggled.connect(self._toggle_top)
        self.cmb_theme.currentIndexChanged.connect(self._change_theme)

        for b in self.findChildren(QPushButton):
            if b.property("secs") is not None: b.clicked.connect(lambda _, btn=b: self._apply_preset(btn))
            if b.property("preview") is not None: b.clicked.connect(lambda _, btn=b: self._preview(btn))

        QShortcut(QKeySequence(Qt.Key_Space), self, self._space)
        QShortcut(QKeySequence("R"), self, self._on_reset)
        QShortcut(QKeySequence("F"), self, self._show_pres)

    @staticmethod
    def _fmt(s):
        h, m, s = s // 3600, (s % 3600) // 60, s % 60
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _play(self, name, player=None):
        path = SoundEngine.path(name)
        if not path or not os.path.isfile(path): return
        tgt = player or self.alert_player; tgt.stop()
        tgt.setSource(QUrl.fromLocalFile(os.path.abspath(path))); tgt.setPosition(0); tgt.play()

    def _set_volume(self, v):
        vol = v / 100.0; self.tick_out.setVolume(vol); self.alert_out.setVolume(vol)

    def _apply_preset(self, btn): self._set_time(btn.property("secs"))

    def _set_custom(self):
        s = self.sp_h.value()*3600 + self.sp_m.value()*60 + self.sp_s.value()
        if s > 0: self._set_time(s)

    def _set_time(self, secs):
        self.clock.stop(); self.pulse.stop()
        self.total_seconds = max(int(secs), 0); self.remaining = self.total_seconds
        self.running = self.paused = False
        self.btn_start.setEnabled(True); self.btn_start.setText("▶  Start"); self.btn_pause.setEnabled(False)
        self._refresh()

    def _change_theme(self, index):
        themes = ["default", "psychedelic", "cosmic", "glitch"]
        if 0 <= index < len(themes):
            SoundEngine.set_theme(themes[index])
            self.ring.visual_theme = themes[index]
            self.vid_preview.visual_theme = themes[index]

    def _refresh(self):
        text = self._fmt(self.remaining); total = max(self.total_seconds, 1)
        prog = self.remaining / total if self.total_seconds else 1.0

        if not self.running and not self.paused: state = "idle"
        elif self.remaining <= 0: state = "done"
        elif self.remaining <= 3: state = "critical"
        elif self.remaining <= 10: state = "warning"
        else: state = "running"

        self.ring.progress, self.ring.time_text, self.ring.state = prog, text, state
        self.ring.update()
        self.vid_preview.update_display(text, state, prog)
        self.pres.update_display(text, state, prog)

        msgs = {"done": ("⏰ Timer complete!", "#3498db"), "critical": ("🔴 Final seconds!", "#e74c3c"), "warning": ("🟡 Under 10 seconds", "#f39c12")}
        if self.paused: msg, col = "⏸  Paused", "#f39c12"
        elif self.running: msg, col = msgs.get(state, ("▶  Running…", "#27ae60"))
        else: msg, col = "Set a time and press Start", "#666"

        self.status.setText(msg); self.status.setStyleSheet(f"color:{col};font-size:11px;")

    def _on_start(self):
        if self.total_seconds <= 0: return
        if self.paused:
            self.paused = False; self.running = True; self.clock.start(); self.pulse.stop()
        else:
            self.remaining = self.total_seconds; self.running = True; self.paused = False
            self.pulse.stop(); self.clock.start()
        self.btn_start.setEnabled(False); self.btn_pause.setEnabled(True); self.btn_start.setText("▶  Start"); self._refresh()

    def _on_pause(self):
        if self.running:
            self.running = False; self.paused = True; self.clock.stop()
            self.btn_start.setEnabled(True); self.btn_start.setText("▶  Resume"); self.btn_pause.setEnabled(False); self._refresh()

    def _on_reset(self):
        self.clock.stop(); self.pulse.stop(); self.running = self.paused = False; self.remaining = self.total_seconds
        self.btn_start.setEnabled(True); self.btn_start.setText("▶  Start"); self.btn_pause.setEnabled(False); self._refresh()

    def _space(self):
        if self.running: self._on_pause()
        else: self._on_start()

    def _tick(self):
        r = self.remaining
        if self.chk_hr.isChecked() and r % 3600 == 0 and r > 0: self._play("hour")
        elif self.chk_min.isChecked() and r % 60 == 0 and r > 0: self._play("minute")
        elif r <= 3 and r > 0 and self.chk_done.isChecked(): self._play("last3", self.tick_player)
        elif r == 10 and self.chk_warn.isChecked(): self._play("warning", self.tick_player)
        elif self.chk_tick.isChecked() and r > 0: self._play("tick", self.tick_player)

        self.remaining -= 1
        if self.remaining <= 0:
            self.remaining = 0; self._finish(); return
        self._refresh()

    def _finish(self):
        self.clock.stop(); self.running = False; self._refresh()
        if self.chk_done.isChecked(): QTimer.singleShot(250, lambda: self._play("complete"))
        self.pulse.start(); self.btn_start.setEnabled(True); self.btn_start.setText("▶  Start"); self.btn_pause.setEnabled(False)
        if self.chk_loop.isChecked(): QTimer.singleShot(3000, self._loop)

    def _loop(self):
        if not self.chk_loop.isChecked(): return
        self.pulse.stop(); self.remaining = self.total_seconds; self.running = True; self.paused = False; self.clock.start()
        self.btn_start.setEnabled(False); self.btn_pause.setEnabled(True); self._refresh()

    def _do_pulse(self):
        self.ring.pulse_on = not self.ring.pulse_on; self.ring.update()

    def _preview(self, btn):
        self._play(btn.property("preview"))

    def _show_pres(self):
        self.pres.showFullScreen()

    def _toggle_top(self, on):
        flags = self.windowFlags()
        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint if on else flags & ~Qt.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        self.pres.close()
        SoundEngine.cleanup()
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════════════
#  DARK THEME STYLESHEET
# ═══════════════════════════════════════════════════════════════════
DARK_QSS = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; }
QGroupBox { border: 1px solid #3a3a3a; border-radius: 6px; margin-top: 12px; padding: 14px 8px 8px 8px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QPushButton { background-color: #333; border: 1px solid #4a4a4a; border-radius: 5px; padding: 8px 14px; color: #ddd; font-size: 13px; }
QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #222; }
QPushButton#startBtn { background:#27ae60; border-color:#1e8449; color:#fff; font-weight:bold; font-size:14px; } QPushButton#startBtn:hover { background:#2ecc71; } QPushButton#startBtn:disabled { background:#444; color:#777; }
QPushButton#pauseBtn { background:#e67e22; border-color:#c0691c; color:#fff; font-weight:bold; font-size:14px; } QPushButton#pauseBtn:hover { background:#f39c12; } QPushButton#pauseBtn:disabled { background:#444; color:#777; }
QPushButton#resetBtn { background:#c0392b; border-color:#922b21; color:#fff; font-weight:bold; font-size:14px; } QPushButton#resetBtn:hover { background:#e74c3c; }
QPushButton#presetBtn { background:#2c3e50; border-color:#3d566e; color:#ecf0f1; padding:5px 8px; font-size:12px; } QPushButton#presetBtn:hover { background:#34495e; }
QComboBox { background:#333; border:1px solid #4a4a4a; border-radius:4px; padding:6px; color:#eee; font-weight:bold; } QComboBox::drop-down { border:none; } QComboBox QAbstractItemView { background:#2c3e50; color:#ecf0f1; selection-background-color:#34495e; }
QSpinBox { background:#333; border:1px solid #4a4a4a; border-radius:4px; padding:4px; color:#eee; font-size:15px; font-weight:bold; } QSpinBox::up-button, QSpinBox::down-button { background:#444; border:1px solid #555; width:20px; }
QCheckBox { color:#e0e0e0; spacing:8px; } QCheckBox::indicator { width:18px; height:18px; border:1px solid #555; border-radius:3px; background:#333; } QCheckBox::indicator:checked { background:#27ae60; border-color:#27ae60; }
QSlider::groove:horizontal { height:6px; background:#333; border-radius:3px; } QSlider::handle:horizontal { width:16px; height:16px; background:#27ae60; border-radius:8px; margin:-5px 0; } QSlider::sub-page:horizontal { background:#27ae60; border-radius:3px; }
QLabel { color: #e0e0e0; }
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    SoundEngine.init(theme="default")
    win = TimerWindow()
    win.show()
    ret = app.exec()
    SoundEngine.cleanup()
    sys.exit(ret)

if __name__ == "__main__":
    main()