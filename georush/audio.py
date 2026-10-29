"""Original local synthesis for GeoRush: no recordings, downloads or TTS."""
from __future__ import annotations

from pathlib import Path
import math
import wave

import numpy as np

SAMPLE_RATE = 48_000
QUESTION_SECONDS = 6.5
COUNTDOWN_SECONDS = 5.0
CTA_SECONDS = 1.5


def synthesize_audio(destination: Path, question_count: int, bgm_volume: float = .10) -> dict:
    """Write a deterministic stereo PCM track and report its measured peak.

    The selectable gain applies to the original music component before effects
    are mixed. The final limiter only attenuates if necessary; it never clips.
    """
    if bgm_volume not in (.08, .10, .12):
        raise ValueError('BGM volume must be 0.08, 0.10 or 0.12')
    if not 1 <= question_count <= 5:
        raise ValueError('Question count must be between 1 and 5')
    destination = Path(destination)
    duration = QUESTION_SECONDS * question_count + CTA_SECONDS
    size = round(duration * SAMPLE_RATE)
    track = np.zeros((size, 2), dtype=np.float64)
    music = np.zeros_like(track)
    # An original, light pentatonic pattern. No external compositions or files.
    notes = (261.6256, 329.6276, 391.9954, 493.8833, 391.9954, 329.6276, 293.6648, 391.9954)
    beat = .375
    for index in range(math.ceil(duration / beat)):
        start = round(index * beat * SAMPLE_RATE)
        length = min(round(.34 * SAMPLE_RATE), size-start)
        t = np.arange(length) / SAMPLE_RATE
        envelope = np.minimum(t/.014, 1) * np.exp(-t*8)
        tone = (.55*np.sin(2*np.pi*notes[index % len(notes)]*t)
                + .12*np.sin(4*np.pi*notes[index % len(notes)]*t)) * envelope
        pan = .18 if index % 2 else -.18
        music[start:start+length, 0] += tone*(1-pan)
        music[start:start+length, 1] += tone*(1+pan)
    # A quiet synthesized bass pulse makes the original BGM more than a beep.
    for index in range(math.ceil(duration / 1.5)):
        start = round(index*1.5*SAMPLE_RATE)
        length = min(round(.55*SAMPLE_RATE), size-start)
        t = np.arange(length)/SAMPLE_RATE
        bass = .30*np.sin(2*np.pi*65.4064*t)*np.minimum(t/.018,1)*np.exp(-t*7)
        music[start:start+length] += bass[:, None]
    track += music * bgm_volume
    events = []

    def add_tone(at: float, frequencies: tuple[float, ...], seconds: float, gain: float, kind: str):
        start = round(at*SAMPLE_RATE)
        length = min(round(seconds*SAMPLE_RATE), size-start)
        t = np.arange(length)/SAMPLE_RATE
        envelope = np.minimum(t/.012,1) * np.minimum((seconds-t)/.06,1).clip(0,1)
        envelope *= np.exp(-t*4)
        signal = sum(np.sin(2*np.pi*f*t) for f in frequencies)/len(frequencies)*gain*envelope
        track[start:start+length] += signal[:,None]
        events.append({'kind':kind,'time_seconds':at,'duration_seconds':seconds})

    for question in range(question_count):
        base = question*QUESTION_SECONDS
        add_tone(base+.12,(740.0,1110.0),.14,.08,'entrance')
        for tick in range(5):
            add_tone(base+tick,(1000.0 if tick<4 else 1250.0,),.075,.12,'countdown_tick')
        # A short ascending major chord is an original answer reveal cue.
        for step, frequency in enumerate((523.251,659.255,783.991)):
            add_tone(base+COUNTDOWN_SECONDS+step*.065,(frequency,),.24,.15,'correct_answer')
        if question+1 < question_count:
            start = round((base+QUESTION_SECONDS-.16)*SAMPLE_RATE)
            length = round(.16*SAMPLE_RATE)
            t = np.arange(length)/SAMPLE_RATE
            # Deterministic, gently filtered noise; no source recording.
            rng = np.random.default_rng(100+question)
            noise = rng.normal(0,1,length)
            noise = np.convolve(noise,np.ones(9)/9,mode='same')
            noise *= .07*np.sin(np.pi*t/.16)**2
            track[start:start+length] += noise[:,None]
            events.append({'kind':'transition','time_seconds':base+QUESTION_SECONDS-.16,'duration_seconds':.16})
    add_tone(question_count*QUESTION_SECONDS,(659.255,783.991),.42,.11,'cta')
    fade = min(round(.08*SAMPLE_RATE),size)
    track[:fade] *= np.linspace(0,1,fade)[:,None]
    end_fade=min(round(.45*SAMPLE_RATE),size)
    track[-end_fade:] *= np.linspace(1,0,end_fade)[:,None]
    pre_peak = float(np.max(np.abs(track)))
    attenuation = min(1.0, .92/pre_peak) if pre_peak else 1.0
    track *= attenuation
    pcm = np.round(track*32767).astype('<i2')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(destination),'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    return {'source':'Original GeoRush procedural synthesis; no recordings or external music',
            'sample_rate':SAMPLE_RATE,'channels':2,'duration':duration,'bgm_gain':bgm_volume,
            'peak_before_limiter':pre_peak,'limiter_gain':attenuation,
            'peak_pcm':float(np.max(np.abs(pcm.astype(np.float64)))/32767),
            'clipped_samples':int((np.abs(pcm.astype(np.int32))>=32767).sum()),
            'end_fade_seconds':end_fade/SAMPLE_RATE,
            'events':events}
