#!/usr/bin/env python3
"""Build a standalone RPM on Fedora with Python, PyInstaller and rpm-build."""
import ast
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if not shutil.which('rpmbuild'):
        raise SystemExit('Missing rpmbuild. On Fedora: sudo dnf install rpm-build python3 python3-pip')
    tree = ast.parse((ROOT / 'gitapps.py').read_text())
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets))
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for name in ['BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS', 'BUILDROOT']:
            (root / name).mkdir()
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                        '--onedir', '--name', 'gitapps', '--distpath', str(root / 'frozen'),
                        '--workpath', str(root / 'work'), '--specpath', str(root / 'spec'),
                        '--add-data', str(ROOT / 'tracked_repositories.json') + ':.',
                        str(ROOT / 'gitapps.py')], check=True)
        spec = root / 'SPECS/gitapps.spec'
        spec.write_text(f'''Name: gitapps
Version: {version}
Release: 1
Summary: Check installed applications against GitHub Releases
License: MIT
URL: https://github.com/milad-mantashi/gitapps
# Bundles Python. Retain automatic native-library requirements for compatibility.
%global debug_package %{{nil}}
%global __brp_strip %{{nil}}
%global __brp_strip_comment_note %{{nil}}
%description
A terminal update checker with a bundled Python interpreter.
%install
mkdir -p %{{buildroot}}/usr/lib/gitapps %{{buildroot}}/usr/bin
cp -a {root}/frozen/gitapps/. %{{buildroot}}/usr/lib/gitapps/
ln -s ../lib/gitapps/gitapps %{{buildroot}}/usr/bin/gitapps
mkdir -p %{{buildroot}}/usr/share/doc/gitapps
cp {ROOT}/README.md {ROOT}/README.fa.md {ROOT}/CHANGELOG.md %{{buildroot}}/usr/share/doc/gitapps/
mkdir -p %{{buildroot}}/usr/share/licenses/gitapps
cp {ROOT}/LICENSE %{{buildroot}}/usr/share/licenses/gitapps/
%files
/usr/bin/gitapps
/usr/lib/gitapps
%doc /usr/share/doc/gitapps
%license /usr/share/licenses/gitapps
''')
        subprocess.run(['rpmbuild', '--define', f'_topdir {root}', '-bb', str(spec)], check=True)
        output = ROOT / 'dist'
        output.mkdir(exist_ok=True)
        for rpm in (root / 'RPMS').glob('**/*.rpm'):
            target = output / rpm.name
            shutil.copy2(rpm, target)
            print(target)


if __name__ == '__main__':
    main()
