"""Decode produced video and verify its actual streams, without online services."""
import json
from pathlib import Path
import re
import shutil
import subprocess

from .paths import find_ffmpeg, subprocess_options


def _run(args, timeout=180):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout,
                            **subprocess_options())
    if result.returncode:
        raise RuntimeError('영상 검증 실패: '+result.stderr[-2500:])
    return result


def validate_video(path, expected_duration=21.0, expected_frames=630, ffmpeg_path=None):
    path = Path(path)
    ffmpeg = str(ffmpeg_path or find_ffmpeg())
    if not path.is_file() or path.stat().st_size < 1000:
        raise ValueError('출력 MP4가 없거나 비정상입니다.')
    probe = shutil.which('ffprobe')
    if probe:
        raw = _run([probe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)])
        document = json.loads(raw.stdout)
        video = next(stream for stream in document['streams'] if stream['codec_type'] == 'video')
        audio = next(stream for stream in document['streams'] if stream['codec_type'] == 'audio')
        duration = float(document['format']['duration'])
        width, height = video['width'], video['height']
        num, den = video['avg_frame_rate'].split('/')
        fps = float(num)/float(den)
        video_codec, audio_codec = video['codec_name'], audio['codec_name']
        pixel_format = video['pix_fmt']
        channel_count = audio['channels']
        probe_method = 'ffprobe'
    else:
        # imageio-ffmpeg on Windows includes ffmpeg, not ffprobe. Parse actual
        # stream headers and count every decoded frame; never skip validation.
        raw = _run([ffmpeg, '-hide_banner', '-i', str(path), '-t', '0.001', '-f', 'null', '-'])
        text = raw.stderr
        duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', text)
        video_line = next(line for line in text.splitlines() if 'Video:' in line)
        audio_line = next(line for line in text.splitlines() if 'Audio:' in line)
        if not duration_match:
            raise ValueError('FFmpeg에서 영상 길이를 확인하지 못했습니다.')
        hh, mm, ss = map(float, duration_match.groups())
        duration = hh*3600+mm*60+ss
        width, height = map(int, re.search(r' (\d{2,5})x(\d{2,5})(?:[ ,\[])', video_line).groups())
        fps = float(re.search(r'([\d.]+) fps', video_line).group(1))
        video_codec = re.search(r'Video: (\w+)', video_line).group(1)
        audio_codec = re.search(r'Audio: (\w+)', audio_line).group(1)
        pixel_format = 'yuv420p' if 'yuv420p' in video_line else 'unknown'
        channel_count = 2 if 'stereo' in audio_line else 1
        probe_method = 'ffmpeg_stream_header_and_full_decode'
    decoded = _run([ffmpeg, '-hide_banner', '-v', 'error', '-xerror', '-i', str(path),
                    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-', '-progress', 'pipe:1'])
    counts = re.findall(r'^frame=(\d+)', decoded.stdout, re.MULTILINE)
    decoded_frames = int(counts[-1]) if counts else -1
    stats = _run([ffmpeg, '-hide_banner', '-i', str(path), '-vn', '-af',
                  'astats=metadata=0:reset=0', '-f', 'null', '-'])
    peaks = re.findall(r'Peak level dB: (-?[\d.]+)', stats.stderr)
    rms_values = re.findall(r'RMS level dB: (-?[\d.]+)', stats.stderr)
    peak_db = max(map(float, peaks)) if peaks else None
    rms_db = max(map(float, rms_values)) if rms_values else None
    checks = {'duration': abs(duration-expected_duration) <= .08,
              'resolution': (width, height) == (1080, 1920),
              'fps': abs(fps-30) < .001, 'decoded_frames': decoded_frames == expected_frames,
              'h264': video_codec == 'h264', 'aac': audio_codec == 'aac',
              'pixel_format': pixel_format == 'yuv420p', 'stereo': channel_count == 2,
              'audio_not_silent': rms_db is not None and rms_db > -75,
              'audio_below_full_scale': peak_db is not None and peak_db < -.05}
    report = {'checks': checks, 'duration': duration, 'width': width, 'height': height,
              'fps': fps, 'frames': decoded_frames, 'video_codec': video_codec,
              'audio_codec': audio_codec, 'pixel_format': pixel_format,
              'decoded_audio_peak_dbfs': peak_db, 'decoded_audio_rms_dbfs': rms_db,
              'probe_method': probe_method, 'full_video_audio_decode': True,
              'size_bytes': path.stat().st_size}
    if not all(checks.values()):
        raise ValueError('MP4 규격 또는 오디오 검사 실패: '+json.dumps(report, ensure_ascii=False))
    return report


def extract_encoded_frames(path, output_folder, question_count=3, ffmpeg_path=None):
    from .audio import QUESTION_SECONDS, COUNTDOWN_SECONDS
    ffmpeg = str(ffmpeg_path or find_ffmpeg())
    output = Path(output_folder)
    output.mkdir(exist_ok=True, parents=True)
    times = []
    for number in range(question_count):
        base = number*QUESTION_SECONDS
        for label, offset in (('start', 0), ('countdown', 2), ('answer', COUNTDOWN_SECONDS+.2)):
            times.append((f'q{number+1}_{label}', base+offset))
    times.append(('cta', question_count*QUESTION_SECONDS+.3))
    for name, second in times:
        _run([ffmpeg, '-hide_banner', '-v', 'error', '-y', '-ss', str(second), '-i', str(path),
              '-frames:v', '1', '-q:v', '2', str(output/(name+'.jpg'))], timeout=60)
    return [{'file': name+'.jpg', 'time_seconds': second} for name, second in times]
