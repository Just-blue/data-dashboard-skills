from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_skill', ROOT/'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_standalone_install_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = installer.install('zwift-segment-hud', Path(directory)/'skills')
            self.assertTrue((target/'SKILL.md').is_file())
            self.assertTrue((target/'LICENSE').is_file())
            self.assertFalse((target/'outputs').exists())
            self.assertFalse((target/'examples/demo').exists())
            sentinel = target/'custom.txt'; sentinel.write_text('keep me')
            with self.assertRaises(FileExistsError):
                installer.install('zwift-segment-hud', target.parent)
            self.assertEqual(sentinel.read_text(), 'keep me')
            data = Path(directory)/'data'; out = Path(directory)/'preview'
            subprocess.run([sys.executable, str(target/'scripts/make_demo.py'),
                            '--output-dir', str(data)], check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(target/'scripts/hud.py'),
                                     '--config', str(data/'config.json'), '--output-dir', str(out),
                                     '--at', '55', '--width', '1920'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out/'preview-alpha.png').is_file())

    def test_rejects_path_outside_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                installer.install('../other', directory)


if __name__ == '__main__':
    unittest.main()
