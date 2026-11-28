# GeoRush third-party notices

Bundled country data, PNG conversions, source SVGs and required notices: [assets/ASSET_LICENSES.md](assets/ASSET_LICENSES.md).
Bundled font: unmodified DejaVu Sans Bold; Bitstream Vera/DejaVu notices are included in `assets/licenses/`.

Runtime dependencies installed into this project's virtual environment:

- Pillow 12.3.0 — HPND and component licenses, https://python-pillow.github.io/.
- NumPy 2.3.5 — BSD-3-Clause and bundled component notices, https://numpy.org/.
- imageio-ffmpeg 0.6.0 — BSD-2-Clause Python wrapper, https://github.com/imageio/imageio-ffmpeg.
- FFmpeg — free software; LGPL/GPL terms depend on the actual binary/build. `imageio-ffmpeg` provides a local binary. https://ffmpeg.org/legal.html.

This source ZIP does not contain Python, third-party wheels or FFmpeg executables.
The first free installation downloads dependencies; normal rendering uses only installed local files.
Their packages carry their notices. A separately redistributed EXE folder must retain applicable notices and fulfill the license of its bundled FFmpeg build.

BGM and effects are synthesized by `georush/audio.py` from mathematical oscillators and seeded noise. No third-party recording is included.

## Flag stories (v1.7.0)

assets/flag_stories.json: sentences written for GeoRush from the flag descriptions of factbook/factbook.json
(CIA World Factbook data, CC0-1.0) and checked against the second page listed per entry. The pages are references for
facts; their text is not included. Story voice clips (assets/voice/story_*.wav) are generated with Kokoro-82M (Apache-2.0).
