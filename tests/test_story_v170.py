import copy
import json
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image

from georush import audio, render
from georush.catalog import Catalog
from georush.paths import resource_root
from georush.quiz import build_quiz, validate_quiz
from georush.stories import is_verified, text_hash, verified_stories
from georush.textvariants import short_texts


def clip_seconds(key):
    with wave.open(str(resource_root()/'assets'/'voice'/f'{key}.wav')) as clip:
        return clip.getnframes()/clip.getframerate()


class StoryTests(unittest.TestCase):
    def test_only_cross_checked_sentences_are_usable(self):
        data = json.loads((resource_root()/'assets'/'flag_stories.json').read_text(encoding='utf-8'))
        good = verified_stories()
        self.assertGreater(len(good), 100)
        for code, item in data.items():
            self.assertEqual(code in good, is_verified(item), code)
        item = copy.deepcopy(data['jp'])
        self.assertTrue(is_verified(item))
        item['text'] += ' Edited.'
        self.assertFalse(is_verified(item), 'an edited sentence must be checked again')
        self.assertFalse(is_verified({'text': 'x', 'source': 's', 'checked': text_hash('x')}), 'needs a second source')
        for code in ('mx', 'tr', 'ar'):  # disputed between the two sources
            self.assertNotIn(code, good)

    def test_every_story_has_a_clip_that_fits_its_question_and_the_screen(self):
        image = Image.new('RGB', (render.WIDTH, render.HEIGHT))
        for code, text in verified_stories().items():
            need = audio.COUNTDOWN_SECONDS+.08+clip_seconds('name_'+code)+.15+clip_seconds('story_'+code)
            self.assertLessEqual(need, audio.STORY_QUESTION_SECONDS-.2, code)
            render._story_panel(image, text, 1345)  # raises when the sentence cannot fit

    def test_story_quiz_mixes_three_ways_to_play(self):
        catalog = Catalog()
        stories = verified_stories()
        for seed in range(30):
            quiz = build_quiz(catalog, seed=seed, theme='Story')
            self.assertEqual(sorted(str(q.get('kind')) for q in quiz['questions']), ['None', 'find', 'zoom'])
            for question in quiz['questions']:
                self.assertEqual(question['story'], stories[question['country_code']])
        tampered = copy.deepcopy(quiz)
        tampered['questions'][0]['story'] = 'Something nobody checked.'
        with self.assertRaises(ValueError):
            validate_quiz(tampered, catalog)

    def test_voices_never_overlap_and_the_ask_is_not_cut(self):
        catalog = Catalog()
        with tempfile.TemporaryDirectory() as folder:
            for seed in range(12):
                questions = build_quiz(catalog, seed=seed, theme='Story')['questions']
                report = audio.synthesize_audio(Path(folder)/'a.wav', 3, .10, questions)
                voices = [e for e in report['events'] if e['kind'] == 'voice']
                self.assertEqual(sum(e['clip'].startswith('story_') for e in voices), 3)
                for first, second in zip(voices, voices[1:]):
                    self.assertLessEqual(first['time_seconds']+first['duration_seconds'], second['time_seconds']+.001, seed)
                last = voices[-1]
                self.assertTrue(last['clip'].startswith('outro'))
                self.assertLess(last['time_seconds']+last['duration_seconds'], report['duration']-.2)

    def test_other_themes_keep_their_timing_and_text_credits_the_check(self):
        quiz = build_quiz(Catalog(), seed=1, theme='Find')
        self.assertEqual(audio.timing(quiz['questions']), (audio.QUESTION_SECONDS, audio.CTA_SECONDS))
        self.assertFalse(any('story' in q for q in quiz['questions']))
        title, description, tags, _ = short_texts('sig', 3, 'Mixed', 'Story', 98)
        self.assertIn('#98', title)
        self.assertIn('second reference', description)
        self.assertNotIn('World Bank', description)


if __name__ == '__main__':
    unittest.main()
