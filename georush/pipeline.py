"""Country selection through validated MP4 and publishing text, entirely local."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
import shutil
import sqlite3
import uuid

from .audio import QUESTION_SECONDS, CTA_SECONDS
from .batchsizes import SHORTS_BATCH_SIZES
from .catalog import Catalog
from .history import History
from .paths import default_output_root, find_ffmpeg, data_root
from .output import get_history, combine_metadata, extract_thumbnail, publish, keep_success_evidence
from .quiz import build_quiz, validate_quiz
from .render import render_video
from .textvariants import short_texts
from .validation import validate_video, extract_encoded_frames


def _write(path, document):
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')


def _metadata(folder, quiz):
    title, description, tags, comment = short_texts(quiz['signature'], len(quiz['questions']), quiz['difficulty'])
    documents = {'title.txt': title+'\n', 'description.txt': description,
                 'tags.txt': tags+'\n', 'pinned_comment.txt': comment+'\n'}
    for name, value in documents.items():
        (folder/name).write_text(value, encoding='utf-8')


def generate_batch(count=1, difficulty='Mixed', questions_per_video=3, bgm_volume=.10,
                   output_root=None, progress_callback=None, seed=None):
    if count not in SHORTS_BATCH_SIZES:
        raise ValueError('제작 편수는 '+' / '.join(str(n) for n in SHORTS_BATCH_SIZES)+' 중에서 선택하세요.')
    if bgm_volume not in (.08, .10, .12):
        raise ValueError('BGM 볼륨은 8% / 10% / 12%입니다.')
    root = Path(output_root if output_root is not None else default_output_root()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f'georush.{uuid.uuid4().hex}')
    logger.setLevel(logging.INFO)
    internal = data_root()
    (internal/'logs').mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(internal/'logs'/'georush.log', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    results = []

    def emit(index, stage, progress, message):
        if progress_callback:
            try:
                progress_callback({'index': index, 'total': count, 'stage': stage,
                                   'progress': progress, 'message': message})
            except Exception:
                logger.exception('진행 상태 표시 오류')
    try:
        catalog = Catalog()
        history = get_history(root)
        ffmpeg = find_ffmpeg()
        for index in range(1, count+1):
            directory = None
            run_id = None
            work = None
            try:
                emit(index, 'prepare', 0.0, f'{index}/{count} 국가·국기 검증 중')
                if shutil.disk_usage(root).free < 256*1024*1024:
                    raise OSError('남은 디스크 공간이 256MB보다 적습니다. 공간을 확보해 주세요.')
                label = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
                directory = root/f'GeoRush_{label}_{uuid.uuid4().hex[:6]}'
                work = internal/'debug'/directory.name
                work.mkdir(parents=True, exist_ok=False)
                for retry in range(8):
                    quiz = build_quiz(catalog, history, difficulty, questions_per_video,
                                      None if seed is None else seed+index-1+retry*1009)
                    validate_quiz(quiz, catalog)
                    try:
                        run_id = history.reserve_quiz(quiz['signature'], difficulty, directory, quiz)
                        break
                    except sqlite3.IntegrityError:
                        if retry == 7:
                            raise ValueError('다른 제작 작업과 문제 구성이 충돌했습니다.')
                _write(work/'quiz_data.json', quiz)
                _metadata(work, quiz)
                for warning in quiz['asset_warnings']:
                    logger.warning(warning)
                report = render_video(quiz, work/'video.mp4', bgm_volume,
                                      lambda event: emit(index, event.get('stage', 'render'),
                                                         event.get('progress', 0)*.90,
                                                         event.get('message', '렌더 중')), ffmpeg)
                emit(index, 'validate', .92, f'{index}/{count} 실제 MP4·오디오 전체 디코딩 검사')
                media = validate_video(work/'video.mp4',
                                       questions_per_video*QUESTION_SECONDS+CTA_SECONDS,
                                       round((questions_per_video*QUESTION_SECONDS+CTA_SECONDS)*30), ffmpeg)
                media['encoded_inspection'] = extract_encoded_frames(work/'video.mp4',
                                                                      work/'encoded_inspection',
                                                                      questions_per_video, ffmpeg)
                validate_quiz(quiz, catalog)
                _write(work/'MEDIA_REPORT.json', media)
                _write(work/'RENDER_REPORT.json', report)
                combine_metadata(work)
                extract_thumbnail(work/'video.mp4', work/'shorts_thumbnail.jpg', ffmpeg)
                publish(work, directory)
                # Success is committed last, after mandatory outputs and real decoding.
                history.finish(run_id, success=True)
                try:
                    keep_success_evidence(work)
                except OSError:
                    logger.exception('성공한 영상의 내부 임시 파일 정리 실패')
                results.append({'status': 'success', 'path': str(directory), 'error': '',
                                'signature': quiz['signature'], 'debug_path': str(work)})
                logger.info('SUCCESS %s', directory.name)
                emit(index, 'success', 1.0, f'{index}/{count} 제작 성공: {directory.name}')
            except Exception as exc:
                error = str(exc)
                logger.exception('FAILED %s', directory.name if directory else index)
                if run_id is not None:
                    try:
                        history.finish(run_id, success=False, error=error)
                    except Exception:
                        logger.exception('실패 이력 기록 오류')
                if work is not None:
                    try:
                        (work/'ERROR.txt').write_text(error+'\n', encoding='utf-8')
                    except OSError:
                        logger.exception('오류 파일 저장 실패')
                results.append({'status': 'failed', 'path': str(work or root), 'error': error})
                emit(index, 'failed', 1.0, f'{index}/{count} 실패: {error}')
                # Continue other videos even if one local render fails.
        return results
    finally:
        handler.close()
        logger.removeHandler(handler)
