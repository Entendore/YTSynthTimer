#!/usr/bin/env python3
"""
Strudel Timer — A PySide6 timer app with embedded Strudel live-coding audio.
Psychedelic edition v2: rainbow background, morphing blobs, trippy particles,
audio visualizer, celebration fireworks, multi-ring tick markers (sec/min/hour),
analog clock, minute/hour chime sounds, lap times, volume control, fullscreen,
countdown warning, pulsing border glow, Pomodoro auto-cycle, always-on-top,
keyboard shortcuts, and background intensity control.

Requirements:
  pip install PySide6
  sudo apt install libxtst6 libegl1   (for QWebEngineView on Linux)

Keyboard Shortcuts:
  Space     Start / Pause
  R         Reset
  L         Lap (stopwatch mode)
  F11       Toggle Fullscreen
  T         Toggle Always-on-Top
  Escape    Quit

Run:
  python strudel_timer.py
"""

import sys
import os
import math
import random
import time
import datetime
import colorsys
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QUrl, QSize, Signal, Slot, QElapsedTimer,
    QRectF, QPointF, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QRadialGradient, QPalette,
    QLinearGradient, QPainterPath, QPolygonF, QBrush, QConicalGradient,
    QShortcut, QKeySequence
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit,
    QSplitter, QSizePolicy, QGroupBox, QCheckBox, QStatusBar,
    QGridLayout, QFrame, QSlider, QListWidget, QListWidgetItem,
    QScrollArea
)

# ---------------------------------------------------------------------------
# WebEngine (graceful fallback)
# ---------------------------------------------------------------------------
WEBENGINE_AVAILABLE = False
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Stylesheet — Psychedelic Dark Theme v2
# ---------------------------------------------------------------------------
STYLESHEET = """
QMainWindow, QWidget#central {
    background-color: transparent;
}
QWidget {
    color: #e8e0f0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}
QLabel { background: transparent; }

/* ── Buttons ── */
QPushButton {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2a1050,stop:1 #1a0835);
    border: 1px solid #6a30a0;
    border-radius: 10px;
    padding: 10px 20px;
    color: #e8e0f0;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3d1870,stop:1 #2a1050);
    border-color: #a060e0;
    color: #fff;
}
QPushButton:pressed {
    background-color: #e040a0;
    border-color: #e040a0;
    color: #fff;
}
QPushButton#startBtn {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #10504a,stop:1 #082a28);
    border: 2px solid #40e0d0;
    border-radius: 12px;
    font-size: 16px;
    padding: 14px 36px;
    color: #40e0d0;
}
QPushButton#startBtn:hover {
    background-color: #40e0d0;
    color: #0a0a1e;
    border-color: #80fff0;
}
QPushButton#resetBtn {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #501030,stop:1 #3a0820);
    border: 1px solid #e040a0;
    border-radius: 12px;
}
QPushButton#resetBtn:hover {
    background-color: #e040a0;
    color: #fff;
}
QPushButton#presetBtn {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #201040,stop:1 #150a2a);
    border: 1px solid #5030a0;
    padding: 8px 16px;
    min-width: 80px;
    font-size: 12px;
    border-radius: 8px;
}
QPushButton#presetBtn:checked, QPushButton#presetBtn:selected {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #a060e0,stop:1 #7030b0);
    color: #0a0a1e;
    border-color: #c080ff;
    font-weight: bold;
}
QPushButton#smallBtn {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #201040,stop:1 #150a2a);
    border: 1px solid #5030a0;
    padding: 7px 16px;
    min-width: 70px;
    font-size: 12px;
    border-radius: 8px;
}
QPushButton#smallBtn:hover {
    background-color: #5030a0;
    border-color: #a060e0;
}

/* ── Combo / Spin ── */
QComboBox, QSpinBox {
    background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #201040,stop:1 #150a2a);
    border: 1px solid #5030a0;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e8e0f0;
    font-size: 13px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #150a2a;
    border: 1px solid #5030a0;
    selection-background-color: #5030a0;
    color: #e8e0f0;
}

/* ── Text Edit ── */
QTextEdit {
    background-color: #0a0818;
    border: 1px solid #3a2050;
    border-radius: 10px;
    color: #d0c0e8;
    font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    padding: 8px;
    selection-background-color: #5030a0;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #5030a0;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
    color: #c080ff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
}

/* ── Splitter ── */
QSplitter::handle { background-color: #3a2060; width: 3px; }

/* ── Status Bar ── */
QStatusBar { background-color: rgba(10,8,24,200); color: #a090b8; font-size: 12px; }

/* ── Check Box ── */
QCheckBox { spacing: 8px; color: #e8e0f0; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid #5030a0; background-color: #150a2a;
}
QCheckBox::indicator:checked {
    background-color: #c080ff; border-color: #c080ff;
}

/* ── Slider ── */
QSlider::groove:horizontal {
    height: 6px;
    background: #201040;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px; height: 16px;
    margin: -5px 0;
    background: qradialgradient(cx:0.5,cy:0.5,radius:0.5,fx:0.5,fy:0.3,
        stop:0 #c080ff, stop:1 #7030b0);
    border: 1px solid #a060e0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7030b0,stop:1 #c080ff);
    border-radius: 3px;
}

/* ── List Widget (Lap times) ── */
QListWidget {
    background-color: #0a0818;
    border: 1px solid #3a2050;
    border-radius: 8px;
    color: #d0c0e8;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 3px 6px;
    border-bottom: 1px solid #1a1030;
}
QListWidget::item:selected {
    background-color: #5030a0;
    color: #fff;
}
QScrollArea {
    background: transparent;
    border: none;
}
"""

PRESETS = {
    "Pomodoro (25m)": 25 * 60,
    "Short Break (5m)": 5 * 60,
    "Long Break (15m)": 15 * 60,
    "1 Minute": 60,
}

DEFAULT_STRUDEL_PATTERN = """\
// Finish pattern — plays when timer completes
$: s("bd sd hh oh").slow(2)
  .gain(0.8)
  .room(0.5)
"""

DEFAULT_TICK_PATTERN = """\
// Tick pattern — plays continuously while timer runs
$: s("click").fast(1)
  .gain(0.4)
  .speed(1.5)
"""

# ---------------------------------------------------------------------------
# HTML for the embedded Strudel panel (with minute/hour chime + warning beep)
# ---------------------------------------------------------------------------
STRUDEL_PANEL_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Strudel Audio Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;background:#0a0818}
#strudel-frame{width:100%;height:100%;border:none}
#status-bar{
  position:absolute;top:8px;right:12px;color:#a090b8;font-size:12px;
  font-family:'Consolas',monospace;z-index:10;
  background:rgba(10,8,24,0.85);padding:4px 10px;border-radius:4px;
  display:flex;align-items:center;gap:6px;
}
.dot{width:10px;height:10px;border-radius:50%;background:#484f58;transition:background 0.3s}
.dot.active{background:#c080ff;box-shadow:0 0 8px #c080ff}
</style>
</head>
<body>
<div id="status-bar"><span class="dot" id="dot"></span><span id="status-text">idle</span></div>
<iframe id="strudel-frame" src="https://strudel.cc/~/embed" allow="autoplay"></iframe>
<script>
var dot=document.getElementById('dot'), statusText=document.getElementById('status-text');
var audioCtx=null;
var masterVolume=1.0;

function getAudioCtx(){
  if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)();
  return audioCtx;
}

function setStatus(t,a){statusText.textContent=t;dot.classList.toggle('active',a)}

function playTick(freq, dur, vol){
  try{
    var ctx=getAudioCtx();
    var osc=ctx.createOscillator();
    var gain=ctx.createGain();
    osc.type='sine';
    osc.frequency.setValueAtTime(freq||800, ctx.currentTime);
    gain.gain.setValueAtTime((vol||0.15)*masterVolume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+(dur||0.06));
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime+(dur||0.06));
  }catch(e){}
}

function playClickTick(){
  try{
    var ctx=getAudioCtx();
    var buf=ctx.createBuffer(1, ctx.sampleRate*0.03, ctx.sampleRate);
    var data=buf.getChannelData(0);
    for(var i=0;i<data.length;i++){
      data[i]=(Math.random()*2-1)*Math.exp(-i/(ctx.sampleRate*0.005));
    }
    var src=ctx.createBufferSource();
    src.buffer=buf;
    var gain=ctx.createGain();
    gain.gain.setValueAtTime(0.25*masterVolume, ctx.currentTime);
    var hp=ctx.createBiquadFilter();
    hp.type='highpass';
    hp.frequency.value=2000;
    src.connect(hp);
    hp.connect(gain);
    gain.connect(ctx.destination);
    src.start();
  }catch(e){}
}

function playNoteTick(freq, type, dur){
  try{
    var ctx=getAudioCtx();
    var osc=ctx.createOscillator();
    var gain=ctx.createGain();
    osc.type=type||'triangle';
    osc.frequency.setValueAtTime(freq||523.25, ctx.currentTime);
    gain.gain.setValueAtTime(0.2*masterVolume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+(dur||0.15));
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime+(dur||0.15));
  }catch(e){}
}

function playMinuteChime(){
  try{
    var ctx=getAudioCtx();
    var t=ctx.currentTime;
    var freqs=[220, 440, 660, 880];
    for(var i=0;i<freqs.length;i++){
      var osc=ctx.createOscillator();
      var gain=ctx.createGain();
      osc.type='sine';
      osc.frequency.setValueAtTime(freqs[i], t);
      var vol=0.18/(i+1)*masterVolume;
      gain.gain.setValueAtTime(vol, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t+0.8);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t+0.8);
    }
  }catch(e){}
}

