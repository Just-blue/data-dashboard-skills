"""Render the approved transparent HUD from a job-local config and telemetry CSV."""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))

def check(path, width, height, frames):
    p = probe(path)
    s = p['streams'][0]
    if len(p['streams']) != 1 or (s['width'], s['height'], s['codec_name'], s['pix_fmt'], s['r_frame_rate'], int(s['nb_frames'])) != (width, height, 'qtrle', 'argb', '60/1', frames):
        raise ValueError(f'Unexpected export format: {path}')
    if abs(float(p['format']['duration'])-frames/60) > 1e-5:
        raise ValueError(f'Unexpected duration: {path}')
    return p

def frame_rgba(path, frame):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', f'{frame/60:.9f}', '-i', str(path), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'])

def encode_chunk(job):
    import render
    index, start, stop, args, fingerprint = job
    out = Path(args.output_dir)/'chunks'/f'{index:04d}.mov'
    marker = out.with_suffix('.json')
    if out.exists() and marker.exists():
        saved = json.loads(marker.read_text())
        if saved['fingerprint'] != fingerprint:
            raise ValueError('Existing chunks use different inputs; choose a new output directory')
        check(out, args.width, args.height, stop-start)
        return saved
    temporary = out.with_suffix('.partial.mov')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1920x1080', '-r', '60', '-i', '-', '-an', '-vf', f'scale={args.width}:{args.height}:flags=lanczos', '-filter_threads', '1', '-c:v', 'qtrle', '-threads', '1', '-pix_fmt', 'argb', '-video_track_timescale', '60000', str(temporary)]
    with out.with_suffix('.log').open('w') as log:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)
        try:
            for f in range(start, stop):
                elapsed = args.begin+f/60
                if f == args.frames-1 and abs(args.begin+args.duration-render.hud.END) < 1e-7:
                    elapsed = render.hud.END
                proc.stdin.write(render.render(elapsed).tobytes())
                if (f-start) % 120 == 0:
                    print(f'chunk {index+1}: {f-start+1}/{stop-start}', flush=True)
            proc.stdin.close()
            if proc.wait() != 0:
                raise RuntimeError(f'ffmpeg failed; inspect {out.with_suffix(".log")}')
        except BaseException:
            proc.kill()
            proc.wait()
            raise
    check(temporary, args.width, args.height, stop-start)
    temporary.replace(out)
    result = {'index': index, 'start': start, 'stop': stop, 'file': str(out), 'fingerprint': fingerprint}
    marker.write_text(json.dumps(result, indent=2))
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--mode', choices=['inspect', 'preview', 'video'], default='preview')
    ap.add_argument('--at', type=float, default=0)
    ap.add_argument('--begin', type=float, default=0)
    ap.add_argument('--duration', type=float)
    ap.add_argument('--width', type=int, choices=[1920, 3840], default=3840)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--chunk-seconds', type=int, default=120)
    args = ap.parse_args()
    args.config = args.config.resolve()
    args.output_dir = args.output_dir.resolve()
    os.environ['HUD_CONFIG'] = str(args.config)
    cfg = json.loads(args.config.read_text())
    font = cfg.get('font_path')
    if font:
        os.environ['HUD_FONT'] = str((args.config.parent/Path(font)).resolve())
    import telemetry as data
    import render
    args.height = args.width*9//16
    if args.workers < 1 or args.chunk_seconds < 1:
        ap.error('workers and chunk-seconds must be positive')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'sector-summary.json').write_text(json.dumps(data.STUDY, ensure_ascii=False, indent=2))
    if args.mode == 'inspect':
        print(json.dumps(data.STUDY, ensure_ascii=False, indent=2))
        return
    if args.mode == 'preview':
        from PIL import Image
        if not 0 <= args.at <= data.END:
            ap.error('preview time outside segment')
        layer = render.render(args.at).resize((args.width, args.height), Image.Resampling.LANCZOS)
        layer.save(args.output_dir/'preview-alpha.png')
        bg = Image.new('RGBA', layer.size, (90, 94, 99, 255))
        bg.alpha_composite(layer)
        bg.convert('RGB').save(args.output_dir/'preview-gray.jpg', quality=94)
        print(args.output_dir/'preview-alpha.png')
        return
    args.duration = data.END-args.begin if args.duration is None else args.duration
    if args.begin < 0 or args.duration <= 0 or args.begin+args.duration > data.END+1e-7:
        ap.error('video time range outside segment')
    args.frames = round(args.duration*60)
    if abs(args.frames/60-args.duration) > 1e-7:
        ap.error('duration must be representable at 60 fps')
    final = args.output_dir/'hud-alpha.mov'
    if final.exists():
        ap.error('hud-alpha.mov already exists; choose a new output directory')
    digest = hashlib.sha256()
    from drawing import FONT
    for file in [args.config, data.path, FONT, *sorted(HERE.glob('*.py'))]:
        digest.update(file.read_bytes())
    digest.update(json.dumps([args.width, args.begin, args.duration, args.chunk_seconds]).encode())
    fingerprint = digest.hexdigest()
    (args.output_dir/'chunks').mkdir(exist_ok=True)
    jobs = [(i, f, min(args.frames, f+args.chunk_seconds*60), args, fingerprint)
            for i, f in enumerate(range(0, args.frames, args.chunk_seconds*60))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        chunks = sorted(pool.map(encode_chunk, jobs), key=lambda c: c['index'])
    listing = args.output_dir/'chunks.ffconcat'
    listing.write_text('ffconcat version 1.0\n'+''.join(f"file 'chunks/{c['index']:04d}.mov'\n" for c in chunks))
    partial = final.with_suffix('.partial.mov')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing), '-map', '0:v:0', '-c', 'copy', '-video_track_timescale', '60000', str(partial)], check=True)
    p = check(partial, args.width, args.height, args.frames)
    import numpy as np
    samples = sorted(set([0, args.frames-1]+[f for c in chunks[1:] for f in [c['start']-1, c['start']]]))
    for f in samples:
        c = next(c for c in chunks if c['start'] <= f < c['stop'])
        buf = frame_rgba(partial, f)
        if buf != frame_rgba(c['file'], f-c['start']):
            raise ValueError(f'Concat mismatch at frame {f}')
        alpha = np.frombuffer(buf, np.uint8).reshape((args.height, args.width, 4))[:, :, 3]
        if not (alpha.min() == 0 and alpha.max() == 255 and np.any((alpha > 0) & (alpha < 255))):
            raise ValueError(f'Alpha check failed at frame {f}')
    partial.replace(final)
    report = {'status': 'passed', 'output': str(final), 'bytes': final.stat().st_size,
              'probe': p, 'boundary_frames_checked': samples, 'fingerprint': fingerprint,
              'source_config': str(args.config), 'provenance': data.CONFIG['provenance'],
              'spatial_render': 'approved 1080p layout, Lanczos upscale', 'animation_fps': 60}
    (args.output_dir/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(final, flush=True)

if __name__ == '__main__':
    main()
