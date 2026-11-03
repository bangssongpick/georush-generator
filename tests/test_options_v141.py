"""v1.4.1: larger answer choices that still fit their cards for every country and capital name."""
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from georush import render
from georush.catalog import Catalog
from georush.names import display_name
from georush.themes import capital_of


def drawn(name, index=3):
    seen = []
    original = ImageDraw.ImageDraw.text

    def measured(draw, xy, text, *args, **kwargs):
        seen.append((str(text), kwargs['font'].size, draw.textbbox(xy, text, font=kwargs['font'])))
        return original(draw, xy, text, *args, **kwargs)
    image = Image.new('RGB', (render.WIDTH, render.HEIGHT))
    with patch.object(ImageDraw.ImageDraw, 'text', measured):
        render._option(ImageDraw.Draw(image), index, name)
    return seen[1:]  # the first call is the A/B/C/D badge


class OptionSizeTests(unittest.TestCase):
    def test_short_names_use_the_larger_size(self):
        self.assertGreaterEqual(render.OPTION_SIZE, 42)
        for name in ('France', 'Japan', 'Brazil', 'Paris'):
            self.assertEqual({size for _, size, _ in drawn(name)}, {render.OPTION_SIZE}, name)

    def test_every_country_and_capital_fits_inside_its_card(self):
        catalog = Catalog()
        names = {display_name(row['name']) for row in catalog.countries}
        names |= {capital_of(row['code']) for row in catalog.countries} - {''}
        x, y = 76+480, 1255+178  # card D
        for name in sorted(names):
            for text, size, (x0, y0, x1, y1) in drawn(name):
                self.assertGreaterEqual(size, 23, name)
                self.assertGreaterEqual(x0, x+90, name)
                self.assertLessEqual(x1, x+440, name)
                self.assertGreaterEqual(y0, y+2, name)
                self.assertLessEqual(y1, y+144, name)


if __name__ == '__main__':
    unittest.main()
