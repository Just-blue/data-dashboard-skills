# Data Dashboard Skills

A collection of reusable data dashboards and agent skills. Each dashboard ships in its own folder with its renderer, visual assets, data contract, examples and tests. Install the dashboard you need, or run its scripts directly.

[中文说明](README.zh-CN.md) · [Add a dashboard](CONTRIBUTING.md)

## Dashboard catalog

| Dashboard | Use case | Output | Documentation |
| --- | --- | --- | --- |
| **Zwift-inspired Segment HUD** | Cycling power/HR, custom sector timing, moving GPS map and elevation | Transparent4K60 MOV; PNG previews | [Guide](skills/zwift-segment-hud/README.md) · [Skill](skills/zwift-segment-hud/SKILL.md) |

The collection currently contains one dashboard. Additional dashboards belong alongside it in `skills/`; this catalog lists available implementations only.

![Cycling HUD with synthetic data](skills/zwift-segment-hud/docs/demo-preview.jpg)

*Preview of the cycling dashboard. All example telemetry and coordinates are synthetic; gray is a preview background.*

## Repository structure

```text
skills/
  zwift-segment-hud/
    SKILL.md
    scripts/
    assets/
    references/
    tests/
    requirements.txt
scripts/install_skill.py
tests/
```

Each skill owns its dependencies and licenses. The repository root is a catalog and installer, not itself a skill. There is no shared rendering framework to couple unrelated dashboards.

## Install one skill

```sh
git clone https://github.com/Just-blue/data-dashboard-skills.git
cd data-dashboard-skills
python3 scripts/install_skill.py --list
python3 scripts/install_skill.py zwift-segment-hud
```

By default, the installer copies the selected folder to `${CODEX_HOME:-$HOME/.codex}/skills/<name>`. It excludes generated outputs and refuses to overwrite existing installations. It does not install dependencies or change authentication. Use `--destination /path/to/skills` for another skills directory.

For the cycling HUD, install Python3.10+, FFmpeg/ffprobe and the skill's Python requirements:

```sh
python3 -m pip install -r skills/zwift-segment-hud/requirements.txt
```

Use a virtual environment if required by your Python installation. On macOS: `brew install ffmpeg`; on Debian/Ubuntu: `sudo apt-get install ffmpeg`. In a new Codex conversation:

> Use $zwift-segment-hud to create a transparent4K60 HUD for this activity segment: <effort link>.

See the skill guide for data preparation and authentication limits. A Strava URL is not direct renderer input.

## Run without an agent

```sh
cd skills/zwift-segment-hud
python3 scripts/make_demo.py
python3 scripts/hud.py --config examples/demo/config.json \
  --output-dir outputs/preview --at 55 --width 1920
```

See each dashboard's README for video rendering, input schema and limitations. The cycling HUD draws at1080p and upscales to4K while generating animation at60fps.

## Updating from the original single-skill repository

The cycling renderer and its dependencies now live under `skills/zwift-segment-hud/`. Run its previous commands from that directory; root-level `scripts/hud.py` and `requirements.txt` have moved. Existing independent skill installations continue working. To update one, review and back up local customizations, then replace only that skill folder. Do not clone the entire collection as a single installed skill.

## Development

```sh
python3 -m unittest discover -s tests -v
(cd skills/zwift-segment-hud && python3 -m unittest discover -s tests -v)
```

CI checks the collection installer and each registered dashboard. See [CONTRIBUTING.md](CONTRIBUTING.md) when adding one. Use synthetic examples; keep credentials, personal telemetry and large exports out of Git.

## License

Code and documentation: [MIT](LICENSE). Each dashboard includes its applicable third-party notices. [Collection notices](THIRD_PARTY_NOTICES.md) link to bundled asset licenses. This independent collection is not affiliated with Zwift or Strava.
