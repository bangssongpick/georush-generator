"""Bounded one-second synthesis chunks using GeoRush's original pentatonic palette."""
import math
import wave
import numpy as np
from ..audio import SAMPLE_RATE
from .timeline import COUNTDOWN


def synthesize(destination,timeline,bgm=.10):
    if bgm not in (.08,.10,.12):
        raise ValueError('BGM 볼륨 오류')
    events=[]
    for item in timeline['segments']:
        start=item['start']
        if item['kind']=='question':
            events.append({'kind':'entrance','time':start+.12,'length':.14,'frequency':740,'gain':.06})
            for tick in range(COUNTDOWN):
                events.append({'kind':'tick','time':start+tick,'length':.075,'frequency':1000 if tick<6 else 1250,'gain':.065})
            for step,freq in enumerate((523.251,659.255,783.991)):
                events.append({'kind':'answer','time':start+COUNTDOWN+step*.065,'length':.24,'frequency':freq,'gain':.10})
        elif item['kind'] in ('chapter','outro'):
            events.append({'kind':item['kind'],'time':start,'length':.4,'frequency':659.255,'gain':.08})
    duration=timeline['duration'];peak=0.;clipped=0
    notes=(261.6256,329.6276,391.9954,493.8833,391.9954,329.6276,293.6648,391.9954)
    with wave.open(str(destination),'wb') as out:
        out.setnchannels(2);out.setsampwidth(2);out.setframerate(SAMPLE_RATE)
        for second in range(math.ceil(duration)):
            t=np.arange(min(SAMPLE_RATE,round((duration-second)*SAMPLE_RATE)))/SAMPLE_RATE+second
            phase=np.remainder(t,.375)
            freq=np.take(notes,(t/.375).astype(int)%len(notes))
            music=(.55*np.sin(2*np.pi*freq*phase)+.12*np.sin(4*np.pi*freq*phase))
            music*=np.minimum(phase/.014,1)*np.exp(-phase*8)*np.clip((.34-phase)/.04,0,1)*bgm
            bass_phase=np.remainder(t,1.5)
            music+=.30*np.sin(2*np.pi*65.4064*bass_phase)*np.minimum(bass_phase/.018,1)*np.exp(-bass_phase*7)*bgm
            signal=music
            for event in events:
                if event['time']<second+1 and event['time']+event['length']>second:
                    local=t-event['time'];inside=(local>=0)&(local<event['length'])
                    envelope=np.minimum(np.maximum(local,0)/.012,1)*np.clip((event['length']-local)/.06,0,1)*np.exp(-np.maximum(local,0)*4)
                    signal=signal+inside*event['gain']*envelope*np.sin(2*np.pi*event['frequency']*local)
            signal*=np.minimum(t/.08,1)*np.clip((duration-t)/.8,0,1)
            peak=max(peak,float(np.max(np.abs(signal))))
            clipped+=int(np.sum(np.abs(signal)>=1))*2
            pcm=np.round(np.clip(signal,-.92,.92)*32767).astype('<i2')
            out.writeframes(np.repeat(pcm[:,None],2,axis=1).tobytes())
    return {'source':'Original local GeoRush procedural synthesis','duration':duration,'bgm_gain':bgm,
            'peak_before_limiter':peak,'clipped_samples':clipped,'events':events,
            'sample_rate':SAMPLE_RATE,'channels':2,'max_chunk_seconds':1,'end_fade_seconds':.8}
