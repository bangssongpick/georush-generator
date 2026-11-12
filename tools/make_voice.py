"""Pre-render the GeoRush voice clips with Kokoro (Apache-2.0). Run with the Kokoro Python 3.12 venv:

    <Kokoro venv>\\Scripts\\python.exe tools\\make_voice.py

Writes assets/voice/*.wav (24 kHz mono 16-bit) and assets/voice/voice_manifest.json. The generator only plays
these files; it never runs Kokoro itself, so the EXE needs no extra Python or model.
"""
import json
import os
import re
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
KOKORO_DIR = Path(os.environ.get('KOKORO_TOOL', r'C:\Users\82105\Desktop\뱅으니\롱폼A 역사\도구_Kokoro'))
sys.path.insert(0, str(KOKORO_DIR))

VOICE, SPEED, SR = 'af_heart', 1.08, 24000
PHRASES = {
    'first': 'Can you get all three?',
    'guess': 'Guess the flag!',
    'final': 'Final flag!',
    'zoom': 'Zoomed in! Which flag?',
    'pop_first': 'Which country has the most people?',
    'pop': 'Most people?',
    'outro': 'Comment your score, and subscribe for more!',
}


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def main():
    import numpy as np
    import narrate  # the Kokoro tool's helpers (espeak path fix for non-ASCII folders)
    narrate.fix_espeak()
    from kokoro import KPipeline
    from georush.catalog import Catalog
    from georush.names import display_name
    pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    out = ROOT/'assets'/'voice'
    out.mkdir(parents=True, exist_ok=True)
    texts = dict(PHRASES)
    valid, _ = Catalog().valid_countries()
    for row in valid:
        name = display_name(row['name'])
        texts['name_'+row['code']] = name + '!'
        texts['find_'+row['code']] = f'Find {name}!'
    manifest = {'engine': 'Kokoro-82M (Apache-2.0)', 'voice': VOICE, 'speed': SPEED, 'sample_rate': SR, 'clips': {}}
    for index, (key, text) in enumerate(sorted(texts.items())):
        audio = np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice=VOICE, speed=SPEED)])
        # trim leading/trailing silence so clips line up with the picture
        loud = np.nonzero(np.abs(audio) > .01)[0]
        if len(loud):
            audio = audio[max(0, loud[0]-240):loud[-1]+1200]
        pcm = (np.clip(audio, -1, 1)*32767*.9).astype('<i2')
        with wave.open(str(out/f'{key}.wav'), 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(SR); wav.writeframes(pcm.tobytes())
        manifest['clips'][key] = {'text': text, 'seconds': round(len(pcm)/SR, 3)}
        if index % 25 == 0:
            print(index, key, text, manifest['clips'][key]['seconds'], flush=True)
    (out/'voice_manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding='utf-8')
    print('done', len(manifest['clips']))


if __name__ == '__main__':
    main()
