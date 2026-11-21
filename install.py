#!/usr/bin/env python3
"""Install a user-local command pointing to this checkout."""
from pathlib import Path


def main():
    source = Path(__file__).resolve().with_name('gitapps.py')
    target = Path.home() / '.local' / 'bin' / 'gitapps'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if target.is_symlink() and target.resolve() == source:
            print(f'Already installed: {target}')
            return 0
        print(f'Refusing to overwrite existing command: {target}')
        return 1
    source.chmod(source.stat().st_mode | 0o111)
    target.symlink_to(source)
    print(f'Installed: {target}')
    print('Keep this checkout in place. Ensure ~/.local/bin is in PATH.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
