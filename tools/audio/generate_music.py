#!/usr/bin/env python3
"""
第 47 号磁带 (TAPE 47) - 五大场景背景音乐生成引擎
纯 Python 标准库合成器 (44.1kHz 16-bit 立体声 WAV)
通过物理建模、多谐波加法合成、ADSR包络与立体声声场渲染
"""

import math
import random
import struct
import wave
import sys
import os

SAMPLE_RATE = 44100

def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

class AudioBuffer:
    def __init__(self, duration_sec):
        self.duration_sec = duration_sec
        self.num_samples = int(duration_sec * SAMPLE_RATE)
        self.left = [0.0] * self.num_samples
        self.right = [0.0] * self.num_samples

    def add_sample(self, index, l_val, r_val):
        if 0 <= index < self.num_samples:
            self.left[index] += l_val
            self.right[index] += r_val

    def apply_delay(self, delay_sec=0.35, feedback=0.35, cross_mix=0.5):
        """立体声交错延迟效果"""
        ds = int(delay_sec * SAMPLE_RATE)
        if ds <= 0 or ds >= self.num_samples:
            return
        for i in range(ds, self.num_samples):
            prev_l = self.left[i - ds]
            prev_r = self.right[i - ds]
            # 交叉反馈与阻尼
            self.left[i] += (prev_r * (1.0 - cross_mix) + prev_l * cross_mix) * feedback
            self.right[i] += (prev_l * (1.0 - cross_mix) + prev_r * cross_mix) * feedback

    def save_wav(self, filename, peak_target=0.92):
        # 寻找全局峰值
        peak = 0.0001
        for i in range(self.num_samples):
            peak = max(peak, abs(self.left[i]), abs(self.right[i]))
        
        gain = peak_target / peak
        
        # 自动进退淡化处理：前 1.2 秒平滑淡入，最后 2.5 秒自然淡出
        fade_in = int(1.2 * SAMPLE_RATE)
        fade_out = int(2.5 * SAMPLE_RATE)
        out_start = self.num_samples - fade_out

        raw_bytes = bytearray()
        for i in range(self.num_samples):
            cur_gain = gain
            if i < fade_in:
                cur_gain *= (i / fade_in)
            elif i > out_start:
                cur_gain *= ((self.num_samples - i) / fade_out)

            l = self.left[i] * cur_gain
            r = self.right[i] * cur_gain

            # 模拟母带软削波饱和 (Soft saturation)
            l = math.tanh(l)
            r = math.tanh(r)

            il = max(-32767, min(32767, int(l * 32767.0)))
            ir = max(-32767, min(32767, int(r * 32767.0)))
            raw_bytes += struct.pack("<hh", il, ir)

        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(raw_bytes)
        print(f"-> 导出 WAV 音频: {filename} ({self.duration_sec:.1f}s)")


# ===================== 乐器与音色合成器 =====================

