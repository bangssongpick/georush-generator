"""v1.3.7/v1.4.2: the very first frame already shows the full flag, one challenge line and all four choices."""
import unittest
from unittest.mock import patch

import numpy as np
from PIL import ImageDraw

from georush import render
from georush.catalog import Catalog
from georush.quiz import build_quiz


class FirstScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quiz = build_quiz(Catalog(), None, seed=137)
        cls.context = render.prepare_animation(cls.quiz['questions'])

    def drawn_text(self, second):
        seen = []
        original = ImageDraw.ImageDraw.text

        def measured(draw, xy, text, *args, **kwargs):
            seen.append((str(text), draw.textbbox(xy, text, font=kwargs.get('font'))))
            return original(draw, xy, text, *args, **kwargs)
        with patch.object(ImageDraw.ImageDraw, 'text', measured):
            image = render.animated_frame(self.context, second)
        return image, seen

    def test_frame_zero_shows_question_hook_and_all_four_choices(self):
        image, seen = self.drawn_text(0.0)
        texts = [text for text, _ in seen]
        self.assertIn('CAN YOU GET ALL 3?', texts)
        # The four choices are part of the pre-drawn board: they must be drawn while the board is built, and be the
        # same on frame zero as later in the question (no delayed or changing choices).
        seen_board = []
        original = ImageDraw.ImageDraw.text

        def measured(draw, xy, text, *args, **kwargs):
            seen_board.append(str(text))
            return original(draw, xy, text, *args, **kwargs)
        with patch.object(ImageDraw.ImageDraw, 'text', measured):
            render._question_static(self.quiz['questions'][0], 0, 3, self.context['background'])
        joined = ' '.join(seen_board)  # long names wrap onto two or three drawn lines
        for name in render._question_data(self.quiz['questions'][0])[0]:
            self.assertIn(name, joined)
        options = lambda second: render.animated_frame(self.context, second).crop((60, 1245, 1030, 1605)).tobytes()
        self.assertEqual(options(0.0), options(2.0))
        pixels = np.asarray(image, dtype=np.int16)
        self.assertGreater(float(pixels.mean()), 40)                   # no black frame
        flag = pixels[340:980, 100:980]
        self.assertGreater(int(((flag.max(axis=2) - flag.min(axis=2)) > 35).sum()), 10000)  # coloured flag visible

    def test_no_intro_or_delay_before_the_question(self):
        state = render.animation_state(0.0, 3)
        self.assertFalse(state['cta'])
        self.assertEqual((state['question_index'], state['remaining']), (0, 3))
        self.assertEqual(state['flag_scale'], 1.0)

    def test_flag_pop_is_short_and_stays_inside_the_card(self):
        scales = [render.animation_state(step / 30, 3)['flag_scale'] for step in range(0, 11)]
        self.assertEqual(scales[0], 1.0)
        self.assertLessEqual(max(scales), 1.06 + 1e-9)
        self.assertEqual(render.animation_state(render.FLAG_POP_SECONDS + .01, 3)['flag_scale'], 1.0)
        w, h = self.context['flags'][0].size
        self.assertGreaterEqual((1080 - w * 1.06) / 2, render.FLAG_CARD[0]+4)
        self.assertLessEqual(render.FLAG_CENTER_Y + h * 1.06 / 2, render.FLAG_CARD[3]-4)

    def test_headlines_fit_the_repainted_band_on_every_question(self):
        for second in (0.0, .1, 1.0, 4.5 + 1.0, 9.0 + 1.0):
            _, seen = self.drawn_text(second)
            for text, (x0, _, x1, _) in seen:
                if text in ('CAN YOU GET ALL 3?', 'FINAL FLAG!', 'GUESS THE FLAG!'):
                    self.assertGreaterEqual(x0, 80, text)
                    self.assertLessEqual(x1, 1000, text)

    def test_headline_is_larger_than_before(self):
        self.assertGreaterEqual(render.TITLE_SIZE, 70)


if __name__ == '__main__':
    unittest.main()