function playHourChime(){
  try{
    var ctx=getAudioCtx();
    var t=ctx.currentTime;
    var freqs=[261.63, 329.63, 392.00, 523.25, 783.99];
    for(var i=0;i<freqs.length;i++){
      var osc=ctx.createOscillator();
      var gain=ctx.createGain();
      osc.type = i<2 ? 'sine' : (i<4 ? 'triangle' : 'sine');
      osc.frequency.setValueAtTime(freqs[i], t);
      var vol = 0.15/(i*0.5+1)*masterVolume;
      gain.gain.setValueAtTime(0.001, t);
      gain.gain.linearRampToValueAtTime(vol, t+0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, t+1.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t+1.5);
    }
    setTimeout(function(){
      try{
        var osc2=ctx.createOscillator();
        var g2=ctx.createGain();
        osc2.type='sine';
        osc2.frequency.setValueAtTime(1046.5, ctx.currentTime);
        g2.gain.setValueAtTime(0.08*masterVolume, ctx.currentTime);
        g2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+1.0);
        osc2.connect(g2); g2.connect(ctx.destination);
        osc2.start(ctx.currentTime); osc2.stop(ctx.currentTime+1.0);
      }catch(e){}
    }, 300);
  }catch(e){}
}

// WARNING BEEP — urgent tone for last 10 seconds of countdown
function playWarningBeep(secsLeft){
  try{
    var ctx=getAudioCtx();
    var t=ctx.currentTime;
    // Higher pitch and faster beeps as time runs out
    var freq = 600 + (10 - secsLeft) * 80;
    var dur = 0.08 + (10 - secsLeft) * 0.01;
    var osc=ctx.createOscillator();
    var gain=ctx.createGain();
    osc.type='square';
    osc.frequency.setValueAtTime(freq, t);
    var vol = (0.15 + (10 - secsLeft) * 0.02) * masterVolume;
    gain.gain.setValueAtTime(vol, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t+dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(t);
    osc.stop(t+dur);
    // Double beep for last 3 seconds
    if(secsLeft <= 3){
      var osc2=ctx.createOscillator();
      var gain2=ctx.createGain();
      osc2.type='square';
      osc2.frequency.setValueAtTime(freq*1.5, t+dur+0.05);
      gain2.gain.setValueAtTime(vol*0.8, t+dur+0.05);
      gain2.gain.exponentialRampToValueAtTime(0.001, t+dur*2+0.1);
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(t+dur+0.05);
      osc2.stop(t+dur*2+0.1);
    }
  }catch(e){}
}

window.addEventListener('message',function(e){
  if(e.data&&e.data.type==='strudel-play'){
    setStatus('playing',true);
    try{document.getElementById('strudel-frame').contentWindow.postMessage({type:'eval',code:e.data.code},'*')}catch(err){}
    setTimeout(function(){setStatus('idle',false)},16000);
  }
  if(e.data&&e.data.type==='strudel-stop'){
    setStatus('idle',false);
    try{document.getElementById('strudel-frame').contentWindow.postMessage({type:'stop'},'*')}catch(err){}
  }
  if(e.data&&e.data.type==='tick-sound'){
    var t=e.data;
    if(t.sound==='click') playClickTick();
    else if(t.sound==='note') playNoteTick(t.freq, t.wave, t.dur);
    else if(t.sound==='beep') playTick(t.freq, t.dur, t.vol);
    else if(t.sound==='minute') playMinuteChime();
    else if(t.sound==='hour') playHourChime();
    else if(t.sound==='warning') playWarningBeep(t.secs);
  }
  if(e.data&&e.data.type==='set-volume'){
    masterVolume=e.data.volume;
  }
  if(e.data&&e.data.type==='tick-pattern-play'){
    setStatus('tick pattern',true);
    try{document.getElementById('strudel-frame').contentWindow.postMessage({type:'eval',code:e.data.code},'*')}catch(err){}
  }
  if(e.data&&e.data.type==='tick-pattern-stop'){
    setStatus('idle',false);
    try{document.getElementById('strudel-frame').contentWindow.postMessage({type:'stop'},'*')}catch(err){}
  }
});
</script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════════════════
#  Psychedelic Particle Background
# ═══════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'r', 'alpha', 'hue', 'pulse_speed', 'pulse_phase')

    def __init__(self, w, h, hue=None):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.6, -0.1)
        self.r = random.uniform(1.0, 4.0)
        self.alpha = random.uniform(50, 200)
        self.pulse_speed = random.uniform(0.5, 2.5)
        self.pulse_phase = random.uniform(0, math.pi * 2)
        self.hue = hue if hue is not None else random.uniform(0, 360)