def render_pluck(buf, freq, start_sec, dur_sec, vol=0.15, pan=0.0):
    """拨弦乐器 (竖琴/木吉他)：基频 + 泛音序列，衰减随谐波频率加快"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    # 4 级泛音序列
    harmonics = [(1.0, 1.0, 3.2), (2.0, 0.55, 4.8), (3.0, 0.28, 7.0), (4.0, 0.12, 10.0)]
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        if t > dur_sec:
            break
        # 初始 8ms 轻微击弦噪波瞬态
        noise_click = (random.random() * 2.0 - 1.0) * math.exp(-t * 220.0) * 0.18
        sig = noise_click
        for mult, h_amp, decay_rate in harmonics:
            omega = 2.0 * math.pi * (freq * mult)
            sig += h_amp * math.sin(omega * t) * math.exp(-decay_rate * t)

        sig *= vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_celesta(buf, freq, start_sec, dur_sec, vol=0.12, pan=0.0):
    """水滴钟琴 / 钢片琴：纯净高频基频 + 非整泛音"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    # 金属音叉非整数共振模式
    modes = [(1.0, 1.0, 2.5), (2.756, 0.25, 4.5), (5.404, 0.08, 7.5)]
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # 极快速微瞬态 Attack
        att = min(1.0, t / 0.005)
        sig = 0.0
        for mult, h_amp, decay_rate in modes:
            omega = 2.0 * math.pi * (freq * mult)
            sig += h_amp * math.sin(omega * t) * math.exp(-decay_rate * t)
        sig = sig * att * vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_piano(buf, freq, start_sec, dur_sec, vol=0.18, pan=0.0, tape_flutter=0.0):
    """抒情温暖毛毡钢琴 / 磁带复古钢琴"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    # 钢琴双弦微走音 (Detune)
    detunes = [0.9988, 1.0012]
    harmonics = [(1.0, 1.0, 1.8), (2.0, 0.65, 2.8), (3.0, 0.35, 4.2), (4.0, 0.18, 5.8), (5.0, 0.08, 7.5)]

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        att = min(1.0, t / 0.012)
        # 磁带颤音调制 (Tape Flutter / Wow)
        mod = 0.0
        if tape_flutter > 0.0:
            mod = tape_flutter * (math.sin(2.0 * math.pi * 0.8 * t) * 0.0025 + math.sin(2.0 * math.pi * 4.2 * t) * 0.0015)

        sig = 0.0
        for d in detunes:
            f_d = freq * d * (1.0 + mod)
            for mult, h_amp, decay_rate in harmonics:
                omega = 2.0 * math.pi * (f_d * mult)
                sig += h_amp * math.sin(omega * t) * math.exp(-decay_rate * t)

        sig = sig * 0.5 * att * vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_marimba(buf, freq, start_sec, dur_sec, vol=0.18, pan=0.0):
    """马林巴木琴 / 工坊敲击乐"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    # 木质敲击：第 1 泛音迅速衰减，留下共鸣木腔
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        att = min(1.0, t / 0.004)
        h1 = math.sin(2.0 * math.pi * freq * t) * math.exp(-5.5 * t)
        h2 = 0.5 * math.sin(2.0 * math.pi * (freq * 3.8) * t) * math.exp(-22.0 * t)
        h3 = 0.25 * math.sin(2.0 * math.pi * (freq * 9.2) * t) * math.exp(-40.0 * t)
        # 木棒击打声
        thump = (random.random() * 2.0 - 1.0) * math.exp(-t * 260.0) * 0.25
        sig = (h1 + h2 + h3 + thump) * att * vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_pizz_bass(buf, freq, start_sec, dur_sec, vol=0.22, pan=0.0):
    """低音提琴拨奏 (Pizzicato Bass)"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        att = min(1.0, t / 0.01)
        # 深厚的基音与少量饱满泛音
        b1 = math.sin(2.0 * math.pi * freq * t) * math.exp(-3.2 * t)
        b2 = 0.45 * math.sin(2.0 * math.pi * freq * 2.0 * t) * math.exp(-5.0 * t)
        b3 = 0.15 * math.sin(2.0 * math.pi * freq * 3.0 * t) * math.exp(-8.0 * t)
        sig = (b1 + b2 + b3) * att * vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_pad(buf, freqs, start_sec, dur_sec, vol=0.10, pan=0.0, warm=True):
    """温暖弦乐 / 空灵背景和弦 Pad (缓升缓降)"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    att_len = min(1.2, dur_sec * 0.3)
    rel_len = min(1.5, dur_sec * 0.35)
    rel_start = dur_sec - rel_len

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # ADSR 缓动包络
        if t < att_len:
            env = 0.5 * (1.0 - math.cos(math.pi * t / att_len))
        elif t > rel_start:
            env = 0.5 * (1.0 + math.cos(math.pi * (t - rel_start) / rel_len))
        else:
            env = 1.0

        sig = 0.0
        # 慢速双声道合唱 Chorus
        lfo = math.sin(2.0 * math.pi * 0.35 * t) * 0.003
        for f in freqs:
            f_l = f * (1.0 + lfo)
            f_r = f * (1.0 - lfo)
            # 正弦波与微弱平滑三角波
            sig += math.sin(2.0 * math.pi * f_l * t)
            if warm:
                sig += 0.35 * math.sin(2.0 * math.pi * (f_r * 2.0) * t)

        sig = sig * env * (vol / max(1, len(freqs)))
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_synth_arp(buf, freq, start_sec, dur_sec, vol=0.12, pan=0.0, filter_ratio=1.0):
    """实验室微光电子琶音 (带共振峰滤波感)"""
    start_idx = int(start_sec * SAMPLE_RATE)
    num_samples = int(dur_sec * SAMPLE_RATE)
    pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
    pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        att = min(1.0, t / 0.008)
        dec = math.exp(-6.0 * t)
        # 模拟模拟合成器滤波谐波
        sig = math.sin(2.0 * math.pi * freq * t)
        sig += 0.5 * filter_ratio * math.sin(2.0 * math.pi * freq * 2.0 * t)
        sig += 0.25 * (filter_ratio ** 2) * math.sin(2.0 * math.pi * freq * 3.0 * t)
        sig = sig * att * dec * vol
        buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_water_drops(buf, duration_sec, count=16, vol=0.06):
    """温室随机滴水清音"""
    for _ in range(count):
        st = random.uniform(1.0, duration_sec - 2.0)
        dur = random.uniform(0.15, 0.35)
        # 频率微变水滴 (从微高滑落到基频)
        f0 = random.uniform(1400.0, 2200.0)
        pan = random.uniform(-0.8, 0.8)
        start_idx = int(st * SAMPLE_RATE)
        samples = int(dur * SAMPLE_RATE)
        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)
        for i in range(samples):
            t = i / SAMPLE_RATE
            f_curr = f0 * (1.0 - t * 0.8)
            sig = math.sin(2.0 * math.pi * f_curr * t) * math.exp(-28.0 * t) * vol
            buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)

