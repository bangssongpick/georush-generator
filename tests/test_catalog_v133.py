"""v1.3.3: 190 UN member flags; the v1.3 60 keep their names, groups and exact PNG/SVG bytes."""
from collections import Counter
import json
from pathlib import Path
import unittest

from PIL import Image, ImageDraw

from georush import render
from georush.catalog import Catalog, EXCLUDED_FROM_QUIZ
from georush.longform import render as longform_render
from georush.names import display_name
from georush.longform.quiz import EXPERT, HARD, build as build_longform, tier_for, validate
from georush.quiz import build_quiz, composition_signature, validate_quiz

UN_MEMBERS = set('''af al dz ad ao ag ar am au at az bs bh bd bb by be bz bj bt bo ba bw br bn bg bf bi cv kh cm
ca cf td cl cn co km cg cd cr ci hr cu cy cz dk dj dm do ec eg sv gq er ee sz et fj fi fr ga gm ge de gh gr gd gt
gn gw gy ht hn hu is in id ir iq ie il it jm jp jo kz ke ki kp kr kw kg la lv lb ls lr ly li lt lu mg mw my mv ml
mt mh mr mu mx fm md mc mn me ma mz mm na nr np nl nz ni ne ng mk no om pk pw pa pg py pe ph pl pt qa ro ru rw kn
lc vc ws sm st sa sn rs sc sl sg sk si sb so za ss es lk sd sr se ch sy tj tz th tl tg to tt tn tr tm tv ug ua ae
gb us uy uz vu ve vn ye zm zw'''.split())
OMITTED = {'td', 'mc', 'lu'}  # near-identical to Romania, Indonesia, Netherlands as 4:3 icons
V13 = json.loads((Path(__file__).parent / 'v13_catalog_60.json').read_text(encoding='utf-8'))


class Catalog190Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()
        cls.valid, cls.errors = cls.catalog.valid_countries()

    def test_un_members_minus_near_identical_flags(self):
        self.assertEqual(len(UN_MEMBERS), 193)
        self.assertEqual(self.errors, [])
        # v1.3.4: the data keeps all 190; the quiz pool leaves out the two contested flags (Afghanistan, Syria).
        self.assertEqual({row['code'] for row in self.catalog.countries}, UN_MEMBERS - OMITTED)
        self.assertEqual(len({row['sha256'] for row in self.catalog.countries}), 190)
        self.assertEqual(set(EXCLUDED_FROM_QUIZ), {'af', 'sy'})
        self.assertEqual({row['code'] for row in self.valid}, UN_MEMBERS - OMITTED - set(EXCLUDED_FROM_QUIZ))

    def test_v13_countries_unchanged(self):
        rows = {row['code']: row for row in self.catalog.countries}
        for code, old in V13.items():
            with self.subTest(code=code):
                self.assertEqual({key: rows[code][key] for key in old}, old)

    def test_groups_and_longform_split(self):
        self.assertEqual(Counter(row['difficulty'] for row in self.catalog.countries), {'Easy': 40, 'Normal': 60, 'Hard': 90})
        hard = {row['code'] for row in self.catalog.countries if row['difficulty'] == 'Hard'}
        self.assertFalse(HARD & EXPERT)
        self.assertEqual(HARD | EXPERT, hard)
        self.assertEqual(Counter(tier_for(row) for row in self.catalog.countries)['Expert'], 45)
        # Quiz pool without Afghanistan (Normal) and Syria (Longform Hard).
        self.assertEqual(Counter(row['difficulty'] for row in self.valid), {'Easy': 40, 'Normal': 59, 'Hard': 89})
        self.assertEqual(Counter(tier_for(row) for row in self.valid), {'Easy': 40, 'Normal': 59, 'Hard': 44, 'Expert': 45})

    def test_every_name_fits_shorts_and_longform_layouts(self):
        short = ImageDraw.Draw(Image.new('RGB', (1080, 1920)))
        wide = Image.new('RGB', (1920, 1080))
        for row in self.catalog.countries:
            shown = display_name(row['name'])
            with self.subTest(country=shown):
                render._option(short, 3, shown, True)  # raises when it cannot fit
                reveal = f"D · {shown}"
                size = render._center(short, reveal, 1105, 48, max_width=900)
                self.assertLessEqual(short.textbbox((0, 0), reveal, font=render._font(size))[2], 900)
                longform_render.option(wide, 3, shown, True, 1.025)
                longform_render.text(ImageDraw.Draw(wide), f"D: {shown}", (1455, 478, 405, 160), 35)

    def test_every_country_links_flag_name_and_revealed_answer(self):
        # Each country as the answer: catalog checks pass and the green card lands on its option.
        import numpy
        background = render._background()
        for index, row in enumerate(self.valid):
            with self.subTest(country=row['code']):
                peers = [r for r in self.valid if r['difficulty'] == row['difficulty'] and r['code'] != row['code']]
                correct = index % 4
                options = [r['name'] for r in peers[index % len(peers):][:3] + peers[:3]][:3]
                options.insert(correct, row['name'])
                question = {'country_code': row['code'], 'country_name': row['name'], 'flag_path': row['flag_path'],
                            'flag': row['flag'], 'flag_sha256': row['sha256'], 'options': options,
                            'correct_index': correct, 'difficulty': row['difficulty']}
                validate_quiz({'questions': [question], 'signature': composition_signature([question])}, self.catalog)
                pixels = numpy.asarray(render._question_static(question, 0, 3, background, reveal=True)).astype(int)
                green = []
                for option in range(4):
                    x, y = 76 + (option % 2) * 480, 1255 + (option // 2) * 178
                    box = pixels[y:y + 146, x:x + 448]
                    green.append(int(((box[:, :, 1] > box[:, :, 0] + 60) & (box[:, :, 1] > box[:, :, 2] + 25)
                                      & (box[:, :, 1] > 140)).sum()))
                self.assertEqual(green.index(max(green)), correct)

    def test_no_flag_has_a_large_transparent_area(self):
        # Longform draws flags as RGB, so a mostly transparent area shows black (unflattened Nepal: 64%).
        # Anti-aliased stripe edges keep their colour and stay well under 1%.
        import numpy
        for row in self.valid:
            with Image.open(row['flag_path']) as image:
                alpha = numpy.asarray(image.convert('RGBA'))[:, :, 3]
            self.assertLess((alpha < 128).mean(), 0.01, row['code'])

    def test_flag_images_are_900x675(self):
        for row in self.valid:
            with Image.open(row['flag_path']) as image:
                self.assertEqual(image.size, (900, 675), row['code'])

    def test_mixed_shorts_keep_one_third_per_group(self):
        counts = Counter()
        for seed in range(600):
            quiz = build_quiz(self.catalog, seed=seed)
            validate_quiz(quiz, self.catalog)
            counts.update(question['difficulty'] for question in quiz['questions'])
        total = sum(counts.values())
        for group in ('Easy', 'Normal', 'Hard'):
            self.assertAlmostEqual(counts[group] / total, 1 / 3, delta=0.04, msg=dict(counts))

    def test_single_group_and_longform_still_build(self):
        for group in ('Easy', 'Normal', 'Hard'):
            quiz = build_quiz(self.catalog, difficulty=group, seed=7)
            self.assertEqual({q['difficulty'] for q in quiz['questions']}, {group})
        for count in (20, 40):
            self.assertTrue(validate(build_longform(self.catalog, count=count, seed=count), self.catalog))


if __name__ == '__main__':
    unittest.main()
