"""v1.6.6: two closing asks (comment/subscribe vs tag-a-friend/like) split by quiz, voiced and drawn consistently."""
import unittest

from PIL import Image, ImageDraw

from georush import cta, render
from georush.audio import voice_plan, _voice_clip
from georush.catalog import Catalog
from georush.quiz import build_quiz


class CtaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()
        cls.quizzes = [build_quiz(cls.catalog, None, seed=seed)['questions'] for seed in range(40)]

    def test_variant_is_deterministic_and_order_free_and_both_appear(self):
        names = set()
        for questions in self.quizzes:
            codes = [q['country_code'] for q in questions]
            self.assertEqual(cta.variant(codes), cta.variant(list(reversed(codes))))
            self.assertEqual(cta.choose(questions)[3], cta.variant(codes))
            names.add(cta.variant(codes))
        self.assertEqual(names, {'A', 'B'})

    def test_only_three_question_quizzes_can_use_the_tag_ask(self):
        self.assertEqual(cta.variant(['us', 'fr']), 'A')
        self.assertEqual(cta.variant(['us', 'fr', 'de', 'jp']), 'A')

    def test_texts_and_voice_keys(self):
        for questions in self.quizzes:
            line1, line2, key, name = cta.choose(questions)
            if name == 'A':
                self.assertEqual((line1, line2, key), ('COMMENT YOUR SCORE + COUNTRY!', 'LIKE & SUBSCRIBE FOR MORE!', 'outro'))
            else:
                self.assertEqual((line1, line2, key), ("TAG A FRIEND WHO CAN'T GET 3/3!", 'LIKE & SUBSCRIBE IF YOU GOT 3/3!', 'outro_tag'))
            self.assertEqual(voice_plan(questions)[-1][1], key)  # the spoken ask matches the written one
            self.assertIsNotNone(_voice_clip(key), key)

    def test_both_asks_fit_the_yellow_banner_on_the_last_answer(self):
        draw = ImageDraw.Draw(Image.new('RGB', (10, 10)))
        for line, size in ((cta.TEXT_B[0].format(n=3), 40), (cta.TEXT_B[1].format(n=3), 38),
                           (cta.TEXT_A[0], 40), (cta.TEXT_A[1], 38)):
            fitted = render._center(draw, line, 0, size, max_width=790)
            self.assertGreaterEqual(fitted, 30, line)  # still readable on a phone

    def test_last_answer_board_draws_the_chosen_ask(self):
        for questions in self.quizzes[:6]:
            context = render.prepare_animation(questions)
            line1, line2, _, name = cta.choose(questions)
            self.assertEqual(context['cta_variant'], name)
            plain = render._question_static(questions[-1], 2, 3, context['background'], True, cta=(line1, line2))
            other = render._question_static(questions[-1], 2, 3, context['background'], True,
                                            cta=('SOMETHING ELSE', 'ENTIRELY DIFFERENT'))
            self.assertNotEqual(plain.tobytes(), other.tobytes())

    def test_default_ask_is_the_original_when_none_is_given(self):
        question = self.quizzes[0][-1]
        context = render.prepare_animation(self.quizzes[0])
        default = render._question_static(question, 2, 3, context['background'], True)
        original = render._question_static(question, 2, 3, context['background'], True,
                                           cta=('COMMENT YOUR SCORE + COUNTRY!', 'LIKE & SUBSCRIBE FOR MORE!'))
        self.assertEqual(default.tobytes(), original.tobytes())


if __name__ == '__main__':
    unittest.main()
