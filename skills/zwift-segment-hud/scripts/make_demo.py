"""Create an entirely synthetic climb; no real ride or location is used."""
from pathlib import Path
import csv
import json
import math


def create_demo(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    fields = ['time_s', 'distance_m', 'lat', 'lon', 'altitude_m', 'power_w',
              'heart_rate_bpm', 'cadence_rpm', 'speed_m_s', 'ascent_m']
    with (output / 'telemetry.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for t in range(121):
            writer.writerow(dict(zip(fields, [t, 6*t,
                .01 + t*.000045, .01 + .0005*math.sin(t/15),
                100+t*.36, round(260+35*math.sin(t/8)),
                round(145+t*.18), round(85+5*math.cos(t/9)), 6, t*.36])))
    config = {'telemetry_path': 'telemetry.csv', 'route_display_name': 'Demo Climb',
              'rider_name': 'DEMO', 'rider_weight_kg': 70, 'ftp_w': 260,
              'sector_end_distances_m': [240, 480, 720],
              'provenance': {'sports_source': 'synthetic', 'boundary_status': 'verified',
                 'boundary_evidence': 'Generated 0–120s interval; not a real activity',
                 'description': 'Entirely fictional telemetry and coordinates for demonstration'}}
    (output / 'config.json').write_text(json.dumps(config, indent=2)+'\n')
    return output / 'config.json'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('examples/demo'))
    print(create_demo(parser.parse_args().output_dir))
