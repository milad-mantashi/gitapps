#!/usr/bin/env python3
"""Build a Python-based or standalone DEB without root."""
import argparse
import sys
import ast
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standalone', action='store_true', help='Bundle Python using PyInstaller (build dependency only)')
    args = parser.parse_args()
    tree = ast.parse((ROOT / 'gitapps.py').read_text())
    version = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets))
    architecture = subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip() if args.standalone else 'all'
    output = ROOT / 'dist' / f'gitapps_{version}-1_{architecture}.deb'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        package = Path(folder)
        control = package / 'DEBIAN'
        app = package / 'usr/lib/gitapps'
        binary = package / 'usr/bin'
        docs = package / 'usr/share/doc/gitapps'
        for directory in [control, app, binary, docs]:
            directory.mkdir(parents=True)
        for name in ['gitapps.py', 'tracked_repositories.json']:
            shutil.copyfile(ROOT / name, app / name)
            (app / name).chmod(0o755 if name.endswith('.py') else 0o644)
        if args.standalone:
            subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                            '--clean', '--onedir', '--name', 'gitapps',
                            '--distpath', str(package / 'frozen'),
                            '--workpath', str(package / 'work'),
                            '--specpath', str(package / 'spec'),
                            '--add-data', str(ROOT / 'tracked_repositories.json') + ':.',
                            str(ROOT / 'gitapps.py')], check=True)
            shutil.rmtree(app)
            shutil.copytree(package / 'frozen/gitapps', app)
            for name in ['frozen', 'work', 'spec']:
                shutil.rmtree(package / name)
            (binary / 'gitapps').symlink_to('../lib/gitapps/gitapps')
        else:
            (binary / 'gitapps').symlink_to('../lib/gitapps/gitapps.py')
        for name in ['README.md', 'README.fa.md', 'CHANGELOG.md', 'LICENSE']:
            shutil.copyfile(ROOT / name, docs / name)
            (docs / name).chmod(0o644)
        (control / 'control').write_text(
            f'Package: gitapps\nVersion: {version}-1\nArchitecture: {architecture}\n'
            'Maintainer: Milad Mantashi <6298635+milad-mantashi@users.noreply.github.com>\n'
            'Section: utils\nPriority: optional\n'
            + ('' if args.standalone else 'Depends: python3 (>= 3.10)\n') +
            'Homepage: https://github.com/milad-mantashi/gitapps\n'
            'Description: Check installed apps against GitHub Releases\n'
            ' Detect local versions and show release links when updates are available.\n')
        (control / 'control').chmod(0o644)
        subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(package), str(output)], check=True)
    print(output)


if __name__ == '__main__':
    main()
