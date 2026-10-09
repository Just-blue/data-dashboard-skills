# Cycling Segment HUD

Render a Zwift-inspired cycling dashboard as a **transparent 4K60 MOV** for your ride videos. Includes an optional Codex skill and a standalone Python renderer.

[中文说明](README.zh-CN.md) · [Data contract](references/data.md) · [Rendering details](references/rendering.md)

![Synthetic climb preview](docs/demo-preview.jpg)

*Entirely synthetic route and sensor data. Gray is a preview background; the exported MOV has alpha transparency.*

## What it does

- Current power, cadence, heart rate, speed, distance, ascent and elapsed time.
- Custom sector timing, average power/HR, progress and completion stars.
- A moving GPS route map, grade/elevation profile and power/HR history.
- Rider W/kg using the same unrounded trailing3s power shown by the power tile.
- Resumable chunk rendering, lossless concatenation and alpha/boundary verification.

Default export: **3840×2160,60fps,qtrle/ARGB,MOV,no audio**. The spatial layout is drawn at1920×1080 and upscaled with Lanczos; animation is generated at60fps. This is not native4K typography.

This is an independent project inspired by cycling-game interfaces, not affiliated with Zwift or Strava. The open-source edition uses the OFL-licensed Tektur font, not a proprietary game font.

## Quick start

Requires Python3.10+ and `ffmpeg`/`ffprobe` on PATH. On macOS, install FFmpeg with `brew install ffmpeg`; on Debian/Ubuntu, use `sudo apt-get install ffmpeg`.

```sh
git clone https://github.com/Just-blue/zwift-segment-hud.git
cd zwift-segment-hud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Generate a fictional two-minute climb; no accounts or credentials required.
python scripts/make_demo.py

# View a transparent PNG plus gray-background preview.
python scripts/hud.py --config examples/demo/config.json \
  --output-dir outputs/preview --at 55 --width 1920

# Render a short4K60 sample crossing a sector boundary.
python scripts/hud.py --config examples/demo/config.json \
  --output-dir outputs/sample --mode video --begin 39 --duration 3
```

Output: `outputs/sample/hud-alpha.mov`. Drop it on a track above your footage using normal alpha compositing. Do not chroma-key black. For the full demo, omit `--begin` and `--duration`, and choose a new output directory.

## Your own ride

Prepare a segment-local1Hz CSV and JSON config using the [data contract](references/data.md). Cut the exact attempt, preserve pauses, and verify boundaries. Set the rider name, activity-date weight/FTP and your data source. Run `--mode inspect` before rendering.

**A Strava link is not direct CLI input.** Fetching data, authentication, FIT conversion and matching a Strava attempt to another platform are not implemented here. An agent using the skill can orchestrate those steps with available authorized tools. A specific activity-segment effort link is more useful than a generic segment URL. Respect the athlete's source and privacy preferences.

The renderer requires complete finite sensor fields and whole-second1Hz telemetry. It rejects missing readings rather than treating them as zero. Fractional-duration efforts and partial-sensor layouts need preprocessing or an extension. PR/KOM comparison is not included. Custom sectors are presentation intervals, not official Strava subsectors.

## Install as a Codex skill

For a **new installation**, clone into your user-level skill directory:

```sh
git clone https://github.com/Just-blue/zwift-segment-hud.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/zwift-segment-hud"
```

Install Python requirements and FFmpeg as above. If that directory already exists, review/update the existing installation; do not overwrite private customizations. In a new Codex conversation:

> Use $zwift-segment-hud to create a transparent4K60 cycling HUD for this activity segment: <effort link>.

The skill will need authorized telemetry access and verified boundaries. It does not include credentials or create authentication automatically. You can also run the scripts without Codex.

## Resume and validation

Rerun an interrupted command with the same config/output directory to reuse completed chunks. A fingerprint checks data,config,font,code and export settings. Existing final MOVs are not overwritten. Allow space for both chunks and final output; lossless4K alpha can be large.

Each export writes `verification.json`. Checks cover dimensions,frame rate,framecount,duration,alpha and decoded concat boundaries. Visually review representative frames as well. Camera synchronization is separate; the renderer assumes no video offset.

```sh
python -m unittest discover -s tests -v
```

The tests use generated telemetry only and exercise sector calculations, missing sensors, transparency, video concatenation, resume and changed-input rejection. macOS has been tested locally; Ubuntu is exercised by CI. Windows has not been tested.

## License

Code and documentation: [MIT](LICENSE). Bundled Tektur font: [SIL OFL1.1](assets/OFL.txt). See [third-party notices](THIRD_PARTY_NOTICES.md). Custom fonts are not committed and remain subject to their own licenses.
