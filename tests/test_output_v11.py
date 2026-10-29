"""Output-only regressions; fake-render unit checks are not MP4 validation."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from georush import pipeline
from georush.catalog import Catalog
from georush.history import History
from georush.paths import history_path
from georush.output import FINAL_FILES, combine_metadata, get_history
from georush.quiz import build_quiz


class OutputV11Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='GeoRush v11 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.output=self.root/'영상';self.internal=self.root/'내부'
        env=patch.dict(os.environ,{'GEORUSH_DATA_DIR':str(self.internal),'GEORUSH_DEBUG':'0'})
        env.start();self.addCleanup(env.stop)

    def batch(self, fail_thumbnail=False, debug=False):
        def render(quiz, destination, *args):
            p=Path(destination);p.write_bytes(b'unit test MP4 fixture, not playable')
            (p.parent/'original_audio.wav').write_bytes(b'unit WAV fixture')
            (p.parent/'ffmpeg.log').write_text('unit log')
            for name in ('inspection','encoded_inspection'):
                (p.parent/name).mkdir();(p.parent/name/'frame.jpg').write_bytes(b'fixture')
            return {'unit_fixture':True}
        def thumb(video, destination, ffmpeg):
            if fail_thumbnail:raise RuntimeError('thumbnail deliberately failed')
            Image.new('RGB',(1080,1920),'blue').save(destination)
        with patch.object(pipeline,'render_video',side_effect=render),patch.object(pipeline,'validate_video',return_value={'unit_fixture':True}),patch.object(pipeline,'extract_encoded_frames',return_value=[]),patch.object(pipeline,'extract_thumbnail',side_effect=thumb),patch.object(pipeline,'find_ffmpeg',return_value='unused'),patch.dict(os.environ,{'GEORUSH_DEBUG':'1' if debug else '0'}):
            return pipeline.generate_batch(output_root=self.output,count=1,seed=121)[0]

    def test_success_has_exactly_three_files_and_no_public_database(self):
        r=self.batch();self.assertEqual(r['status'],'success')
        final=Path(r['path']);self.assertEqual({p.name for p in final.iterdir()},FINAL_FILES)
        self.assertTrue(all(p.is_file() for p in final.iterdir()))
        self.assertEqual(list(self.output.iterdir()),[final])
        self.assertFalse((self.output/'georush_history.sqlite3').exists())
        self.assertEqual(History(history_path()).list_runs()[0]['status'],'success')

    def test_success_cleans_pcm_video_and_inspection_but_keeps_evidence(self):
        r=self.batch();debug=Path(r['debug_path'])
        for name in ('video.mp4','original_audio.wav','inspection','encoded_inspection'):
            self.assertFalse((debug/name).exists(),name)
        for name in ('quiz_data.json','MEDIA_REPORT.json','RENDER_REPORT.json','ffmpeg.log'):
            self.assertTrue((debug/name).is_file(),name)

    def test_failure_stays_internal_and_preserves_pcm_and_log(self):
        r=self.batch(fail_thumbnail=True);self.assertEqual(r['status'],'failed')
        self.assertEqual(list(self.output.iterdir()),[])
        for name in ('ERROR.txt','original_audio.wav','video.mp4','ffmpeg.log','quiz_data.json'):
            self.assertTrue((Path(r['path'])/name).is_file(),name)
        self.assertEqual(History(history_path()).list_runs()[0]['status'],'failed')

    def test_debug_inspection_is_private_not_a_fourth_public_item(self):
        r=self.batch(debug=True)
        self.assertTrue((Path(r['debug_path'])/'inspection').is_dir())
        self.assertEqual({p.name for p in Path(r['path']).iterdir()},FINAL_FILES)
        self.assertFalse((Path(r['debug_path'])/'original_audio.wav').exists())

    def test_metadata_count_sections_and_answers_for_1_3_5(self):
        for n in (1,3,5):
            q=build_quiz(Catalog(),None,questions_per_video=n,seed=n)
            work=self.root/f'meta{n}';work.mkdir();pipeline._metadata(work,q);combine_metadata(work)
            text=(work/'shorts_metadata.txt').read_text(encoding='utf-8-sig')
            positions=[text.index(h) for h in ('[제목]','[설명]','[고정 댓글]','[태그]','[카테고리]')]
            self.assertEqual(positions,sorted(positions));self.assertIn(str(n),text)
            self.assertIn(f'0/{n}',text);self.assertIn(f'{n}/{n}',text)
            self.assertIn('#GeoRush #GuessTheFlag #FlagQuiz #GeographyQuiz #Shorts',text)
            self.assertIn('GeoRush, GeoRushGames,',text)
            for item in q['questions']:self.assertNotIn(item['country_name'],text)

    def test_legacy_history_import_keeps_original_and_is_idempotent(self):
        self.output.mkdir();old=History(self.output/'georush_history.sqlite3')
        quiz=build_quiz(Catalog(),None,seed=17)
        record=old.reserve_quiz(quiz['signature'],'Mixed',self.output/'old',quiz);old.finish(record,True)
        before=old.path.read_bytes()
        new=get_history(self.output);get_history(self.output)
        self.assertEqual(old.path.read_bytes(),before)
        self.assertEqual(len(new.list_runs()),1);self.assertIn(quiz['signature'],new.used_signatures())

    def test_different_output_roots_share_history_and_no_repeat(self):
        first=self.batch();self.output=self.root/'다른 출력';second=self.batch()
        self.assertNotEqual(first['signature'],second['signature'])
        self.assertEqual(len(History(history_path()).list_runs()),2)

    def test_source_thumbnail_is_jpeg_1080x1920(self):
        r=self.batch()
        with Image.open(Path(r['path'])/'shorts_thumbnail.jpg') as image:
            self.assertEqual(image.format,'JPEG');self.assertEqual(image.size,(1080,1920))
