"""Pre-render assets/voice/story_<code>.wav for the cross-checked stories (Kokoro venv Python, same voice as make_voice).

Clips of sentences that are no longer verified are removed, so the voice can never say something the screen may not show.
"""
import json, wave

import make_voice as mv

import numpy as np
import narrate

narrate.fix_espeak()
from kokoro import KPipeline

from georush.stories import is_verified

folder = mv.ROOT/'assets'/'voice'
stories = {code: item['text'] for code, item in
           json.loads((mv.ROOT/'assets'/'flag_stories.json').read_text(encoding='utf-8')).items() if is_verified(item)}
for stale in folder.glob('story_*.wav'):
    if stale.stem[6:] not in stories:
        stale.unlink()
pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
lengths = {}
for code, text in sorted(stories.items()):
    audio = np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice=mv.VOICE, speed=mv.SPEED)])
    loud = np.nonzero(np.abs(audio) > .01)[0]
    audio = audio[max(0, loud[0]-240):loud[-1]+1200]
    pcm = (np.clip(audio, -1, 1)*32767*.9).astype('<i2')
    with wave.open(str(folder/f'story_{code}.wav'), 'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(mv.SR); wav.writeframes(pcm.tobytes())
    lengths[code] = len(pcm)/mv.SR
print('clips', len(lengths), 'longest', max((round(v, 2), c) for c, v in lengths.items()))
