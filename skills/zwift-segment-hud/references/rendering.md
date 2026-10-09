# Rendering

Python3.10+, NumPy, Pillow and ffmpeg/ffprobe are required. Linux and macOS are suitable; verify your ffmpeg supports qtrle. Windows has not been tested.

Default:4K60 transparent MOV. Add --width1920 with a space (`--width 1920`) for1080p60. `--begin` and `--duration` choose a clip in seconds. Default2 workers and120-second chunks; `--workers` and `--chunk-seconds` tune resource usage. Durations must be representable at60fps.

Outputs include hud-alpha.mov, sector-summary.json, verification.json and chunks/. Restart the same command to reuse completed chunks; fingerprints cover data,config,font,scripts and export settings. Changed inputs need a new output directory. Existing finalMOV is not overwritten.

Each chunk is probed; concatenation uses stream copy. Verification checks final format/framecount/duration and compares decoded first/last and both sides of chunk boundaries byte-for-byte. Fully transparent, opaque and intermediate alpha pixels are checked. Also visually inspect start/middle/end and a transition; these checks are not a full perceptual review.

Lossless alpha files are large. Estimate disk use from a short sample and allow space for chunks plus final output. Avoid filling the system disk. Stop on encoder/storage errors and preserve completed chunks for retry.

Spatial layout is1080p upscaled with Lanczos; animation calculated60 times/second. A player may display alpha as black; composite normally over footage instead of chroma-keying. Match the overlay zero to the segment start in footage. If source is59.94fps, align by timestamps and preserve duration. No camera offset is assumed.
