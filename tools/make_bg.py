"""v1.6.5: build assets/bg_v165.jpg, the GeoRush background plate, from the approved design mock.

The mock (assets/design/find_mock_v165.webp) is the user's design: globe logo, world maps and plane on top, glowing
banner and card in the middle, grid floor at the bottom. Only the top and bottom decoration is kept; the middle is a plain
navy gradient taken from the mock's own left edge, so the banner, badge and card can be drawn fresh with any text.

    python tools/make_bg.py
"""
import numpy as np
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'assets'/'design'/'find_mock_v165.webp'
TARGET = ROOT/'assets'/'bg_v165.jpg'
CENTER_KEEP, SIDE_KEEP, TOP_FADE = 306, 288, 12  # rows of the mock kept at the top (logo / maps and plane), then a short fade
BOTTOM_START, BOTTOM_FADE = 1580, 60  # the grid floor starts here (the Shorts caption covers it on a phone anyway)


def main():
    mock = np.asarray(Image.open(SOURCE).convert('RGB').resize((1080, 1920), Image.Resampling.LANCZOS)).astype(float)
    # one colour per row: the median of the mock's left edge, where no banner, card or glow reaches
    rows = np.median(mock[:, :20, :], axis=1)
    kernel = np.ones(41)/41
    rows = np.stack([np.convolve(np.pad(rows[:, c], 20, mode='edge'), kernel, mode='valid') for c in range(3)], axis=1)
    plate = np.repeat(rows[:, None, :], 1080, axis=1)
    y = np.arange(1920)[:, None]
    x = np.arange(1080)[None, :]
    # the logo medallion reaches lower (row 322) than the maps and the plane (row 290): the mock's own banner starts right under it
    middle = np.clip((np.minimum(x, 1079-x)-330)/40, 0, 1)  # 1 over the medallion, 0 at the sides
    keep = SIDE_KEEP+(CENTER_KEEP-SIDE_KEEP)*middle
    top = np.clip((keep+TOP_FADE-y)/TOP_FADE, 0, 1)
    bottom = np.clip((y-BOTTOM_START)/BOTTOM_FADE, 0, 1)*np.ones((1, 1080))
    alpha = np.maximum(top, bottom)[:, :, None]
    plate = plate*(1-alpha)+mock*alpha
    Image.fromarray(plate.astype('uint8'), 'RGB').save(TARGET, quality=95, subsampling=0)
    print('wrote', TARGET, TARGET.stat().st_size//1024, 'KB')


if __name__ == '__main__':
    main()
