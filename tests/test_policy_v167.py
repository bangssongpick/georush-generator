"""v1.6.7: no made-up statistics in anything a viewer reads or hears, and a verifiable fact line on the answer screen."""
import re
import unittest

from georush import hooks, render, textvariants
from georush.catalog import Catalog
from georush.quiz import build_quiz

# Statistics, "most people ..." and "only experts ..." cannot be verified, so they read as misleading metadata.
CLAIM = re.compile(r"\d\s*%|most people (miss|fail|get|guess|mix)|only (flag |the real )?experts|nobody|everyone", re.I)  # "has the most people?" is a question, not a claim


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


class NoMadeUpClaimsTests(unittest.TestCase):
    def test_hooks_and_voice_lines(self):
        for text, key in hooks.HOOKS:
            self.assertIsNone(CLAIM.search(text), text)
        for key, line in hooks.VOICE_LINES.items():
            self.assertIsNone(CLAIM.search(line), line)

    def test_badges_and_headlines(self):
        quiz = build_quiz(Catalog(), None, seed=3, theme='Find')['questions']
        for index in range(3):
            self.assertIsNone(CLAIM.search(render._subline(index, 3, quiz[index])))
        self.assertEqual(render._subline(0, 3, quiz[0]), 'ONLY 1 IS RIGHT!')

    def test_every_title_and_comment_pool(self):
        pools = [textvariants.THEME_TITLES, textvariants.COMMENTS, textvariants.CAPITAL_COMMENTS]
        for pool in pools:
            for text in _strings(pool):
                self.assertIsNone(CLAIM.search(text), text)
        for seed in range(60):
            title, description, _, _ = textvariants.short_texts(f's{seed}', 3, 'Mixed')
            self.assertIsNone(CLAIM.search(title), title)


class FactsLineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()

    def test_facts_for_flag_questions_only(self):
        find = build_quiz(self.catalog, None, seed=2, theme='Find')['questions'][0]
        facts = render._facts(find)
        self.assertIn('people', facts)  # population from the pinned World Bank file
        self.assertIsNone(render._facts({'kind': 'capital', 'country_code': 'fr'}))
        self.assertIsNone(render._facts({'kind': 'population', 'country_code': 'fr'}))
        fr = render._facts({'country_code': 'fr'})
        self.assertTrue(fr.startswith('Capital: Paris · ') and fr.endswith('M people'), fr)

    def test_reveal_draws_the_fact_and_the_credit_but_the_question_does_not(self):
        questions = build_quiz(self.catalog, None, seed=2, theme='Find')['questions']
        context = render.prepare_animation(questions)
        ask, reveal = context['boards'][0]
        plain = render._question_static(dict(questions[0], country_code='zz'), 0, 3, context['background'], True, hook=context['hook'])
        self.assertNotEqual(reveal.tobytes(), plain.tobytes())  # an unknown country draws no fact line
        self.assertEqual(render._facts(dict(questions[0], country_code='zz')), None)

    def test_descriptions_credit_the_data(self):
        for theme in ('Classic', 'Find', 'Zoom', 'Lookalike'):
            _, description, _, _ = textvariants.short_texts('sig', 3, 'Mixed', theme)
            self.assertIn('World Bank', description, theme)
        for theme in ('Capital',):
            _, description, _, _ = textvariants.short_texts('sig', 3, 'Mixed', theme)
            self.assertNotIn('World Bank', description)


if __name__ == '__main__':
    unittest.main()
