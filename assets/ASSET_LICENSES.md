# GeoRush bundled assets

## Flag graphics and country-code/name data

- Source: [lipis/flag-icons](https://github.com/lipis/flag-icons).
- Pinned source commit: `ac7e0eb3259eb62aa6100c435607e2fe03896a97`.
- License: **MIT**, Copyright (c) 2013 Panayiotis Lipiridis. Full required notice: `licenses/flag-icons-MIT.txt`.
- Commercial use, modification and redistribution are permitted under that notice.
- `country_source_upstream.json` is the unchanged upstream country data. Only 60 ISO-coded countries are enabled in `countries.json`; the full upstream data file is provenance, not the active quiz pool.
- `source_svg/` retains the exact 60 upstream SVGs; `flags/` contains local 900×675 PNG conversions. Each mapping uses the same lower-case ISO alpha-2 code as the upstream filename and data record. Source SVG and output PNG SHA-256 hashes are in `countries.json`.
- These are the upstream project's **standardized 4:3 icon variants**. They preserve recognizable national flag designs but do not reproduce every country's official flag aspect ratio. The program should describe them as flag icons, not official manufacturing specifications.
- No flags are fetched while creating videos. A missing, corrupt or mismatched asset must be excluded by runtime validation.
- Ambiguous near-identical pairs such as Chad/Romania and Monaco/Indonesia are omitted from this initial pool.
- Difficulty groups (20 Easy / 20 Normal / 20 Hard) are editorial familiarity groups, not an objective ranking of countries.
- An asset's copyright license does not waive applicable local laws on national symbols. This project uses the assets only for a geography identification game.

## Font

- `fonts/DejaVuSans-Bold.ttf` from the DejaVu Fonts distribution, https://dejavu-fonts.github.io/.
- License: Bitstream Vera font license; DejaVu modifications are public domain. Exact notices: `licenses/DejaVu-font-license.txt`.
- The unmodified font may be bundled with this application, and rendered text may be used commercially. The font is not sold by itself.
- The checksum is in `fonts/font_manifest.json`.

## Audio

The runtime generates original BGM and effects mathematically. No third-party music recording, YouTube audio, or commercial sound pack is included by the asset builder. See the audio engine and project documentation for the actual synthesis and mixing settings.

## Rebuild

Rebuilding is a developer action requiring a pinned local `flag-icons` checkout and `CairoSVG==2.8.2`. Run `tools/build_assets.py --upstream <checkout>`. Normal offline video creation does not require CairoSVG, SVG rendering, Git or internet access.
