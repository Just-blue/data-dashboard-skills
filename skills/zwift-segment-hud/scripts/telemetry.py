"""Strict segment-local 1 Hz data adapter for the approved HUD drawing modules."""
from pathlib import Path
import csv
import json
import math
import os
import numpy as np
from drawing import Canvas, font

CONFIG_PATH = Path(os.environ['HUD_CONFIG']).resolve()
CONFIG = json.loads(CONFIG_PATH.read_text())
source = CONFIG.get('provenance', {})
if not source.get('sports_source') or source.get('boundary_status') != 'verified':
    raise ValueError('Declare the telemetry source and verify segment boundaries in provenance')
for key in ['rider_name', 'route_display_name']:
    if not str(CONFIG.get(key, '')).strip():
        raise ValueError(f'Missing {key}')
for key in ['rider_weight_kg', 'ftp_w']:
    if not math.isfinite(float(CONFIG.get(key, 0))) or float(CONFIG[key]) <= 0:
        raise ValueError(f'{key} must be a verified positive value')
path = Path(CONFIG['telemetry_path'])
if not path.is_absolute():
    path = CONFIG_PATH.parent / path
with path.open() as f:
    records = list(csv.DictReader(f))

def arr(key):
    try:
        a = np.array([float(r[key]) for r in records])
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f'Missing/invalid telemetry column {key}; do not replace missing sensors with zeros') from exc
    if not np.all(np.isfinite(a)):
        raise ValueError(f'Non-finite telemetry: {key}')
    return a

t = arr('time_s')
distance = arr('distance_m')
alt = arr('altitude_m')
power = arr('power_w')
hr = arr('heart_rate_bpm')
cad = arr('cadence_rpm')
speed = arr('speed_m_s')
lat = arr('lat')
lon = arr('lon')
if len(t) < 3 or t[0] != 0 or not np.allclose(np.diff(t), 1, rtol=0, atol=1e-7):
    raise ValueError('Telemetry must cover the segment on a complete 1 Hz elapsed-time axis starting at 0; preserve pauses')
if abs(distance[0]) > 1e-6 or distance[-1] <= 0 or np.any(np.diff(distance) < 0):
    raise ValueError('Distance must start at 0 and be nondecreasing; resolve resets before rendering')
if np.any(np.abs(lat) > 90) or np.any(np.abs(lon) > 180):
    raise ValueError('GPS coordinates outside degree ranges')
if any(np.any(a < 0) for a in [power, hr, cad, speed]):
    raise ValueError('Negative sensor values')
START, END = 0., float(t[-1])
ds, de = float(distance[0]), float(distance[-1])
tt, dd, aa, pp = t, distance, alt, power
C = {'ftp_account_w': float(CONFIG['ftp_w'])}
x = (lon-lon[0])*math.cos(math.radians(np.mean(lat)))*111320
y = (lat-lat[0])*111320
heading = np.unwrap(np.arctan2(np.gradient(x), np.gradient(y)))
heading = np.convolve(np.pad(heading, (3, 3), mode='edge'), np.ones(7)/7, mode='valid')
grid = np.arange(ds, de+10, 10)
zs = np.convolve(np.pad(np.interp(grid, dd, aa), (5, 5), mode='edge'), np.ones(11)/11, mode='valid')
if 'ascent_m' in records[0]:
    ascent = arr('ascent_m')
    if np.any(np.diff(ascent) < -1e-6):
        raise ValueError('Cumulative ascent must not decrease')
    ASCENT_SOURCE = 'recorded cumulative ascent'
else:
    ascent = np.r_[0, np.cumsum(np.maximum(0, np.diff(alt)))]
    ASCENT_SOURCE = 'estimated sum of positive altitude changes; not recorded device ascent'

def val(a, ts):
    return float(np.interp(ts, t, a))

def stats(ts):
    ts = float(np.clip(ts, START, END))
    i = int(np.searchsorted(t, ts, side='right')-1)
    w = power[(t >= max(START, t[i]-2)) & (t <= t[i])]
    used = (t > START) & (t <= t[i])
    d = val(distance, ts)
    return {
        'power_3s_w': round(float(np.mean(w))),
        'split_avg_power_w': round(float(np.mean(power[used]))) if np.any(used) else '—',
        'heart_rate_bpm': round(float(hr[i])), 'cadence_rpm': round(float(cad[i])),
        'speed_kmh': float(speed[i])*3.6, 'segment_distance_m': d-ds,
        'segment_ascent_m': round(val(ascent, ts)-ascent[0]),
        'segment_work_kj': round(float(np.sum(power[used]))/1000),
        'grade_estimated_percent': float(np.interp(min(de, d+50), grid, zs)-np.interp(max(ds, d-50), grid, zs))/max(1, min(de, d+50)-max(ds, d-50))*100,
    }

def slope_color(g):
    return '#49b5d3' if g < 3 else '#71bd64' if g < 5 else '#f1d249' if g < 8 else '#f09b3e' if g < 10 else '#eb6f47' if g < 13 else '#db4c53'

def crossing(m):
    i = int(np.searchsorted(distance, m, side='left'))
    if i == 0:
        return 0.
    return float(t[i-1]+(m-distance[i-1])/(distance[i]-distance[i-1])*(t[i]-t[i-1]))

def mean_between(values, start, end):
    weights = np.maximum(0, np.minimum(end, t[1:])-np.maximum(start, t[:-1]))
    return float(np.sum(values[1:]*weights)/(end-start))

ends = CONFIG.get('sector_end_distances_m')
if ends is None:
    # Keep a short tail in the last kilometre, and fit long courses within the panel.
    step = max(1000., math.ceil(de/12000)*1000.)
    ends = [k*step for k in range(1, max(1, int(de//step)))] + [de]
ends = np.asarray(ends, dtype=float)
if len(ends) == 0 or len(ends) > 12 or not np.all(np.isfinite(ends)) or ends[0] <= 0 or np.any(np.diff(ends) <= 0) or abs(ends[-1]-de) > .01:
    raise ValueError('Use 1–12 increasing sector end distances; final end must equal segment distance')
ends[-1] = de
sectors = []
start_m, start_s = 0., 0.
for i, end_m in enumerate(ends):
    end_s = END if i == len(ends)-1 else crossing(end_m)
    sectors.append({'sector': i+1, 'start_m': start_m, 'end_m': float(end_m),
                    'start_s': start_s, 'end_s': end_s, 'duration_s': end_s-start_s,
                    'avg_power_w': mean_between(power, start_s, end_s),
                    'avg_hr_bpm': mean_between(hr, start_s, end_s)})
    start_m, start_s = float(end_m), end_s
STUDY = {'duration_s': END, 'distance_m': de, 'sectors': sectors,
         'avg_power_w': mean_between(power, 0, END),
         'avg_hr_bpm': mean_between(hr, 0, END), 'ascent_source': ASCENT_SOURCE,
         'custom_sectors': True, 'ascent_m': float(ascent[-1]-ascent[0])}
