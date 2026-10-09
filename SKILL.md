---
name: zwift-segment-hud
description: Render Zwift-inspired cycling segment HUDs with sector statistics, moving GPS maps, elevation and power charts as transparent 4K60 MOV overlays. Use when a user requests a cycling telemetry overlay or a Strava activity-segment visualization.
---

# Cycling segment HUD

Use the bundled Python renderer to keep this preset consistent. Follow the user's chosen data source and privacy requirements; do not assume access to Strava or an athlete account.

## Inputs

An activity-specific segment effort link identifies a particular attempt. A generic segment URL identifies only a route: resolve the activity and repetition from context, or ask if ambiguous. Obtain authorized telemetry, verify segment boundaries against elapsed time and GPS, then normalize a local CSV. Browser/API access and matching are agent work, not functionality implemented by the renderer.

Read [references/data.md](references/data.md) for CSV/config requirements. Never invent missing sensors, weight, FTP, benchmarks or camera offsets. Historical weight/FTP must match the ride date. Credentials stay outside the repository and output reports.

## Style and output

Use this preset when requested; do not require a fresh design discussion for every export. It includes sector averages and timing, an expanded real-route map, elevation/grade, rider W/kg and power history. Tektur is bundled under OFL; custom local fonts are optional. It is inspired by a cycling-game interface, not an official or pixel-identical Zwift product.

Default output is qtrle/ARGB transparent MOV, 3840×2160, 60fps, no audio. Layout is drawn at1080p and Lanczos-upscaled; animations are generated at60fps. Do not claim native4K typography. PR/KOM comparison is not implemented. Internal sectors are custom display intervals, not official Strava subsegments.

## Execution

Install dependencies from requirements.txt and make ffmpeg/ffprobe available. Resolve paths against this skill folder. First inspect inputs and a preview:

```sh
python scripts/hud.py --config <job>/config.json --output-dir <job>/inspect --mode inspect
python scripts/hud.py --config <job>/config.json --output-dir <job>/preview --at 0
python scripts/hud.py --config <job>/config.json --output-dir <job>/export --mode video
```

Read [references/rendering.md](references/rendering.md) for resumable export and verification. For a requested full export in this style, inspect representative frames and a sector transition then proceed. For preview-only requests, stop at the preview. Check disk space before lengthy exports.

Deliver the output with duration, resolution, alpha format, evidence of checks and any unresolved video sync limitations. A transparent overlay needs no footage; compositing requires a separately verified camera offset.