def render_clockwork_ticks(buf, duration_sec, bpm=96, vol=0.04):
    """维修间微型发条齿轮轻敲声"""
    step_sec = 60.0 / bpm / 2.0 # 8分音符节拍
    t = 0.5
    idx = 0
    while t < duration_sec - 1.0:
        pan = 0.25 if (idx % 2 == 0) else -0.25
        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)
        start_idx = int(t * SAMPLE_RATE)
        f = 2800.0 if (idx % 4 == 0) else 3400.0
        v = vol * (1.2 if (idx % 4 == 0) else 0.7)
        for i in range(int(0.02 * SAMPLE_RATE)):
            tt = i / SAMPLE_RATE
            sig = (math.sin(2.0 * math.pi * f * tt) + (random.random() * 2.0 - 1.0) * 0.4) * math.exp(-tt * 240.0) * v
            buf.add_sample(start_idx + i, sig * pan_l, sig * pan_r)
        t += step_sec
        idx += 1

def render_tape_hiss(buf, duration_sec, vol=0.018):
    """47号磁带真实底噪"""
    num_samples = int(duration_sec * SAMPLE_RATE)
    # 高通滤波粉红噪声
    prev = 0.0
    for i in range(num_samples):
        white = random.random() * 2.0 - 1.0
        # 一阶低通 + 高通模拟带通磁带响应
        pink = prev * 0.65 + white * 0.35
        prev = pink
        sig = (white - pink) * vol
        buf.add_sample(i, sig * 0.9, sig * 1.1)


# ===================== 五大场景音乐编曲 =====================

