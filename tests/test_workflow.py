"""Integration checks use generated telemetry only."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from make_demo import create_demo


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = create_demo(self.root / 'demo')

    def tearDown(self):
        self.temp.cleanup()

    def run_hud(self, *args):
        return subprocess.run([sys.executable, str(ROOT/'scripts/hud.py'), '--config',
                               str(self.config), *map(str, args)], capture_output=True, text=True)

    def test_sector_totals_and_alpha_preview(self):
        out = self.root/'preview'
        result = self.run_hud('--output-dir', out, '--mode', 'preview', '--at', 55, '--width', 1920)
        self.assertEqual(result.returncode, 0, result.stderr)
        stats = json.loads((out/'sector-summary.json').read_text())
        self.assertEqual(len(stats['sectors']), 3)
        self.assertEqual(sum(s['duration_s'] for s in stats['sectors']), 120)
        weighted = sum(s['avg_power_w']*s['duration_s'] for s in stats['sectors'])/120
        self.assertAlmostEqual(weighted, stats['avg_power_w'])
        from PIL import Image
        alpha = Image.open(out/'preview-alpha.png').getchannel('A')
        self.assertEqual(alpha.getextrema(), (0, 255))

    def test_missing_sensor_fails(self):
        path = self.config.parent/'telemetry.csv'
        import csv
        with path.open() as file:
            rows = list(csv.DictReader(file))
        rows[15]['power_w'] = ''
        with path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        result = self.run_hud('--output-dir', self.root/'bad', '--mode', 'inspect')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('power_w', result.stderr)

    def test_sector_state_has_no_future_average(self):
        env = dict(os.environ, HUD_CONFIG=str(self.config), PYTHONPATH=str(ROOT/'scripts'))
        result = subprocess.run([sys.executable, '-c',
            "import sector_panel as s; assert s.active_index(39.99)==0; "
            "assert s.active_index(40)==1; assert s.average(1,40,'power') is None; "
            "assert s.average(1,41,'power') is not None"], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_video_concat_and_resume(self):
        out = self.root/'video'
        args = ['--output-dir', out, '--mode', 'video', '--begin', 39, '--duration', 2,
                '--chunk-seconds', 1, '--width', 1920, '--workers', 1]
        result = self.run_hud(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((out/'verification.json').read_text())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['boundary_frames_checked'], [0,59,60,119])
        chunks = list((out/'chunks').glob('*.mov'))
        mtimes = [p.stat().st_mtime_ns for p in chunks]
        (out/'hud-alpha.mov').rename(self.root/'first.mov')
        result = self.run_hud(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mtimes, [p.stat().st_mtime_ns for p in chunks])
        (out/'hud-alpha.mov').rename(self.root/'second.mov')
        cfg = json.loads(self.config.read_text()); cfg['ftp_w'] = 275
        self.config.write_text(json.dumps(cfg))
        result = self.run_hud(*args)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('different inputs', result.stderr)


if __name__ == '__main__':
    unittest.main()
