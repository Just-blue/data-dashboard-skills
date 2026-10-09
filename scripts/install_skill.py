"""Install one dashboard skill without overwriting local customizations."""
import argparse
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def available_skills():
    return sorted(p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md'))


def install(name, destination):
    if name not in available_skills():
        raise ValueError(f'Unknown skill: {name}')
    source = ROOT / 'skills' / name
    target = Path(destination).expanduser() / name
    if target.exists() or target.is_symlink():
        raise FileExistsError(f'{target} already exists; review local changes before updating')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '.venv', 'outputs', 'private', '.DS_Store',
        '.env', '.env.*', '*.fit', '*.gpx', '*.mov', '*.mp4', 'demo'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', nargs='?', choices=available_skills())
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--destination', type=Path,
                        default=Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'skills')
    args = parser.parse_args()
    if args.list:
        print('\n'.join(available_skills()))
        return
    if args.name is None:
        parser.error('choose a skill name, or use --list')
    try:
        print(install(args.name, args.destination))
    except (ValueError, FileExistsError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
