#!/usr/bin/env python3
"""Check stable GitHub releases from the terminal using Python's standard library."""
import argparse
import json
import re
import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def repository(value):
    if value.startswith('https://'):
        parsed = urlparse(value)
        if parsed.netloc != 'github.com' or parsed.query or parsed.fragment:
            raise argparse.ArgumentTypeError('Use a github.com repository URL.')
        value = parsed.path.strip('/')
    value = value.removesuffix('.git')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise argparse.ArgumentTypeError('Expected OWNER/REPO or https://github.com/OWNER/REPO')
    return value


def compare(current, latest):
    # Compare numeric stable versions only; do not guess arbitrary tag ordering.
    pattern = r'v?(\d+(?:\.\d+)*)(?:\+[0-9A-Za-z.-]+)?'
    a, b = re.fullmatch(pattern, current), re.fullmatch(pattern, latest)
    if not a or not b:
        return 'Cannot compare these version formats automatically'
    left = tuple(map(int, a[1].split('.')))
    right = tuple(map(int, b[1].split('.')))
    size = max(len(left), len(right))
    left += (0,) * (size - len(left))
    right += (0,) * (size - len(right))
    if left < right:
        return 'Update available'
    if left == right:
        return 'Up to date'
    return 'Installed version is newer than the latest stable release'


def run_local(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True,
                                timeout=5, errors='replace', stdin=subprocess.DEVNULL)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


PACKAGE_NAMES = {'happ-proxy/happ-desktop': 'happ'}


def detect_installed(repo):
    """Discover an executable matching the repository name; never run shell text."""
    name = PACKAGE_NAMES.get(repo.lower(), repo.split('/')[1])
    # Reject option-like names and path components before executing anything.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name):
        return None, 'Automatic detection unavailable for this repository name'
    executable = shutil.which(name)
    if executable and repo.lower() not in {'localsend/localsend', 'happ-proxy/happ-desktop'}:
        output = run_local([executable, '--version'])
        if output:
            match = re.search(
                r'^' + re.escape(name) + r'\s+(?:version\s+)?v?(\d+(?:\.\d+)+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)(?=\s|$)',
                output, re.IGNORECASE | re.MULTILINE,
            )
            if match:
                return match[1], f'{executable} --version'
    # Package metadata also covers DEBs whose executable has another name.
    dpkg = shutil.which('dpkg-query')
    if dpkg:
        output = run_local([dpkg, '-W', '-f=${Status}\t${Version}', name.lower()])
        if output and output.startswith('install ok installed\t'):
            version = output.split('\t', 1)[1].strip()
            upstream = version.split(':', 1)[-1].rsplit('-', 1)[0]
            if re.fullmatch(r'\d+(?:\.\d+)+(?:\+[0-9A-Za-z.-]+)?', upstream):
                return upstream, f'dpkg-query ({name}: {version})'
            return None, f'Installed package has unsupported version format: {version}'
    if executable:
        return None, f'Found {executable}, but could not determine its version'
    return None, 'No matching executable or installed DEB found; automatic detection may need an app-specific mapping'


def state_path():
    root = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return root / 'gitapps' / 'repositories.json'


def load_state():
    path = state_path()
    defaults = Path(__file__).resolve().with_name('tracked_repositories.json')
    data = json.loads(defaults.read_text()) if defaults.exists() else {}
    if path.exists():
        saved = json.loads(path.read_text())
        if not isinstance(saved, dict):
            raise ValueError('Invalid repository registry')
        data.update(saved)
    if not isinstance(data, dict):
        raise ValueError('Invalid repository registry')
    for name, entry in data.items():
        if repository(name) != name or not isinstance(entry, dict):
            raise ValueError('Invalid repository entry')
        current = entry.get('current')
        if current is not None and not isinstance(current, str):
            raise ValueError('Invalid installed version')
    return data


def save_state(data):
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def check_release(repo, current=None):
    detected, source = detect_installed(repo)
    current = detected or current
    request = Request(
        f'https://api.github.com/repos/{repo}/releases/latest',
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'gitapps-checker'},
    )
    try:
        with urlopen(request, timeout=20) as response:
            release = json.load(response)
        latest = release['tag_name']
        if not isinstance(latest, str) or not latest:
            raise ValueError('Invalid release tag')
    except HTTPError as error:
        messages = {
            404: 'Repository is unavailable or has no stable release.',
            403: 'GitHub denied access; its API rate limit may have been reached.',
            429: 'GitHub API rate limit reached; try again later.',
        }
        print('Error: ' + messages.get(error.code, f'GitHub returned HTTP {error.code}.'), file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError):
        print('Error: Cannot reach GitHub. Check your network and DNS, then retry.', file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError):
        print('Error: GitHub returned an invalid release response.', file=sys.stderr)
        return 1
    print(f'Repository: {repo}')
    print(f'Installed:  {current or "Unknown"}')
    print(f'Detection:  {source}')
    print(f'Latest:     {latest}')
    status = compare(current, latest) if current else 'Installed version could not be detected; comparison unavailable'
    print(f'Status:     {status}')
    print(f'Release:    https://github.com/{repo}/releases/latest')
    if status == 'Update available':
        print(f'Action:     A new version is available. Download it from https://github.com/{repo}/releases/latest')
    elif not current:
        print('Action:     Latest release shown above; installed version is unknown, so an update cannot be confirmed.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add', help='Save a GitHub repository for future checks')
    add.add_argument('repository', type=repository)
    sub.add_parser('list', help='List saved repositories')
    check = sub.add_parser('check', help='Check one repository or all saved repositories')
    check.add_argument('repository', type=repository, nargs='?')
    check.add_argument('--current', help='Installed version for a single repository')
    args = parser.parse_args()
    if args.command == 'check' and args.current and not args.repository:
        parser.error('--current requires a repository')
    try:
        data = load_state()
        if args.command == 'add':
            # GitHub names are case insensitive; preserve the first spelling.
            name = next((key for key in data if key.lower() == args.repository.lower()), args.repository)
            entry = data.setdefault(name, {'current': None})
            detected, source = detect_installed(name)
            entry['current'] = detected
            entry['detection'] = source
            save_state(data)
            print(f'Saved: {name} (installed: {detected or "Unknown"})')
            print(f'Detection: {source}')
            return 0
        if args.command == 'list':
            for name, entry in data.items():
                detected, source = detect_installed(name)
                print(f'{name}  installed: {detected or "Unknown"}')
                if not detected:
                    print(f'  {source}')
            if not data:
                print('No repositories saved. Use: gitapps add OWNER/REPO')
            return 0
        if args.repository:
            entry = next((v for k, v in data.items() if k.lower() == args.repository.lower()), {})
            return check_release(args.repository, args.current)
        if not data:
            print('No repositories saved. Use: gitapps add OWNER/REPO')
            return 0
        result = 0
        for index, (name, entry) in enumerate(data.items()):
            if index:
                print()
            result = max(result, check_release(name))
        return result
    except (OSError, ValueError, argparse.ArgumentTypeError) as error:
        print(f'Error: Cannot read or save repository registry: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