class PsychedelicBackground(QWidget):
    """Animated psychedelic background with morphing color blobs, shifting gradient, rainbow particles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._particles: list[Particle] = []
        self._t = 0.0
        self._hue_shift = 0.0
        self._intensity = 1.0  # 0.0-1.0, controlled by slider
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_intensity(self, val: float):
        self._intensity = max(0.0, min(1.0, val))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        count = max(40, self.width() * self.height() // 8000)
        self._particles = [Particle(self.width(), self.height()) for _ in range(count)]

    def _tick(self):
        speed = 0.033 * (0.3 + 0.7 * self._intensity)
        self._t += speed
        self._hue_shift = (self._hue_shift + 0.15 * (0.3 + 0.7 * self._intensity)) % 360
        w, h = self.width(), self.height()
        for p in self._particles:
            angle = math.sin(self._t * 0.3 + p.y * 0.01) * 0.5
            p.x += p.vx * (0.3 + 0.7 * self._intensity) + math.sin(angle) * 0.2 * self._intensity
            p.y += p.vy * (0.3 + 0.7 * self._intensity)
            p.hue = (p.hue + 0.2 * self._intensity) % 360
            if p.y < -10:
                p.y = h + 10; p.x = random.uniform(0, w)
            if p.x < -10: p.x = w + 10
            elif p.x > w + 10: p.x = -10
        self.update()

    def _hsv_color(self, h, s, v, a=255):
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return QColor(int(r * 255), int(g * 255), int(b * 255), a)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        inten = self._intensity

        # Base gradient
        hue1 = (self._hue_shift) % 360
        hue2 = (self._hue_shift + 120) % 360
        hue3 = (self._hue_shift + 240) % 360

        grad = QLinearGradient(0, 0, w * 0.5, h)
        grad.setColorAt(0.0, self._hsv_color(hue1, 0.6 * inten, 0.06))
        grad.setColorAt(0.35, self._hsv_color(hue2, 0.5 * inten, 0.04))
        grad.setColorAt(0.7, self._hsv_color(hue3, 0.6 * inten, 0.05))
        grad.setColorAt(1.0, self._hsv_color((hue1 + 60) % 360, 0.4 * inten, 0.03))
        p.fillRect(self.rect(), grad)

        # Morphing blobs
        blob_data = [
            (0.2, 0.3, 350, hue1, 0.7, 0.08),
            (0.8, 0.6, 300, hue2, 0.6, 0.07),
            (0.5, 0.15, 250, hue3, 0.8, 0.06),
            (0.3, 0.8, 280, (hue1 + 180) % 360, 0.5, 0.05),
        ]
        t = self._t
        for cx_f, cy_f, rad, hue, sat, alpha_base in blob_data:
            mx = cx_f * w + math.sin(t * 0.2 + hue) * 40 * inten
            my = cy_f * h + math.cos(t * 0.15 + hue * 0.5) * 30 * inten
            rad_morph = rad + math.sin(t * 0.3 + hue * 0.01) * 50 * inten
            alpha = int(alpha_base * 255 * (0.7 + 0.3 * math.sin(t * 0.5 + hue)) * inten)

            blob = QRadialGradient(mx, my, rad_morph)
            blob.setColorAt(0, self._hsv_color(hue, sat, 0.5, alpha))
            blob.setColorAt(0.5, self._hsv_color((hue + 30) % 360, sat * 0.8, 0.3, alpha // 2))
            blob.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(blob)
            p.drawEllipse(QPointF(mx, my), rad_morph, rad_morph)

        # Particles
        for part in self._particles:
            pulse = 0.5 + 0.5 * math.sin(t * part.pulse_speed + part.pulse_phase)
            a = int(part.alpha * (0.4 + 0.6 * pulse) * (0.3 + 0.7 * inten))
            c = self._hsv_color(part.hue, 0.8, 0.9, a)
            r = part.r * (0.8 + 0.4 * pulse)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawEllipse(QPointF(part.x, part.y), r, r)

            if part.r > 2.0 and inten > 0.3:
                glow = QRadialGradient(part.x, part.y, part.r * 5)
                gc = self._hsv_color(part.hue, 0.9, 0.7, int(a * 0.3 * inten))
                glow.setColorAt(0, gc)
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.setBrush(glow)
                p.drawEllipse(QPointF(part.x, part.y), part.r * 5, part.r * 5)

        # Vignette
        vignette = QRadialGradient(w / 2, h / 2, max(w, h) * 0.7)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.7, QColor(0, 0, 0, 0))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 80))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(vignette)
        p.drawRect(self.rect())

        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Rainbow Audio Visualizer
# ═══════════════════════════════════════════════════════════════════════════
class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar_count = 40
        self._values = [0.0] * self._bar_count
        self._targets = [0.0] * self._bar_count
        self._active = False
        self._t = 0.0
        self._hue_offset = 0.0
        self._warning_mode = False
        self.setMinimumHeight(65)
        self.setMaximumHeight(95)
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._animate)
        self._timer.start()

    def set_active(self, active: bool): self._active = active
    def set_colors(self, top: QColor, bot: QColor): pass
    def set_warning(self, on: bool): self._warning_mode = on

    def trigger_spike(self, intensity=1.0):
        for i in range(self._bar_count):
            self._values[i] = min(1.0, self._values[i] + random.uniform(0.15, 0.5) * intensity)

    def _animate(self):
        self._t += 0.04
        self._hue_offset = (self._hue_offset + 0.8) % 360
        for i in range(self._bar_count):
            if self._active:
                wave = (math.sin(self._t * 3.0 + i * 0.5) * 0.3
                      + math.sin(self._t * 5.7 + i * 0.3) * 0.2
                      + math.sin(self._t * 1.3 + i * 0.8) * 0.15
                      + random.uniform(-0.05, 0.05))
                self._targets[i] = max(0.05, 0.5 + wave)
            else:
                self._targets[i] = 0.03 + 0.02 * math.sin(self._t * 0.8 + i * 0.4)
            self._values[i] += (self._targets[i] - self._values[i]) * 0.18
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w < 10 or h < 10: p.end(); return
        bar_w = max(2, (w - (self._bar_count - 1) * 2) / self._bar_count)
        max_h = h - 8

        for i in range(self._bar_count):
            val = self._values[i]; bh = max(2, val * max_h)
            x = i * (bar_w + 2); y = h - 4 - bh

            if self._warning_mode:
                # Red/orange pulsing in warning mode
                warn_pulse = 0.7 + 0.3 * math.sin(self._t * 8.0 + i * 0.3)
                r_c = int(255 * warn_pulse)
                g_c = int(80 * (1.0 - warn_pulse))
                b_c = 0
                col_top = QColor(r_c, g_c, b_c)
                col_bot = QColor(int(r_c * 0.5), 0, 0)
            else:
                hue = (self._hue_offset + i * (360.0 / self._bar_count)) % 360
                r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.85, 0.95)
                col_top = QColor(int(r * 255), int(g * 255), int(b * 255))
                hue2 = (hue + 40) % 360
                r2, g2, b2 = colorsys.hsv_to_rgb(hue2 / 360.0, 0.9, 0.6)
                col_bot = QColor(int(r2 * 255), int(g2 * 255), int(b2 * 255))

            grad = QLinearGradient(x, y + bh, x, y)
            grad.setColorAt(0, col_bot); grad.setColorAt(1, col_top)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(grad)

            radius = min(bar_w / 2, 3)
            path = QPainterPath()
            path.moveTo(x, y + bh); path.lineTo(x, y + radius)
            path.quadTo(x, y, x + radius, y)
            path.lineTo(x + bar_w - radius, y)
            path.quadTo(x + bar_w, y, x + bar_w, y + radius)
            path.lineTo(x + bar_w, y + bh); path.closeSubpath()
            p.drawPath(path)

            if val > 0.3:
                glow = QRadialGradient(x + bar_w/2, y, bar_w * 1.5)
                gc = QColor(col_top); gc.setAlpha(int(100 * val))
                glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.setBrush(glow)
                p.drawEllipse(QPointF(x + bar_w/2, y), bar_w * 1.5, bar_w)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Session Counter
# ═══════════════════════════════════════════════════════════════════════════
class SessionCounter(QWidget):
    def __init__(self, max_sessions=8, parent=None):
        super().__init__(parent)
        self._count = 0; self._max = max_sessions; self._pulse = 0.0
        self._hue_offset = 0.0
        self.setMinimumHeight(50); self.setMaximumHeight(55)
        self._timer = QTimer(self); self._timer.setInterval(50)
        self._timer.timeout.connect(lambda: (setattr(self, '_pulse', self._pulse + 0.06), self.update()))
        self._timer.start()

    def set_count(self, n: int): self._count = min(n, self._max); self.update()
    def increment(self): self.set_count(self._count + 1)
    def reset(self): self.set_count(0)

    def _hsv_color(self, h, s, v, a=255):
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return QColor(int(r * 255), int(g * 255), int(b * 255), a)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, cy = self.width(), self.height(), self.height() / 2
        self._hue_offset = (self._hue_offset + 0.3) % 360
        p.setPen(QColor(140, 120, 170)); p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRectF(0, 0, 70, h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Sessions")
        sx = 80; sp = min(36, (w - sx - 10) / self._max)
        for i in range(self._max):
            cx = sx + i * sp + sp / 2
            hue = (self._hue_offset + i * 30) % 360
            if i < self._count:
                pulse = 0.7 + 0.3 * math.sin(self._pulse * 2 + i * 0.5)
                glow = QRadialGradient(cx, cy, 18)
                gc = self._hsv_color(hue, 0.8, 0.7, int(80 * pulse))
                glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow)
                p.drawEllipse(QPointF(cx, cy), 18, 18)
                c = self._hsv_color(hue, 0.85, 0.9, int(255 * pulse))
                p.setBrush(c); p.drawEllipse(QPointF(cx, cy), 7, 7)
            else:
                p.setPen(QPen(self._hsv_color(hue, 0.5, 0.3), 1.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(cx, cy), 7, 7)
        p.setPen(QColor(220, 200, 240)); p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.drawText(QRectF(sx + self._max * sp + 10, 0, 60, h),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{self._count}/{self._max}")
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Celebration Overlay
# ═══════════════════════════════════════════════════════════════════════════
class _Firework:
    __slots__ = ('x','y','vx','vy','life','max_life','color','r','trail')
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        a = random.uniform(0, 2*math.pi); s = random.uniform(2, 8)
        self.vx, self.vy = math.cos(a)*s, math.sin(a)*s
        self.max_life = random.uniform(0.6, 1.5); self.life = self.max_life
        self.color = color; self.r = random.uniform(1.5, 4.0)
        self.trail: list = []

class CelebrationOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fireworks: list[_Firework] = []; self._active = False; self._elapsed = 0.0
        self._timer = QTimer(self); self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick); self._timer.start()

    def trigger(self):
        self._active = True; self._elapsed = 0.0; self._fireworks.clear()
        w, h = self.width(), self.height()
        for _ in range(7):
            bx, by = random.uniform(w*0.15, w*0.85), random.uniform(h*0.1, h*0.65)
            hue = random.uniform(0, 360)
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.9, 1.0)
            col = QColor(int(r * 255), int(g * 255), int(b * 255))
            self._fireworks.extend(_Firework(bx, by, col) for _ in range(50))

    def stop(self): self._active = False; self._fireworks.clear(); self.update()

    def _tick(self):
        if not self._active: return
        self._elapsed += 0.025; alive = []
        for fw in self._fireworks:
            fw.life -= 0.025
            if fw.life <= 0: continue
            fw.trail.append((fw.x, fw.y, fw.life/fw.max_life))
            if len(fw.trail) > 10: fw.trail.pop(0)
            fw.x += fw.vx; fw.y += fw.vy; fw.vy += 0.08; fw.vx *= 0.99
            alive.append(fw)
        self._fireworks = alive
        if not alive or self._elapsed > 5.0: self._active = False
        self.update()

    def paintEvent(self, event):
        if not self._fireworks: return
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setCompositionMode(QPainter.CompositionMode.Lighter)
        for fw in self._fireworks:
            frac = fw.life / fw.max_life
            for tx, ty, tf in fw.trail:
                c = QColor(fw.color); c.setAlpha(int(80*tf*frac))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(c)
                p.drawEllipse(QPointF(tx, ty), fw.r*tf*0.7, fw.r*tf*0.7)
            c = QColor(fw.color); c.setAlpha(int(255*frac)); p.setBrush(c)
            p.drawEllipse(QPointF(fw.x, fw.y), fw.r*frac, fw.r*frac)
            glow = QRadialGradient(fw.x, fw.y, fw.r*4*frac)
            gc = QColor(fw.color); gc.setAlpha(int(100*frac))
            glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0,0,0,0))
            p.setBrush(glow); p.drawEllipse(QPointF(fw.x, fw.y), fw.r*4*frac, fw.r*4*frac)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Pulsing Border Glow — draws glowing edges when timer is running
# ═══════════════════════════════════════════════════════════════════════════
class PulsingBorder(QWidget):
    """Overlays a pulsing colored border glow on the main window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self._warning = False
        self._hue_shift = 0.0
        self._pulse = 0.0
        self._thickness = 6
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_active(self, a: bool): self._active = a
    def set_warning(self, w: bool): self._warning = w

    def _tick(self):
        self._pulse += 0.06
        self._hue_shift = (self._hue_shift + 0.3) % 360
        if self._active:
            self.update()

    def paintEvent(self, event):
        if not self._active:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pulse = 0.5 + 0.5 * math.sin(self._pulse)
        border_w = self._thickness + int(4 * pulse)

        if self._warning:
            # Red pulsing border
            for i in range(3):
                alpha = int((40 + 30 * pulse) * (1.0 - i * 0.25))
                p.setPen(QPen(QColor(255, 50, 50, alpha), border_w - i * 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(i, i, w - 2 * i, h - 2 * i)
        else:
            # Rainbow border
            for i in range(4):
                hue = (self._hue_shift + i * 90) % 360
                alpha = int((20 + 15 * pulse) * (1.0 - i * 0.2))
                r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.8, 0.7)
                p.setPen(QPen(QColor(int(r * 255), int(g * 255), int(b * 255), alpha),
                              border_w - i * 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(i, i, w - 2 * i, h - 2 * i)

        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Gradient Title Bar (rainbow shifting)
# ═══════════════════════════════════════════════════════════════════════════
class GradientTitle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = "STRUDEL TIMER"; self._offset = 0.0
        self._timer = QTimer(self); self._timer.setInterval(40)
        self._timer.timeout.connect(lambda: (setattr(self, '_offset', (self._offset+0.8)%360), self.update()))
        self._timer.start(); self.setFixedHeight(44)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, w, 0)
        num_stops = 8
        for i in range(num_stops):
            hue = (self._offset + i * (360 / num_stops)) % 360
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.85, 0.95)
            pos = i / (num_stops - 1)
            wrapped_pos = (pos + self._offset / 720.0) % 1.0
            grad.setColorAt(min(1.0, wrapped_pos), QColor(int(r * 255), int(g * 255), int(b * 255)))
        hue0 = (self._offset) % 360
        r0, g0, b0 = colorsys.hsv_to_rgb(hue0 / 360.0, 0.85, 0.95)
        grad.setColorAt(0, QColor(int(r0 * 255), int(g0 * 255), int(b0 * 255)))
        grad.setColorAt(1, QColor(int(r0 * 255), int(g0 * 255), int(b0 * 255)))

        p.setPen(QPen(QBrush(grad), 1))
        f = QFont("Segoe UI", 18, QFont.Weight.Bold); f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        p.setFont(f); p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, self._text)

        sub_grad = QLinearGradient(0, 0, w, 0)
        for i in range(5):
            hue = (self._offset + 180 + i * 72) % 360
            r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.6, 0.6)
            sub_grad.setColorAt(i / 4.0, QColor(int(r * 255), int(g * 255), int(b * 255)))
        p.setPen(QPen(QBrush(sub_grad), 1))
        sf = QFont("Segoe UI", 9); sf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(sf); p.drawText(QRectF(0, h-14, w, 14), Qt.AlignmentFlag.AlignCenter, "PSYCHEDELIC LIVE-CODED AUDIO TIMER")
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Analog Clock — psychedelic glow edition
# ═══════════════════════════════════════════════════════════════════════════
class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse = 0.0
        self._hue_shift = 0.0
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._pulse += 0.05
        self._hue_shift = (self._hue_shift + 0.2) % 360
        self.update()

    def _hsv_color(self, h, s, v, a=255):
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return QColor(int(r * 255), int(g * 255), int(b * 255), a)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        p.translate(self.width() / 2, self.height() / 2)
        sc = side / 220.0
        p.scale(sc, sc)

        R = 95

        for i in range(3):
            hue = (self._hue_shift + i * 120) % 360
            glow = QRadialGradient(0, 0, R + 20)
            gc = self._hsv_color(hue, 0.8, 0.6, int(12 + 8 * math.sin(self._pulse + i)))
            glow.setColorAt(0.8, QColor(0, 0, 0, 0))
            glow.setColorAt(0.93, gc)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow)
            p.drawEllipse(QPointF(0, 0), R + 20, R + 20)

        face = QRadialGradient(0, -10, R)
        face.setColorAt(0, QColor(30, 20, 50))
        face.setColorAt(1, QColor(15, 10, 30))
        p.setBrush(face)
        p.setPen(QPen(self._hsv_color(self._hue_shift, 0.6, 0.5, 100), 2))
        p.drawEllipse(QPointF(0, 0), R, R)

        p.setPen(QPen(self._hsv_color((self._hue_shift + 60) % 360, 0.4, 0.35, 80), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), R - 8, R - 8)

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            inner = R - 18 if i % 3 == 0 else R - 12
            outer = R - 4
            x1, y1 = inner * math.cos(angle), inner * math.sin(angle)
            x2, y2 = outer * math.cos(angle), outer * math.sin(angle)
            hue = (self._hue_shift + i * 30) % 360
            if i % 3 == 0:
                p.setPen(QPen(self._hsv_color(hue, 0.85, 0.9), 2.5))
            else:
                p.setPen(QPen(self._hsv_color(hue, 0.5, 0.5), 1.5))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            if i % 3 == 0:
                num_r = R - 30
                nx, ny = num_r * math.cos(angle), num_r * math.sin(angle)
                p.setPen(self._hsv_color(hue, 0.7, 0.85))
                nf = QFont("Segoe UI", 11, QFont.Weight.Bold)
                p.setFont(nf)
                num_text = str(i or 12)
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(num_text)
                th = fm.height()
                p.drawText(QRectF(nx - tw/2, ny - th/2, tw, th),
                           Qt.AlignmentFlag.AlignCenter, num_text)

        for i in range(60):
            if i % 5 == 0: continue
            angle = math.radians(i * 6 - 90)
            dx, dy = (R - 6) * math.cos(angle), (R - 6) * math.sin(angle)
            hue = (self._hue_shift + i * 6) % 360
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._hsv_color(hue, 0.5, 0.35))
            p.drawEllipse(QPointF(dx, dy), 1.2, 1.2)

        now = datetime.datetime.now()
        h, m, s = now.hour % 12, now.minute, now.second
        ms = now.microsecond / 1_000_000.0

        sec_angle = math.radians((s + ms) * 6 - 90)
        min_angle = math.radians((m + s / 60.0) * 6 - 90)
        hr_angle = math.radians((h + m / 60.0) * 30 - 90)

        def draw_hand(angle, length, width, hue, glow_r=0):
            ex = length * math.cos(angle)
            ey = length * math.sin(angle)
            tail = length * 0.15
            tx = -tail * math.cos(angle)
            ty = -tail * math.sin(angle)
            if glow_r > 0:
                glow = QRadialGradient(ex, ey, glow_r)
                gc = self._hsv_color(hue, 0.8, 0.7, 50)
                glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow)
                p.drawEllipse(QPointF(ex, ey), glow_r, glow_r)
            col = self._hsv_color(hue, 0.8, 0.9)
            p.setPen(QPen(col, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(tx, ty), QPointF(ex, ey))

        draw_hand(hr_angle, 48, 4.5, (self._hue_shift + 180) % 360, 12)
        draw_hand(min_angle, 68, 3, (self._hue_shift + 90) % 360, 10)
        draw_hand(sec_angle, 78, 1.5, (self._hue_shift + 30) % 360, 8)

        cap = QRadialGradient(0, 0, 6)
        cap_hue = (self._hue_shift + 330) % 360
        cap.setColorAt(0, self._hsv_color(cap_hue, 0.9, 1.0))
        cap.setColorAt(0.6, self._hsv_color(cap_hue, 0.8, 0.7))
        cap.setColorAt(1, self._hsv_color(cap_hue, 0.7, 0.4))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(cap)
        p.drawEllipse(QPointF(0, 0), 5, 5)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawEllipse(QPointF(0, 0), 2, 2)

        p.setPen(self._hsv_color((self._hue_shift + 60) % 360, 0.5, 0.6))
        df = QFont("Consolas", 9)
        p.setFont(df)
        time_str = now.strftime("%H:%M:%S")
        p.drawText(QRectF(-30, 25, 60, 16), Qt.AlignmentFlag.AlignCenter, time_str)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Circular Timer — psychedelic multi-ring with minute/hour/warning effects
# ═══════════════════════════════════════════════════════════════════════════
class CircularTimer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0; self._time_text = "25:00"; self._label_text = "READY"
        self._accent = QColor(160, 80, 255); self._state = "idle"
        self._pulse_phase = 0.0; self._trail_points: list = []
        self._tick_flash = 0.0
        self._minute_flash = 0.0
        self._hour_flash = 0.0
        self._warning_flash = 0.0  # red flash for countdown warning
        self._elapsed_secs = 0
        self._elapsed_mins = 0
        self._elapsed_hrs = 0
        self._total_duration_mins = 0
        self._hue_shift = 0.0
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pulse_timer = QTimer(self); self._pulse_timer.setInterval(33)
        self._pulse_timer.timeout.connect(self._pulse_tick); self._pulse_timer.start()

    def set_progress(self, f: float): self._progress = max(0.0, min(1.0, f)); self.update()
    def set_time_text(self, t: str): self._time_text = t; self.update()
    def set_label(self, t: str): self._label_text = t; self.update()
    def set_accent(self, c: QColor): self._accent = c; self.update()
    def set_state(self, s: str): self._state = s; self._trail_points.clear(); self.update()

    def set_elapsed_time(self, total_ms: int, total_duration_ms: int):
        total_sec = max(0, total_ms) // 1000
        self._elapsed_secs = total_sec
        self._elapsed_mins = total_sec // 60
        self._elapsed_hrs = total_sec // 3600
        self._total_duration_mins = max(1, total_duration_ms // 60000)

    def trigger_tick_flash(self): self._tick_flash = 1.0
    def trigger_minute_flash(self): self._minute_flash = 1.0; self._tick_flash = 1.0
    def trigger_hour_flash(self): self._hour_flash = 1.0; self._minute_flash = 1.0; self._tick_flash = 1.0
    def trigger_warning_flash(self): self._warning_flash = 1.0

    def _hsv_color(self, h, s, v, a=255):
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return QColor(int(r * 255), int(g * 255), int(b * 255), a)

    def _pulse_tick(self):
        self._pulse_phase += 0.05
        self._hue_shift = (self._hue_shift + 0.15) % 360
        self._tick_flash = max(0.0, self._tick_flash - 0.06)
        self._minute_flash = max(0.0, self._minute_flash - 0.03)
        self._hour_flash = max(0.0, self._hour_flash - 0.015)
        self._warning_flash = max(0.0, self._warning_flash - 0.04)
        if self._state == "running" and self._progress > 0.001:
            angle_rad = math.radians(90 - self._progress * 360)
            r = 120
            self._trail_points.append((r*math.cos(angle_rad), -r*math.sin(angle_rad), 1.0))
            if len(self._trail_points) > 25: self._trail_points.pop(0)
        elif self._state != "running" and self._trail_points:
            self._trail_points = [(x,y,a-0.05) for x,y,a in self._trail_points if a > 0.05]
        self.update()

    def _draw_tick_ring(self, p, count, inner_r, outer_r, elapsed, color_dim, color_lit, color_glow, show_labels=False, ring_hue=None):
        for i in range(count):
            angle_deg = (360.0 / count) * i - 90
            angle = math.radians(angle_deg)
            is_major = count <= 12 or i % 5 == 0
            is_major_12 = count <= 12 or i % (count // 12) == 0
            ir = inner_r - 4 if is_major else inner_r
            orr = outer_r + 2 if is_major else outer_r
            x1, y1 = ir * math.cos(angle), ir * math.sin(angle)
            x2, y2 = orr * math.cos(angle), orr * math.sin(angle)

            lit = i < elapsed
            flash_boost = 1.0 if (lit and i == elapsed - 1 and self._tick_flash > 0.5) else 0.0

            if lit:
                alpha = min(255, int(180 + 75 * pulse) + int(100 * flash_boost))
                if ring_hue is not None:
                    tick_hue = (ring_hue + i * (360.0 / count)) % 360
                    c = self._hsv_color(tick_hue, 0.85, 0.9, alpha)
                else:
                    c = QColor(color_lit); c.setAlpha(alpha)
                w = 2.5 if is_major else 1.5
                p.setPen(QPen(c, w))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

                if is_major:
                    mx, my = (inner_r + outer_r) / 2 * math.cos(angle), (inner_r + outer_r) / 2 * math.sin(angle)
                    glow = QRadialGradient(mx, my, 8 + 4 * flash_boost)
                    if ring_hue is not None:
                        gc = self._hsv_color((ring_hue + i * (360.0 / count)) % 360, 0.9, 0.7, int(60 + 80 * flash_boost))
                    else:
                        gc = QColor(color_glow); gc.setAlpha(int(60 + 80 * flash_boost))
                    glow.setColorAt(0, gc); glow.setColorAt(1, QColor(0, 0, 0, 0))
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow)
                    p.drawEllipse(QPointF(mx, my), 8 + 4 * flash_boost, 8 + 4 * flash_boost)
            else:
                p.setPen(QPen(color_dim, 2 if is_major else 1))
                p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            if show_labels and is_major:
                lr = outer_r + 14
                lx, ly = lr * math.cos(angle), lr * math.sin(angle)
                num = str(i if count <= 12 else i // 5) if i > 0 else ("12" if count <= 12 else "60")
                if count > 12 and i == 0: num = "0"
                elif count > 12: num = str(i // 5 * 5)
                p.setPen(QColor(color_lit) if lit else QColor(60, 50, 90))
                p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold) if is_major_12 else QFont("Segoe UI", 7))
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(num)
                th = fm.height()
                p.drawText(QRectF(lx - tw/2, ly - th/2, tw, th), Qt.AlignmentFlag.AlignCenter, num)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        p.translate(self.width()/2, self.height()/2); sc = side/400.0; p.scale(sc, sc)
        pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)
        is_run = self._state == "running"; is_fin = self._state == "finished"
        hue = self._hue_shift

        # Warning flash (red burst for countdown < 10s)
        if self._warning_flash > 0.01:
            flash = QRadialGradient(0, 0, 180)
            fc = QColor(255, 40, 40, int(70 * self._warning_flash))
            flash.setColorAt(0.65, QColor(0,0,0,0))
            flash.setColorAt(0.85, fc)
            flash.setColorAt(1.0, QColor(0,0,0,0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(flash)
            p.drawEllipse(-185, -185, 370, 370)

        # Hour flash
        if self._hour_flash > 0.01:
            for i in range(3):
                ring_hue = (hue + i * 120) % 360
                flash = QRadialGradient(0, 0, 180 + i * 10)
                fc = self._hsv_color(ring_hue, 0.9, 0.8, int(50 * self._hour_flash))
                flash.setColorAt(0.7, QColor(0,0,0,0))
                flash.setColorAt(0.85, fc)
                flash.setColorAt(1.0, QColor(0,0,0,0))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(flash)
                p.drawEllipse(-190, -190, 380, 380)
        elif self._minute_flash > 0.01:
            flash = QRadialGradient(0, 0, 170)
            fc = self._hsv_color((hue + 60) % 360, 0.8, 0.7, int(60 * self._minute_flash))
            flash.setColorAt(0.7, QColor(0,0,0,0))
            flash.setColorAt(0.88, fc)
            flash.setColorAt(1.0, QColor(0,0,0,0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(flash)
            p.drawEllipse(-180, -180, 360, 360)
        elif self._tick_flash > 0.01:
            flash = QRadialGradient(0, 0, 175)
            fc = self._hsv_color(hue, 0.8, 0.7, int(40 * self._tick_flash))
            flash.setColorAt(0.7, QColor(0,0,0,0))
            flash.setColorAt(0.88, fc)
            flash.setColorAt(1.0, QColor(0,0,0,0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(flash)
            p.drawEllipse(-175, -175, 350, 350)

        if is_run or is_fin:
            gs = 35 + int(25*pulse) if is_run else int(50*pulse)
            for i in range(2):
                glow_hue = (hue + i * 180) % 360
                glow = QRadialGradient(0, 0, 180)
                gc = self._hsv_color(glow_hue, 0.7, 0.6, gs)
                glow.setColorAt(0.82, QColor(0,0,0,0)); glow.setColorAt(0.94, gc); glow.setColorAt(1.0, QColor(0,0,0,0))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(glow); p.drawEllipse(-180, -180, 360, 360)

        # Ring labels
        p.setPen(self._hsv_color(hue, 0.4, 0.4)); p.setFont(QFont("Segoe UI", 7))
        p.drawText(QRectF(-12, -158, 24, 12), Qt.AlignmentFlag.AlignCenter, "HRS")
        p.drawText(QRectF(-16, -140, 32, 12), Qt.AlignmentFlag.AlignCenter, "MIN")
        p.drawText(QRectF(-16, -120, 32, 12), Qt.AlignmentFlag.AlignCenter, "SEC")

        self._draw_tick_ring(p, count=12, inner_r=165, outer_r=175,
            elapsed=min(self._elapsed_hrs, 12),
            color_dim=QColor(50, 45, 30), color_lit=QColor(255, 200, 60),
            color_glow=QColor(255, 200, 60), show_labels=True, ring_hue=30)

        mins_in_hour = self._elapsed_mins % 60
        self._draw_tick_ring(p, count=60, inner_r=146, outer_r=156,
            elapsed=mins_in_hour,
            color_dim=QColor(35, 25, 50), color_lit=QColor(160, 80, 200),
            color_glow=QColor(160, 80, 200), show_labels=False, ring_hue=270)

        secs_in_min = self._elapsed_secs % 60
        self._draw_tick_ring(p, count=60, inner_r=128, outer_r=138,
            elapsed=secs_in_min,
            color_dim=QColor(20, 40, 50), color_lit=QColor(83, 168, 182),
            color_glow=QColor(83, 168, 182), show_labels=False, ring_hue=170)

        # Progress arc
        p.setPen(QPen(QColor(20,15,40), 8)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(-118, -118, 236, 236)

        if self._progress > 0.001:
            conic = QConicalGradient(0, 0, 90)
            num_colors = 12
            for i in range(num_colors + 1):
                frac = i / num_colors
                arc_hue = (hue + frac * 360) % 360
                conic.setColorAt(frac, self._hsv_color(arc_hue, 0.9, 0.95))
            pen = QPen(QBrush(conic), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            span = -self._progress * 360 * 16
            p.drawArc(QRectF(-118, -118, 236, 236), 90 * 16, int(span))

            for tx, ty, alpha in self._trail_points:
                trail_hue = (hue + self._progress * 360) % 360
                tc = self._hsv_color(trail_hue, 0.9, 0.8, int(150 * alpha))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(tc)
                p.drawEllipse(QPointF(tx, ty), 4 * alpha, 4 * alpha)

            angle_rad = math.radians(90 - self._progress * 360)
            dx, dy = 118 * math.cos(angle_rad), -118 * math.sin(angle_rad)
            tip_hue = (hue + self._progress * 360) % 360
            eg = QRadialGradient(dx, dy, 24)
            eg.setColorAt(0, self._hsv_color(tip_hue, 0.9, 1.0, 200))
            eg.setColorAt(0.3, self._hsv_color(tip_hue, 0.8, 0.7, 80))
            eg.setColorAt(1, self._hsv_color(tip_hue, 0.7, 0.5, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(eg)
            p.drawEllipse(QPointF(dx, dy) - QPointF(24, 24), 48, 48)
            p.setBrush(QColor(255, 255, 255, 220))
            p.drawEllipse(QPointF(dx, dy), 4, 4)

        # Inner circle
        ig = QRadialGradient(0, 0, 108)
        ig.setColorAt(0, self._hsv_color(hue, 0.3, 0.12))
        ig.setColorAt(1, self._hsv_color((hue + 180) % 360, 0.3, 0.08))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(ig); p.drawEllipse(-106, -106, 212, 212)
        p.setPen(QPen(self._hsv_color(hue, 0.3, 0.25, 80), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(-92, -92, 184, 184)

        # Elapsed
        eh, em, es = self._elapsed_hrs, self._elapsed_mins % 60, self._elapsed_secs % 60
        elapsed_str = f"{eh}h {em}m {es}s elapsed"
        p.setPen(self._hsv_color((hue + 60) % 360, 0.4, 0.4)); p.setFont(QFont("Consolas", 8))
        p.drawText(QRectF(-70, -80, 140, 14), Qt.AlignmentFlag.AlignCenter, elapsed_str)

        # Time text
        p.setPen(QColor(0, 0, 0, 80)); p.setFont(QFont("Segoe UI", 44, QFont.Weight.Bold))
        p.drawText(QRectF(-120, -48, 240, 68), Qt.AlignmentFlag.AlignCenter, self._time_text)
        if is_fin:
            tc = self._hsv_color((hue + 330) % 360, 0.9, 0.95, int(200 + 55 * pulse))
        elif self._warning_flash > 0.3:
            tc = QColor(255, int(60 + 140 * self._warning_flash), 60)
        elif is_run:
            tc = self._hsv_color(hue, 0.6, 1.0)
        else:
            tc = QColor(224, 210, 240)
        p.setPen(tc)
        p.drawText(QRectF(-122, -50, 240, 68), Qt.AlignmentFlag.AlignCenter, self._time_text)

        # Label
        if is_fin:
            lc = self._hsv_color((hue + 330) % 360, 0.9, 0.9, int(180 + 75 * pulse))
        elif is_run:
            lc = self._hsv_color(hue, 0.7, 0.85, int(160 + 60 * pulse))
        else:
            lc = QColor(140, 120, 170)
        p.setPen(lc); lf = QFont("Segoe UI", 11); lf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(lf); p.drawText(QRectF(-120, 22, 240, 26), Qt.AlignmentFlag.AlignCenter, self._label_text)

        # Percentage
        pct_hue = (hue + self._progress * 120) % 360
        p.setPen(self._hsv_color(pct_hue, 0.5, 0.5)); p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(-120, 44, 240, 18), Qt.AlignmentFlag.AlignCenter, f"{int(self._progress * 100)}%")
        p.end()


# ═══════════════════════════════════════════════════════════════════════════
#  Strudel Web Panel
# ═══════════════════════════════════════════════════════════════════════════
class StrudelPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        self._web_view = None
        if WEBENGINE_AVAILABLE:
            self._web_view = QWebEngineView()
            html_path = Path(__file__).parent / "_strudel_panel.html"
            html_path.write_text(STRUDEL_PANEL_HTML, encoding="utf-8")
            self._web_view.setUrl(QUrl.fromLocalFile(str(html_path.absolute())))
            layout.addWidget(self._web_view)
        else:
            fb = QLabel("\n  Strudel WebEngine not available.\n\n  Install: sudo apt install libxtst6\n\n  Timer works fine without it.\n")
            fb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fb.setStyleSheet("color:#a090b8;font-size:13px;font-family:'Consolas',monospace;padding:20px;background:#0a0818;border-radius:10px;border:1px solid #3a2050;")
            layout.addWidget(fb)

    def _run_js(self, js: str):
        if self._web_view:
            self._web_view.page().runJavaScript(js)

    def play_pattern(self, code: str):
        import json
        self._run_js(f"window.postMessage({{type:'strudel-play',code:{json.dumps(code)}}},'*');")

    def stop_pattern(self):
        self._run_js("window.postMessage({type:'strudel-stop'},'*');")

    def play_tick_sound(self, sound_type: str = "click", freq: float = 800, dur: float = 0.06, vol: float = 0.15, secs: int = 10):
        import json
        msg = f"{{type:'tick-sound',sound:{json.dumps(sound_type)},freq:{freq},dur:{dur},vol:{vol}"
        if sound_type == "warning":
            msg += f",secs:{secs}"
        msg += "}"
        self._run_js(f"window.postMessage({msg},'*');")

    def set_volume(self, vol: float):
        self._run_js(f"window.postMessage({{type:'set-volume',volume:{vol}}},'*');")

    def play_tick_pattern(self, code: str):
        import json
        self._run_js(f"window.postMessage({{type:'tick-pattern-play',code:{json.dumps(code)}}},'*');")

    def stop_tick_pattern(self):
        self._run_js("window.postMessage({type:'tick-pattern-stop'},'*');")


# ═══════════════════════════════════════════════════════════════════════════
#  Main Window
# ═══════════════════════════════════════════════════════════════════════════
class TimerState:
    IDLE = "idle"; RUNNING = "running"; PAUSED = "paused"; FINISHED = "finished"


class StrudelTimerApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strudel Timer — Psychedelic Edition v2")
        self.setMinimumSize(QSize(1100, 720))
        self.resize(QSize(1350, 820))

        self._state = TimerState.IDLE
        self._mode = "countdown"
        self._total_seconds = 25 * 60
        self._remaining_ms = 25 * 60 * 1000
        self._stopwatch_ms = 0
        self._use_strudel = True
        self._sessions = 0
        self._last_tick_sec = -1
        self._last_tick_min = -1
        self._last_tick_hour = -1
        self._tick_sound_on = True
        self._tick_pattern_on = True

        # Lap/split tracking
        self._laps: list[tuple[int, str]] = []  # (lap_number, time_str)
        self._lap_start_ms = 0

        # Pomodoro auto-cycle
        self._auto_cycle = False
        self._pomodoro_phase = "work"  # "work" or "break"
        self._pomodoro_work_secs = 25 * 60
        self._pomodoro_break_secs = 5 * 60
        self._pomodoro_rounds = 0

        # Fullscreen state
        self._is_fullscreen = False
        self._normal_geometry = None

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(100)
        self._tick_timer.timeout.connect(self._on_tick)
        self._elapsed = QElapsedTimer()

        self._build_ui()
        self._setup_shortcuts()
        self._update_display()
        self.statusBar().showMessage("Ready  |  Space=Start  R=Reset  L=Lap  F11=Fullscreen  T=On-Top  Esc=Quit")

    def _build_ui(self):
        self._bg = PsychedelicBackground(); self._bg.setObjectName("_bg")
        self._celebration = CelebrationOverlay()
        self._border_glow = PulsingBorder()

        central = QWidget(); central.setObjectName("central"); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # Title
        self._title = GradientTitle(); root.addWidget(self._title)
        # Visualizer
        self._visualizer = AudioVisualizer(); root.addWidget(self._visualizer)
        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#3a2060;border:none;border-top:1px solid #3a2060;")
        root.addWidget(sep)

        content = QHBoxLayout(); content.setContentsMargins(14, 10, 14, 14); content.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ═══ LEFT PANEL ═══
        left = QWidget(); left.setFixedWidth(420)
        lv = QVBoxLayout(left); lv.setContentsMargins(0, 0, 0, 0); lv.setSpacing(6)

        # Mode
        mr = QHBoxLayout(); mr.addWidget(QLabel("Mode:"))
        self._mode_combo = QComboBox(); self._mode_combo.addItems(["Countdown", "Stopwatch"])
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mr.addWidget(self._mode_combo, 1); lv.addLayout(mr)

        # Presets
        pg = QGroupBox("Presets"); pgl = QGridLayout(pg); pgl.setSpacing(6)
        self._preset_buttons = {}
        for i, name in enumerate(PRESETS):
            b = QPushButton(name); b.setObjectName("presetBtn"); b.setCheckable(True)
            b.clicked.connect(lambda _, n=name: self._on_preset(n))
            pgl.addWidget(b, i // 2, i % 2); self._preset_buttons[name] = b
        cr = QHBoxLayout(); cr.addWidget(QLabel("Min:"))
        self._custom_min = QSpinBox(); self._custom_min.setRange(1, 999); self._custom_min.setValue(25)
        cr.addWidget(self._custom_min, 1)
        sb = QPushButton("Set"); sb.setObjectName("presetBtn"); sb.clicked.connect(self._on_custom_preset)
        cr.addWidget(sb); pgl.addLayout(cr, 2, 0, 1, 2)
        lv.addWidget(pg); self._preset_buttons["Pomodoro (25m)"].setChecked(True)

        # Session counter
        self._session_counter = SessionCounter(max_sessions=8); lv.addWidget(self._session_counter)

        # Clock + Timer row
        clock_timer_row = QHBoxLayout(); clock_timer_row.setSpacing(8)
        self._clock = AnalogClock(); self._clock.setFixedWidth(160); self._clock.setMinimumHeight(160)
        clock_timer_row.addWidget(self._clock)
        self._circle = CircularTimer(); clock_timer_row.addWidget(self._circle, 1)
        lv.addLayout(clock_timer_row, 1)

        # Controls
        ctrl = QHBoxLayout(); ctrl.setSpacing(10); ctrl.addStretch()
        self._lap_btn = QPushButton("Lap"); self._lap_btn.setObjectName("smallBtn")
        self._lap_btn.setEnabled(False)
        self._lap_btn.clicked.connect(self._on_lap)
        self._start_btn = QPushButton("Start"); self._start_btn.setObjectName("startBtn")
        self._start_btn.clicked.connect(self._on_start_pause)
        self._reset_btn = QPushButton("Reset"); self._reset_btn.setObjectName("resetBtn")
        self._reset_btn.clicked.connect(self._on_reset)
        # Pin (always-on-top) button
        self._pin_btn = QPushButton("Pin"); self._pin_btn.setObjectName("smallBtn")
        self._pin_btn.setCheckable(True)
        self._pin_btn.toggled.connect(self._on_toggle_on_top)
        self._pin_btn.setToolTip("Toggle always-on-top (T)")
        ctrl.addWidget(self._lap_btn)
        ctrl.addWidget(self._start_btn)
        ctrl.addWidget(self._reset_btn)
        ctrl.addWidget(self._pin_btn)
        ctrl.addStretch()
        lv.addLayout(ctrl)

        # Lap times list (compact, only visible in stopwatch or after laps recorded)
        self._lap_list = QListWidget()
        self._lap_list.setMaximumHeight(80)
        self._lap_list.hide()
        lv.addWidget(self._lap_list)

        # ── Settings row: Checkboxes + Volume ──
        chk_row = QHBoxLayout()
        self._strudel_check = QCheckBox("Finish pattern"); self._strudel_check.setChecked(True)
        self._strudel_check.toggled.connect(lambda v: setattr(self, '_use_strudel', v))
        self._tick_sound_check = QCheckBox("Tick sound"); self._tick_sound_check.setChecked(True)
        self._tick_sound_check.toggled.connect(lambda v: setattr(self, '_tick_sound_on', v))
        self._tick_pattern_check = QCheckBox("Tick pattern"); self._tick_pattern_check.setChecked(True)
        self._tick_pattern_check.toggled.connect(lambda v: setattr(self, '_tick_pattern_on', v))
        self._auto_cycle_check = QCheckBox("Auto-cycle"); self._auto_cycle_check.setChecked(False)
        self._auto_cycle_check.setToolTip("Auto-start break after work, work after break (Pomodoro)")
        self._auto_cycle_check.toggled.connect(lambda v: setattr(self, '_auto_cycle', v))
        chk_row.addWidget(self._strudel_check)
        chk_row.addWidget(self._tick_sound_check)
        chk_row.addWidget(self._tick_pattern_check)
        chk_row.addWidget(self._auto_cycle_check)
        lv.addLayout(chk_row)

        # ── Volume + Background Intensity sliders ──
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Volume:"))
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(70)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.setToolTip("Master volume for tick sounds")
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        slider_row.addWidget(self._volume_slider)
        self._vol_label = QLabel("70%")
        self._vol_label.setFixedWidth(35)
        slider_row.addWidget(self._vol_label)

        slider_row.addSpacing(12)
        slider_row.addWidget(QLabel("BG:"))
        self._bg_slider = QSlider(Qt.Orientation.Horizontal)
        self._bg_slider.setRange(0, 100)
        self._bg_slider.setValue(80)
        self._bg_slider.setFixedWidth(80)
        self._bg_slider.setToolTip("Background animation intensity")
        self._bg_slider.valueChanged.connect(self._on_bg_intensity_changed)
        slider_row.addWidget(self._bg_slider)
        self._bg_label = QLabel("80%")
        self._bg_label.setFixedWidth(35)
        slider_row.addWidget(self._bg_label)
        lv.addLayout(slider_row)

        splitter.addWidget(left)

        # ═══ RIGHT PANEL ═══
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(6)

        # Tick pattern editor
        tg = QGroupBox("Tick Pattern (per-second)")
        tv = QVBoxLayout(tg)
        self._tick_editor = QTextEdit(); self._tick_editor.setPlainText(DEFAULT_TICK_PATTERN)
        self._tick_editor.setPlaceholderText("// Per-second Strudel pattern...")
        self._tick_editor.setMaximumHeight(120)
        tv.addWidget(self._tick_editor)
        tpb = QHBoxLayout()
        self._play_tick_btn = QPushButton("Play Tick Pattern"); self._play_tick_btn.setObjectName("smallBtn")
        self._play_tick_btn.clicked.connect(self._on_play_tick_pattern)
        self._stop_tick_btn = QPushButton("Stop Tick Pattern"); self._stop_tick_btn.setObjectName("smallBtn")
        self._stop_tick_btn.clicked.connect(self._on_stop_tick_pattern)
        tpb.addWidget(self._play_tick_btn); tpb.addWidget(self._stop_tick_btn)
        tv.addLayout(tpb)
        rv.addWidget(tg)

        # Finish pattern editor
        eg = QGroupBox("Finish Pattern (on complete)")
        ev = QVBoxLayout(eg)
        self._editor = QTextEdit(); self._editor.setPlainText(DEFAULT_STRUDEL_PATTERN)
        self._editor.setPlaceholderText("// Type your Strudel mini-notation here...")
        self._editor.setMaximumHeight(120)
        ev.addWidget(self._editor)
        pb = QHBoxLayout()
        self._play_btn = QPushButton("Play Finish Pattern"); self._play_btn.setObjectName("smallBtn")
        self._play_btn.clicked.connect(self._on_play_pattern)
        self._stop_btn = QPushButton("Stop Pattern"); self._stop_btn.setObjectName("smallBtn")
        self._stop_btn.clicked.connect(self._on_stop_pattern)
        pb.addWidget(self._play_btn); pb.addWidget(self._stop_btn)
        ev.addLayout(pb)
        rv.addWidget(eg)

        # Web panel
        self._strudel_panel = StrudelPanel(); rv.addWidget(self._strudel_panel, 1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 830])
        content.addWidget(splitter); root.addLayout(content, 1)

        # Overlay layers (bottom to top: bg -> border -> celebration)
        self._bg.setParent(central); self._bg.lower()
        self._border_glow.setParent(central); self._border_glow.raise_()
        self._border_glow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._celebration.setParent(central); self._celebration.raise_()
        self._celebration.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _setup_shortcuts(self):
        """Register keyboard shortcuts."""
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_start_pause)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._on_reset)
        QShortcut(QKeySequence(Qt.Key.Key_L), self, self._on_lap)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self._toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_T), self, lambda: self._pin_btn.toggle())
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)

    # ── Overlay geometry ──
    def resizeEvent(self, event):
        super().resizeEvent(event)
        r = self.centralWidget().rect()
        if hasattr(self, '_bg') and self._bg: self._bg.setGeometry(r)
        if hasattr(self, '_border_glow') and self._border_glow: self._border_glow.setGeometry(r)
        if hasattr(self, '_celebration') and self._celebration: self._celebration.setGeometry(r)

    # ── Helpers ──
    def _ms_to_str(self, ms: int) -> str:
        total = max(0, ms) // 1000; m, s = divmod(total, 60); cs = (ms % 1000) // 10
        return f"{m:02d}:{s:02d}.{cs:02d}" if self._mode == "stopwatch" else f"{m:02d}:{s:02d}"

    def _current_second(self) -> int:
        if self._mode == "countdown":
            return self._remaining_ms // 1000
        return self._stopwatch_ms // 1000

    def _current_minute(self) -> int:
        if self._mode == "countdown":
            return self._remaining_ms // 60000
        return self._stopwatch_ms // 60000

    def _current_hour(self) -> int:
        if self._mode == "countdown":
            return self._remaining_ms // 3600000
        return self._stopwatch_ms // 3600000

    def _elapsed_total_sec(self) -> int:
        if self._mode == "countdown":
            return max(0, (self._total_seconds * 1000 - self._remaining_ms)) // 1000
        return self._stopwatch_ms // 1000

    def _update_display(self):
        if self._mode == "countdown":
            self._circle.set_time_text(self._ms_to_str(self._remaining_ms))
            elapsed_ms = self._total_seconds * 1000 - self._remaining_ms
            frac = 1.0 - (self._remaining_ms / (self._total_seconds * 1000)) if self._total_seconds > 0 else 0.0
            self._circle.set_progress(frac)
            self._circle.set_elapsed_time(elapsed_ms, self._total_seconds * 1000)
        else:
            self._circle.set_time_text(self._ms_to_str(self._stopwatch_ms))
            self._circle.set_progress((self._stopwatch_ms % 60000) / 60000.0)
            self._circle.set_elapsed_time(self._stopwatch_ms, self._stopwatch_ms + 60000)

    def _set_state(self, state: str):
        self._state = state
        labels = {
            TimerState.IDLE: ("READY", "Start"), TimerState.RUNNING: ("RUNNING", "Pause"),
            TimerState.PAUSED: ("PAUSED", "Resume"), TimerState.FINISHED: ("DONE!", "Start"),
        }
        lt, bt = labels[state]
        self._circle.set_label(lt); self._circle.set_state(state); self._start_btn.setText(bt)
        self._border_glow.set_active(state == TimerState.RUNNING)

        # Lap button only enabled in stopwatch mode
        self._lap_btn.setEnabled(self._mode == "stopwatch" and state in (TimerState.RUNNING, TimerState.PAUSED))

        if state == TimerState.FINISHED:
            self._circle.set_accent(QColor(255, 80, 180))
            self._visualizer.set_active(True)
            self._visualizer.set_warning(False)
            self._border_glow.set_warning(False)
            self._celebration.trigger()
            self._sessions += 1; self._session_counter.set_count(self._sessions)
            if self._tick_pattern_on:
                self._strudel_panel.stop_tick_pattern()
            self._on_timer_finished()
        elif state == TimerState.RUNNING:
            self._circle.set_accent(QColor(160, 80, 255))
            self._visualizer.set_active(True)
            self._visualizer.set_warning(False)
            self._border_glow.set_warning(False)
            self._celebration.stop()
            self._last_tick_sec = -1
            self._last_tick_min = -1
            self._last_tick_hour = -1
            # Reset lap start
            if self._mode == "stopwatch" and not self._laps:
                self._lap_start_ms = 0
            if self._tick_pattern_on:
                code = self._tick_editor.toPlainText().strip()
                if code:
                    self._strudel_panel.play_tick_pattern(code)
            phase_label = "Running..." if self._mode == "countdown" else "Stopwatch running..."
            if self._auto_cycle and self._mode == "countdown":
                phase_label = f"Running... ({self._pomodoro_phase.capitalize()} phase, round {self._pomodoro_rounds + 1})"
            self.statusBar().showMessage(phase_label)
        elif state == TimerState.PAUSED:
            self._visualizer.set_active(False)
            self._visualizer.set_warning(False)
            self._border_glow.set_warning(False)
            if self._tick_pattern_on:
                self._strudel_panel.stop_tick_pattern()
            self.statusBar().showMessage("Paused")
        else:
            self._circle.set_accent(QColor(160, 80, 255))
            self._visualizer.set_active(False)
            self._visualizer.set_warning(False)
            self._border_glow.set_warning(False)
            self._celebration.stop()
            if self._tick_pattern_on:
                self._strudel_panel.stop_tick_pattern()
            self.statusBar().showMessage("Ready  |  Space=Start  R=Reset  L=Lap  F11=Fullscreen  T=On-Top  Esc=Quit")

    # ── Slots ──
    def _on_mode_changed(self, text: str):
        self._on_reset()
        self._mode = "countdown" if text == "Countdown" else "stopwatch"
        cd = self._mode == "countdown"
        for b in self._preset_buttons.values(): b.setEnabled(cd)
        self._custom_min.setEnabled(cd)
        # Show/hide lap list
        self._lap_list.setVisible(self._mode == "stopwatch")
        self._update_display()

    def _on_preset(self, name: str):
        if self._mode != "countdown": return
        for n, b in self._preset_buttons.items(): b.setChecked(n == name)
        self._total_seconds = PRESETS[name]; self._remaining_ms = self._total_seconds * 1000
        if "25m" in name: self._pomodoro_work_secs = self._total_seconds
        elif "5m" in name: self._pomodoro_break_secs = self._total_seconds
        self._tick_timer.stop()
        if self._state != TimerState.IDLE: self._set_state(TimerState.IDLE)
        self._update_display(); self.statusBar().showMessage(f"Preset: {name}")

    def _on_custom_preset(self):
        m = self._custom_min.value(); self._total_seconds = m * 60
        self._remaining_ms = self._total_seconds * 1000
        for b in self._preset_buttons.values(): b.setChecked(False)
        self._tick_timer.stop()
        if self._state != TimerState.IDLE: self._set_state(TimerState.IDLE)
        self._update_display(); self.statusBar().showMessage(f"Custom: {m} minutes")

    def _on_start_pause(self):
        if self._state in (TimerState.IDLE, TimerState.FINISHED):
            if self._mode == "countdown":
                self._remaining_ms = self._total_seconds * 1000
            else:
                self._stopwatch_ms = 0
                self._laps.clear()
                self._lap_list.clear()
                self._lap_start_ms = 0
            self._elapsed.start(); self._tick_timer.start()
            self._set_state(TimerState.RUNNING)
        elif self._state == TimerState.RUNNING:
            self._tick_timer.stop()
            if self._mode == "stopwatch": self._stopwatch_ms += self._elapsed.elapsed()
            self._set_state(TimerState.PAUSED)
        elif self._state == TimerState.PAUSED:
            self._elapsed.start(); self._tick_timer.start()
            self._set_state(TimerState.RUNNING)

    def _on_reset(self):
        self._tick_timer.stop()
        if self._mode == "countdown":
            self._remaining_ms = self._total_seconds * 1000
        else:
            self._stopwatch_ms = 0
            self._laps.clear()
            self._lap_list.clear()
            self._lap_start_ms = 0
        self._set_state(TimerState.IDLE); self._update_display()

    def _on_lap(self):
        """Record a lap/split time in stopwatch mode."""
        if self._mode != "stopwatch": return
        if self._state not in (TimerState.RUNNING, TimerState.PAUSED): return

        current_ms = self._stopwatch_ms
        lap_num = len(self._laps) + 1
        time_str = self._ms_to_str(current_ms)

        # Calculate delta from last lap
        if self._laps:
            last_total = self._laps[-1][1]  # the stored ms value
            delta_ms = current_ms - last_total
            delta_str = self._ms_to_str(delta_ms)
        else:
            delta_str = time_str

        # Store (lap_num, total_ms) for delta calculation
        self._laps.append((lap_num, current_ms))

        # Add to list widget
        item_text = f"  Lap {lap_num:>3d}   {time_str}   (+{delta_str})"
        item = QListWidgetItem(item_text)
        self._lap_list.addItem(item)
        self._lap_list.scrollToBottom()

        # Flash visualizer
        self._visualizer.trigger_spike(1.2)
        self.statusBar().showMessage(f"Lap {lap_num} recorded: {time_str} (split: {delta_str})")

    def _on_toggle_on_top(self, checked: bool):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()  # required after changing window flags
        self._pin_btn.setText("Unpin" if checked else "Pin")
        self.statusBar().showMessage("Always-on-top: " + ("ON" if checked else "OFF"))

    def _toggle_fullscreen(self):
        if self._is_fullscreen:
            self.showNormal()
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self._is_fullscreen = False
            self.statusBar().showMessage("Exited fullscreen")
        else:
            self._normal_geometry = self.geometry()
            self.showFullScreen()
            self._is_fullscreen = True
            self.statusBar().showMessage("Fullscreen (F11 to exit)")

    def _on_volume_changed(self, val: int):
        self._vol_label.setText(f"{val}%")
        vol = val / 100.0
        self._strudel_panel.set_volume(vol)

    def _on_bg_intensity_changed(self, val: int):
        self._bg_label.setText(f"{val}%")
        self._bg.set_intensity(val / 100.0)

    def _on_tick(self):
        cur_sec = self._current_second()

        if self._mode == "countdown":
            self._remaining_ms -= 100
            if self._remaining_ms <= 0:
                self._remaining_ms = 0; self._tick_timer.stop(); self._set_state(TimerState.FINISHED)
        else:
            self._stopwatch_ms += 100

        # Countdown warning: last 10 seconds
        in_warning = False
        if self._mode == "countdown" and self._state == TimerState.RUNNING and cur_sec <= 10:
            in_warning = True

        # Update warning state
        self._visualizer.set_warning(in_warning)
        self._border_glow.set_warning(in_warning)

        if self._state == TimerState.RUNNING and cur_sec != self._last_tick_sec:
            self._last_tick_sec = cur_sec

            elapsed_sec = self._elapsed_total_sec()
            current_min = elapsed_sec // 60
            current_hr = elapsed_sec // 3600

            # ── Countdown WARNING (last 10 seconds) ──
            if in_warning:
                self._circle.trigger_warning_flash()
                self._visualizer.trigger_spike(1.5 + (10 - cur_sec) * 0.15)
                if self._tick_sound_on:
                    self._strudel_panel.play_tick_sound("warning", secs=cur_sec)
                # Skip normal tick — warning replaces it
                self._update_display()
                return

            # ── Check for HOUR tick ──
            if self._last_tick_hour != -1 and current_hr != self._last_tick_hour:
                self._last_tick_hour = current_hr
                self._circle.trigger_hour_flash()
                self._visualizer.trigger_spike(2.5)
                if self._tick_sound_on:
                    self._strudel_panel.play_tick_sound("hour")

            # ── Check for MINUTE tick ──
            elif self._last_tick_min != -1 and current_min != self._last_tick_min:
                self._last_tick_min = current_min
                self._circle.trigger_minute_flash()
                self._visualizer.trigger_spike(1.8)
                if self._tick_sound_on:
                    self._strudel_panel.play_tick_sound("minute")

            # ── Regular SECOND tick ──
            else:
                self._circle.trigger_tick_flash()
                self._visualizer.trigger_spike(1.0)
                if self._tick_sound_on:
                    remaining = cur_sec if self._mode == "countdown" else cur_sec
                    if remaining % 5 == 0:
                        freq = 660 + (elapsed_sec % 60) * 4
                        self._strudel_panel.play_tick_sound("note", freq=freq, dur=0.12)
                    else:
                        self._strudel_panel.play_tick_sound("click")

        self._update_display()

    def _on_timer_finished(self):
        if self._use_strudel:
            pattern = self._editor.toPlainText().strip()
            if pattern:
                self._strudel_panel.play_pattern(pattern)
                self.statusBar().showMessage("Timer complete! Playing finish pattern...")
        self.activateWindow()
        try: QApplication.beep()
        except: pass

        # ── Pomodoro auto-cycle ──
        if self._auto_cycle and self._mode == "countdown":
            QTimer.singleShot(2000, self._auto_cycle_next)

    def _auto_cycle_next(self):
        """Auto-start the next phase in Pomodoro cycle."""
        if not self._auto_cycle:
            return

        if self._pomodoro_phase == "work":
            # Switch to break
            self._pomodoro_phase = "break"
            self._total_seconds = self._pomodoro_break_secs
            self.statusBar().showMessage(f"Auto-cycle: starting {self._pomodoro_break_secs // 60}min break (round {self._pomodoro_rounds + 1})")
        else:
            # Switch to work
            self._pomodoro_phase = "work"
            self._pomodoro_rounds += 1
            self._total_seconds = self._pomodoro_work_secs
            self.statusBar().showMessage(f"Auto-cycle: starting {self._pomodoro_work_secs // 60}min work (round {self._pomodoro_rounds + 1})")

        self._remaining_ms = self._total_seconds * 1000
        self._elapsed.start()
        self._tick_timer.start()
        self._set_state(TimerState.RUNNING)
        self._update_display()

    def _on_play_pattern(self):
        code = self._editor.toPlainText().strip()
        if code:
            self._strudel_panel.play_pattern(code)
            self._visualizer.set_active(True)
            self.statusBar().showMessage("Playing finish pattern...")

    def _on_stop_pattern(self):
        self._strudel_panel.stop_pattern()
        if self._state != TimerState.RUNNING: self._visualizer.set_active(False)
        self.statusBar().showMessage("Pattern stopped.")

    def _on_play_tick_pattern(self):
        code = self._tick_editor.toPlainText().strip()
        if code:
            self._strudel_panel.play_tick_pattern(code)
            self._visualizer.set_active(True)
            self.statusBar().showMessage("Playing tick pattern...")

    def _on_stop_tick_pattern(self):
        self._strudel_panel.stop_tick_pattern()
        if self._state != TimerState.RUNNING: self._visualizer.set_active(False)
        self.statusBar().showMessage("Tick pattern stopped.")


# ═══════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv); app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(10, 8, 24))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(232, 224, 240))
    pal.setColor(QPalette.ColorRole.Base, QColor(10, 8, 24))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 20, 50))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(232, 224, 240))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(232, 224, 240))
    pal.setColor(QPalette.ColorRole.Text, QColor(232, 224, 240))
    pal.setColor(QPalette.ColorRole.Button, QColor(30, 20, 50))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(232, 224, 240))
    pal.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 180))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(160, 80, 255))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(20, 10, 40))
    app.setPalette(pal); app.setStyleSheet(STYLESHEET)
    win = StrudelTimerApp(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()