def compose_scene_01_greenhouse(duration=36.0):
    """
    场景 1：温室 (Greenhouse)
    治愈、晨光、水滴、嫩芽复苏 (F Major, 72 BPM)
    """
    buf = AudioBuffer(duration)
    bpm = 72
    beat = 60.0 / bpm # ≈ 0.833s
    bar = beat * 4.0   # ≈ 3.333s

    # 4 小节循环和弦
    # Fmaj7 -> Dm7 -> Bbmaj7 -> C9sus4 -> Fmaj7
    chord_prog = [
        # (root, bass_midi, chord_midis, name)
        (midi_to_freq(41), [midi_to_freq(53), midi_to_freq(57), midi_to_freq(60), midi_to_freq(64)]), # Fmaj7 (F, A, C, E)
        (midi_to_freq(38), [midi_to_freq(50), midi_to_freq(53), midi_to_freq(57), midi_to_freq(60)]), # Dm7 (D, F, A, C)
        (midi_to_freq(34), [midi_to_freq(46), midi_to_freq(50), midi_to_freq(53), midi_to_freq(57)]), # Bbmaj7 (Bb, D, F, A)
        (midi_to_freq(36), [midi_to_freq(48), midi_to_freq(53), midi_to_freq(55), midi_to_freq(58)]), # C9sus4 (C, F, G, Bb)
    ]

    total_bars = int(duration // bar) + 1
    for b in range(total_bars):
        b_time = b * bar
        if b_time >= duration - 2.0:
            break
        chord_info = chord_prog[b % len(chord_prog)]
        root_f, chord_fs = chord_info

        # 1. 铺底 Pad
        render_pad(buf, chord_fs + [root_f * 2.0], b_time, bar * 1.15, vol=0.07, pan=0.0)

        # 2. 竖琴流动分解和弦 (Harp Plucks: 8 分音符)
        for step in range(8):
            st = b_time + step * (beat / 2.0)
            if st >= duration - 1.5:
                break
            # 琶音音型
            note_idx = [0, 1, 2, 3, 2, 1, 2, 3][step]
            f = chord_fs[note_idx]
            pan = -0.45 + (step % 4) * 0.3
            render_pluck(buf, f, st, beat * 1.4, vol=0.13, pan=pan)

    # 3. 水滴钟琴灵动旋律 (Celesta: 治愈的希望旋律)
    melody_notes = [
        # (bar_offset, midi, dur_beats)
        (0.0, 65, 1.5), (1.5, 69, 1.0), (2.5, 72, 1.5), # F4, A4, C5
        (4.0, 76, 2.0), (6.0, 74, 1.0), (7.0, 72, 1.0), # E5, D5, C5
        (8.0, 69, 1.5), (9.5, 70, 1.0), (10.5, 72, 1.5),# A4, Bb4, C5
        (12.0, 67, 2.5), (15.0, 65, 1.5),               # G4, F4
        # 第二段高潮
        (16.0, 77, 1.5), (17.5, 76, 1.0), (18.5, 74, 1.5), # F5, E5, D5
        (20.0, 72, 2.0), (22.0, 69, 1.5), (23.5, 70, 1.0), # C5, A4, Bb4
        (24.0, 72, 2.0), (26.0, 74, 1.5), (27.5, 76, 1.0), # C5, D5, E5
        (28.0, 77, 3.0), (32.0, 72, 2.5)                   # F5, C5
    ]
    for b_off, midi_n, dur_b in melody_notes:
        st = b_off * beat
        if st < duration - 1.5:
            render_celesta(buf, midi_to_freq(midi_n), st, dur_b * beat * 1.5, vol=0.15, pan=0.2)

    # 4. 环境凝露水滴声
    render_water_drops(buf, duration, count=22, vol=0.06)
    buf.apply_delay(delay_sec=0.42, feedback=0.32, cross_mix=0.6)
    return buf


def compose_scene_02_workshop(duration=36.0):
    """
    场景 2：维修间 (Workshop)
    机械律动、齿轮、专注手工、电焊微光 (A minor, 96 BPM)
    """
    buf = AudioBuffer(duration)
    bpm = 96
    beat = 60.0 / bpm # 0.625s
    bar = beat * 4.0   # 2.5s

    # Am9 -> Fmaj7 -> Dm6 -> E7#9
    chord_prog = [
        ([midi_to_freq(45), midi_to_freq(52), midi_to_freq(55), midi_to_freq(60)], 33), # Am (A2, E3, G3, C4)
        ([midi_to_freq(41), midi_to_freq(48), midi_to_freq(53), midi_to_freq(57)], 29), # Fmaj7 (F2, C3, F3, A3)
        ([midi_to_freq(38), midi_to_freq(45), midi_to_freq(50), midi_to_freq(53)], 26), # Dm (D2, A2, D3, F3)
        ([midi_to_freq(40), midi_to_freq(47), midi_to_freq(52), midi_to_freq(56)], 28), # E7 (E2, B2, E3, G#3)
    ]

    total_bars = int(duration // bar) + 1
    for b in range(total_bars):
        b_time = b * bar
        if b_time >= duration - 2.0:
            break
        chord_fs, bass_m = chord_prog[b % len(chord_prog)]

        # 1. 低音提琴拨奏 (Pizzicato Bass Walking)
        render_pizz_bass(buf, midi_to_freq(bass_m), b_time, beat * 1.2, vol=0.22, pan=-0.2)
        render_pizz_bass(buf, midi_to_freq(bass_m + 7), b_time + beat * 2.0, beat * 1.2, vol=0.18, pan=-0.2)

        # 2. 电钢 Warm Rhodes 和弦铺垫
        render_pad(buf, chord_fs, b_time, bar * 1.05, vol=0.06, pan=0.1, warm=False)

        # 3. 马林巴木琴节奏动机 (Marimba Groove)
        groove_steps = [(0.0, 0), (1.0, 1), (1.5, 2), (2.5, 3), (3.0, 2), (3.5, 1)]
        for g_step, c_idx in groove_steps:
            st = b_time + g_step * beat
            if st < duration - 1.5:
                f = chord_fs[c_idx] * 2.0
                pan = 0.35 if (g_step > 1.5) else -0.35
                render_marimba(buf, f, st, beat * 0.8, vol=0.14, pan=pan)

    # 4. 马林巴主旋律 (富有工匠探索精神的跳跃旋律)
    melody_notes = [
        (4.0, 69, 1.0), (5.0, 72, 0.5), (5.5, 71, 0.5), (6.0, 69, 1.5),
        (8.0, 65, 1.0), (9.0, 67, 1.0), (10.0, 69, 1.5),
        (12.0, 62, 1.0), (13.0, 65, 0.5), (13.5, 64, 0.5), (14.0, 62, 1.5),
        (16.0, 64, 1.0), (17.0, 67, 1.0), (18.0, 68, 1.5),
        # 第二段跃动
        (20.0, 72, 1.0), (21.0, 74, 0.5), (21.5, 76, 0.5), (22.0, 77, 1.5),
        (24.0, 76, 1.0), (25.0, 72, 1.0), (26.0, 69, 1.5),
        (28.0, 65, 1.0), (29.0, 67, 0.5), (29.5, 68, 0.5), (30.0, 69, 2.5)
    ]
    for b_off, m_note, dur_b in melody_notes:
        st = b_off * beat
        if st < duration - 1.5:
            render_marimba(buf, midi_to_freq(m_note + 12), st, dur_b * beat * 1.1, vol=0.18, pan=0.15)

    # 5. 发条与齿轮轻巧滴答声
    render_clockwork_ticks(buf, duration, bpm=bpm, vol=0.035)
    buf.apply_delay(delay_sec=0.31, feedback=0.28, cross_mix=0.4)
    return buf


def compose_scene_03_lab(duration=36.0):
    """
    场景 3：实验室 (Laboratory)
    冷光荧光、离心机、微粒悬浮、理性与求索 (C minor, 80 BPM)
    """
    buf = AudioBuffer(duration)
    bpm = 80
    beat = 60.0 / bpm # 0.75s
    bar = beat * 4.0   # 3.0s

    # Cm9 -> Abmaj7#11 -> Fm9 -> Gsus4 / G
    chord_prog = [
        ([midi_to_freq(48), midi_to_freq(55), midi_to_freq(58), midi_to_freq(62)], midi_to_freq(36)), # Cm9
        ([midi_to_freq(44), midi_to_freq(51), midi_to_freq(55), midi_to_freq(59)], midi_to_freq(32)), # Abmaj7
        ([midi_to_freq(41), midi_to_freq(48), midi_to_freq(51), midi_to_freq(55)], midi_to_freq(29)), # Fm9
        ([midi_to_freq(43), midi_to_freq(50), midi_to_freq(53), midi_to_freq(59)], midi_to_freq(31)), # G7
    ]

    total_bars = int(duration // bar) + 1
    for b in range(total_bars):
        b_time = b * bar
        if b_time >= duration - 2.0:
            break
        chord_fs, sub_bass_f = chord_prog[b % len(chord_prog)]

        # 1. 离心机次低音深沉轰鸣 (Sub Bass Drone)
        render_pad(buf, [sub_bass_f, sub_bass_f * 2.0], b_time, bar * 1.1, vol=0.14, pan=0.0, warm=False)

        # 2. 模拟合成器微光琶音 (Filter Sweep Arp - 16分音符)
        filter_r = 0.5 + 0.5 * math.sin(b * 0.8) # 随小节缓动滤波开合
        for step in range(16):
            st = b_time + step * (beat / 4.0)
            if st >= duration - 1.5:
                break
            # 琶音序列：4 个音上下起伏
            pat = [0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0, 2, 1, 3]
            note_f = chord_fs[pat[step]] * 2.0
            pan = -0.6 + 1.2 * (step % 4) / 3.0 # 立体声左右平移
            render_synth_arp(buf, note_f, st, beat * 0.45, vol=0.08, pan=pan, filter_ratio=filter_r)

    # 3. 水晶玻璃钟音主旋律 (冷峻、深邃、科技微光)
    melody_notes = [
        (0.0, 72, 2.0), (2.0, 75, 1.5), (3.5, 74, 1.5), # C5, Eb5, D5
        (5.0, 70, 2.0), (7.0, 67, 2.0),                 # Bb4, G4
        (9.0, 68, 2.0), (11.0, 70, 1.5), (12.5, 72, 1.5),# Ab4, Bb4, C5
        (14.0, 71, 3.0),                                 # B4
        # 第二段跃升
        (16.0, 79, 2.0), (18.0, 77, 1.5), (19.5, 75, 1.5), # G5, F5, Eb5
        (21.0, 74, 2.0), (23.0, 75, 1.5), (24.5, 72, 1.5), # D5, Eb5, C5
        (26.0, 70, 2.0), (28.0, 68, 1.5), (29.5, 67, 1.5), # Bb4, Ab4, G4
        (31.0, 72, 4.0)                                     # C5
    ]
    for b_off, m_note, dur_b in melody_notes:
        st = b_off * beat
        if st < duration - 1.5:
            render_celesta(buf, midi_to_freq(m_note), st, dur_b * beat * 1.4, vol=0.14, pan=0.1)

    buf.apply_delay(delay_sec=0.375, feedback=0.42, cross_mix=0.7)
    return buf


def compose_scene_04_bridge(duration=38.0):
    """
    场景 4：登舰廊桥 (Boarding Bridge)
    远行星海、离别与眷恋、候船广播提示钟、舷窗微光 (G Major, 65 BPM)
    """
    buf = AudioBuffer(duration)
    bpm = 65
    beat = 60.0 / bpm # 0.923s
    bar = beat * 4.0   # 3.692s

    # Gadd9 -> Em9 -> Cmaj9 -> Dsus4/D
    chord_prog = [
        ([midi_to_freq(43), midi_to_freq(50), midi_to_freq(54), midi_to_freq(57), midi_to_freq(59)], 31), # Gadd9
        ([midi_to_freq(40), midi_to_freq(47), midi_to_freq(50), midi_to_freq(54), midi_to_freq(59)], 28), # Em9
        ([midi_to_freq(36), midi_to_freq(43), midi_to_freq(47), midi_to_freq(52), midi_to_freq(54)], 24), # Cmaj9
        ([midi_to_freq(38), midi_to_freq(45), midi_to_freq(50), midi_to_freq(55), midi_to_freq(57)], 26), # Dsus4->D
    ]

    total_bars = int(duration // bar) + 1
    for b in range(total_bars):
        b_time = b * bar
        if b_time >= duration - 2.0:
            break
        chord_fs, bass_m = chord_prog[b % len(chord_prog)]

        # 1. 室内乐弦乐长音铺垫 (Strings Swell)
        render_pad(buf, chord_fs, b_time, bar * 1.15, vol=0.08, pan=0.0, warm=True)

        # 2. 抒情钢琴低音与流动分解
        render_piano(buf, midi_to_freq(bass_m + 12), b_time, beat * 2.5, vol=0.18, pan=-0.3)
        render_piano(buf, midi_to_freq(bass_m + 19), b_time + beat * 2.0, beat * 2.0, vol=0.14, pan=-0.2)

    # 3. 机场/廊桥专属广播提示双音 ("叮——咚——" B5 -> G5)
    broadcast_cues = [1.0, 18.0]
    for bc_t in broadcast_cues:
        if bc_t < duration - 4.0:
            render_celesta(buf, midi_to_freq(83), bc_t, 2.0, vol=0.15, pan=0.35)        # B5
            render_celesta(buf, midi_to_freq(79), bc_t + 0.65, 2.8, vol=0.14, pan=-0.35) # G5

    # 4. 抒情毛毡钢琴主旋律 (温柔中带着离别的深情)
    melody_notes = [
        (2.0, 71, 1.5), (3.5, 74, 1.0), (4.5, 79, 2.0), # B4, D5, G5
        (7.0, 78, 1.5), (8.5, 74, 1.0), (9.5, 76, 2.0), # F#5, D5, E5
        (12.0, 72, 1.5), (13.5, 74, 1.0), (14.5, 76, 1.5), (16.0, 78, 1.5), # C5, D5, E5, F#5
        (18.0, 79, 3.0),                                                      # G5
        # 情绪升华
        (20.0, 83, 1.5), (21.5, 81, 1.0), (22.5, 79, 1.5), (24.0, 78, 1.5), # B5, A5, G5, F#5
        (26.0, 76, 2.0), (28.0, 74, 1.5), (29.5, 71, 1.5),                   # E5, D5, B4
        (31.0, 72, 2.0), (33.0, 74, 1.5), (34.5, 71, 3.0)                    # C5, D5, B4
    ]
    for b_off, m_note, dur_b in melody_notes:
        st = b_off * beat
        if st < duration - 1.5:
            render_piano(buf, midi_to_freq(m_note), st, dur_b * beat * 1.3, vol=0.20, pan=0.1)

    buf.apply_delay(delay_sec=0.46, feedback=0.35, cross_mix=0.55)
    return buf


def compose_scene_05_station(duration=40.0):
    """
    场景 5：废弃空间站 (Abandoned Space Station)
    4017天的寂静、磁带回旋、核心舱信号「……开……门……」(D minor, 60 BPM)
    """
    buf = AudioBuffer(duration)
    bpm = 60
    beat = 60.0 / bpm # 1.0s
    bar = beat * 4.0   # 4.0s

    # Dm -> Bbmaj7 -> Gm6 -> Asus4 -> A7
    chord_prog = [
        ([midi_to_freq(45), midi_to_freq(50), midi_to_freq(53), midi_to_freq(57)], 26), # Dm (D2, A2, D3, F3)
        ([midi_to_freq(41), midi_to_freq(46), midi_to_freq(50), midi_to_freq(53)], 22), # Bbmaj7 (Bb1, F2, D3, F3)
        ([midi_to_freq(43), midi_to_freq(46), midi_to_freq(50), midi_to_freq(55)], 27), # Gm6 (G1, D2, Bb2, E3)
        ([midi_to_freq(40), midi_to_freq(45), midi_to_freq(49), midi_to_freq(55)], 21), # A7 (A1, E2, G2, C#3)
    ]

    total_bars = int(duration // bar) + 1
    for b in range(total_bars):
        b_time = b * bar
        if b_time >= duration - 2.0:
            break
        chord_fs, bass_m = chord_prog[b % len(chord_prog)]

        # 1. 废弃金属舱室极低频共鸣 (Deep Space Station Sub Drone)
        render_pad(buf, [midi_to_freq(bass_m), midi_to_freq(bass_m + 12)], b_time, bar * 1.15, vol=0.15, pan=0.0, warm=True)

        # 2. 磁带质感慢速和弦 (带 Tape Flutter)
        render_piano(buf, midi_to_freq(bass_m + 12), b_time, beat * 3.5, vol=0.16, pan=-0.25, tape_flutter=0.8)

    # 3. 远方微弱信号回声脉冲 (模拟「……开……门……」信号的摩尔斯/雷达轻鸣)
    signal_cues = [2.0, 5.0, 10.0, 14.0, 18.0, 22.0, 26.0, 30.0]
    for sc_t in signal_cues:
        if sc_t < duration - 2.5:
            # 弱音高频脉冲
            render_celesta(buf, midi_to_freq(86), sc_t, 1.8, vol=0.06, pan=0.4)       # D6
            render_celesta(buf, midi_to_freq(86), sc_t + 0.28, 2.2, vol=0.04, pan=-0.4) # Echo

    # 4. 47号磁带核心主题钢琴旋律 (苍凉、坚定、穿透4017天的深情)
    melody_notes = [
        # 主题音型 (D4 -> F4 -> A4 -> G4 -> F4 -> E4 -> D4)
        (0.0, 62, 2.0), (2.0, 65, 1.5), (3.5, 69, 2.5),
        (6.0, 67, 1.5), (7.5, 65, 1.5), (9.0, 64, 2.0), (11.0, 62, 3.0),
        # 展开
        (14.0, 65, 1.5), (15.5, 69, 1.5), (17.0, 74, 3.0),
        (20.0, 72, 1.5), (21.5, 70, 1.5), (23.0, 69, 2.0), (25.0, 67, 2.0),
        # 升华誓言: "总有人替你按住它"
        (27.0, 70, 2.0), (29.0, 69, 1.5), (30.5, 67, 1.5), (32.0, 65, 2.0),
        (34.0, 64, 2.0), (36.0, 62, 4.0)
    ]
    for b_off, m_note, dur_b in melody_notes:
        st = b_off * beat
        if st < duration - 1.5:
            # 开启磁带抖动与浓厚空间
            render_piano(buf, midi_to_freq(m_note), st, dur_b * beat * 1.4, vol=0.22, pan=0.05, tape_flutter=1.0)

    # 5. 真实磁带底噪 (Tape Hiss)
    render_tape_hiss(buf, duration, vol=0.015)

    buf.apply_delay(delay_sec=0.52, feedback=0.40, cross_mix=0.6)
    return buf


# ===================== 主运行入口 =====================

def main():
    print("========================================")
    print("开始生成《第 47 号磁带》五大场景专属背景音乐")
    print("========================================")

    scenes = [
        ("01_greenhouse", "温室 (Greenhouse)", compose_scene_01_greenhouse, 36.0),
        ("02_workshop", "维修间 (Workshop)", compose_scene_02_workshop, 36.0),
        ("03_lab", "实验室 (Laboratory)", compose_scene_03_lab, 36.0),
        ("04_bridge", "登舰廊桥 (Boarding Bridge)", compose_scene_04_bridge, 38.0),
        ("05_station", "废弃空间站 (Abandoned Space Station)", compose_scene_05_station, 40.0),
    ]

    out_dir = "assets/audio"
    os.makedirs(out_dir, exist_ok=True)

    for prefix, name, comp_func, dur in scenes:
        print(f"\n[作曲编曲中] {name} ...")
        buf = comp_func(duration=dur)
        wav_path = os.path.join(out_dir, f"bgm_{prefix}.wav")
        buf.save_wav(wav_path)

    print("\n所有场景 WAV 生成完毕！")

if __name__ == "__main__":
    main()
