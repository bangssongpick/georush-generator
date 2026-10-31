"""v1.3.6: keep viewers watching - hook on the first flag, shorter questions, easy-to-hard order, final-flag tease."""
import unittest

from georush import render
from georush.audio import COUNTDOWN_SECONDS, COUNTDOWN_TICKS, CTA_SECONDS, QUESTION_SECONDS
from georush.catalog import Catalog
from georush.quiz import TIER_ORDER, build_quiz


class RetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_shorter_questions_keep_the_three_second_call_to_action(self):
        self.assertEqual((QUESTION_SECONDS, COUNTDOWN_SECONDS, CTA_SECONDS), (5.5, 4.0, 3.0))
        self.assertEqual(COUNTDOWN_TICKS, 4)
        self.assertEqual(3 * QUESTION_SECONDS + CTA_SECONDS, 19.5)       # was 22.5
        self.assertEqual(QUESTION_SECONDS - COUNTDOWN_SECONDS, 1.5)      # the answer is still shown for 1.5 s

    def test_headlines_hook_first_tease_last(self):
        self.assertEqual(render._headline(0, 3), ('GUESS THE FLAG!', 'Can you get all 3?'))
        self.assertEqual(render._headline(1, 3), ('GUESS THE FLAG!', 'Which country is this?'))
        self.assertEqual(render._headline(2, 3), ('FINAL FLAG!', 'Get it right for a perfect score!'))
        self.assertEqual(render._headline(0, 1), ('GUESS THE FLAG!', 'Which country is this?'))
        self.assertEqual(render._headline(0, 5)[1], 'Can you get all 5?')
        self.assertEqual(render._headline(4, 5)[0], 'FINAL FLAG!')

    def test_frames_show_the_headlines_and_stay_different_between_questions(self):
        quiz = build_quiz(self.catalog, None, seed=7)
        context = render.prepare_animation(quiz['questions'])
        first = render.animated_frame(context, 1.0).crop((60, 232, 1020, 420)).tobytes()
        middle = render.animated_frame(context, QUESTION_SECONDS + 1.0).crop((60, 232, 1020, 420)).tobytes()
        last = render.animated_frame(context, 2 * QUESTION_SECONDS + 1.0).crop((60, 232, 1020, 420)).tobytes()
        self.assertEqual(len({first, middle, last}), 3)

    def test_mixed_quizzes_go_from_easy_to_hard(self):
        for seed in range(60):
            quiz = build_quiz(self.catalog, None, 'Mixed', 3, seed)
            ranks = [TIER_ORDER[q['difficulty']] for q in quiz['questions']]
            self.assertEqual(ranks, sorted(ranks), (seed, [q['difficulty'] for q in quiz['questions']]))
        for seed in range(20):
            quiz = build_quiz(self.catalog, None, 'Mixed', 5, seed)
            ranks = [TIER_ORDER[q['difficulty']] for q in quiz['questions']]
            self.assertEqual(ranks, sorted(ranks))

    def test_ordering_does_not_change_the_composition_signature(self):
        quiz = build_quiz(self.catalog, None, 'Mixed', 3, 11)
        from georush.quiz import composition_signature
        self.assertEqual(quiz['signature'], composition_signature(list(reversed(quiz['questions']))))

    def test_single_tier_quiz_keeps_a_valid_order(self):
        for level in ('Easy', 'Normal', 'Hard'):
            quiz = build_quiz(self.catalog, None, level, 3, 5)
            self.assertEqual({q['difficulty'] for q in quiz['questions']}, {level})


if __name__ == '__main__':
    unittest.main()
