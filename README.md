# GitApps

**Version 0.2.0** · [راهنمای سادهٔ فارسی](README.fa.md) · [Version history](CHANGELOG.md)

A small Python terminal tool that checks installed applications against stable GitHub Releases and prints a download link when an update is available. Open-source and closed-source applications distributed through GitHub Releases are supported.

**Early version:** Linux-first. Checks and notifications only; it does not download or install updates, run a background service, or replace APT.

## Requirements

- Python 3.10 or later, Git, and an internet connection to api.github.com.
- No third-party Python packages required.
- Debian/Ubuntu package detection uses `dpkg-query`. Other systems currently only have executable detection.

## Install (Linux, current user)

```bash
git clone https://github.com/milad-mantashi/gitapps.git
cd gitapps
python3 install.py
```

The installer creates `~/.local/bin/gitapps`, pointing to this checkout. Keep the checkout in place. It refuses to overwrite an unrelated existing command. If the command is not found, add this to your shell configuration and open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Alternatively, run `./gitapps --help` from the checkout without installing.

## Usage

```bash
gitapps add https://github.com/domcyrus/rustnet
gitapps add localsend/localsend
gitapps add Happ-proxy/happ-desktop
gitapps list
gitapps check
gitapps check domcyrus/rustnet
```

`add` saves a repository and detects the installed version. Repeating it updates the same entry. `list` and `check` detect the current installation again, so external upgrades are reflected. LocalSend and Happ are included in the starter tracking list, without assuming they are installed.

Example output (illustrative versions):

```text
Repository: domcyrus/rustnet
Installed:  1.6.0
Latest:     v1.7.0
Status:     Update available
```

When an update is available, an `Action` line provides the release page for manual download. If installation detection fails, the tool still displays the latest release but does not claim an update exists.

## Detection and limitations

- Most CLI applications: looks for an executable matching the repository name and runs its `--version` with a five-second timeout, without a shell. Only add repositories whose corresponding local commands you trust.
- DEB packages: reads installed package metadata for a matching package name; Happ maps `Happ-proxy/happ-desktop` to package `happ`. Known GUI apps LocalSend and Happ are not launched to determine versions.
- Repository names are hints, not proof of executable provenance. Different application/package names need explicit mappings in `PACKAGE_NAMES` in `gitapps.py`.
- There is no universal discovery for AppImage, Flatpak, Snap, Docker, custom build paths, or arbitrary GUI apps yet.
- Stable numeric versions are compared; a leading `v`, omitted trailing zero components, and `+build` metadata are handled. Debian epoch and packaging revision are removed for comparison. Unsupported version formats are reported rather than guessed.
- Uses GitHub's latest stable release endpoint, not latest commits or prerelease channels. Repositories without stable Releases may return 404.
- GitHub's unauthenticated API rate limits apply. Authentication/private repositories are not implemented.
- Status output is in English. Exit code 0 means checks completed (including updates or unknown versions); 1 indicates an operation failed; 2 indicates invalid arguments. Other repositories continue to be checked after a network failure.

## Data and privacy

Saved repositories are stored in `$XDG_CONFIG_HOME/gitapps/repositories.json`, defaulting to `~/.config/gitapps/repositories.json`. The bundled `tracked_repositories.json` starter entries are merged with this file. No telemetry or tokens are stored. Checks contact GitHub for each selected repository.

## Update / uninstall

Update the checkout with `git pull --ff-only`. The command points to this checkout, so no reinstall is needed.

To uninstall, remove the `gitapps` symlink from `~/.local/bin`. Configuration is retained; remove `~/.config/gitapps` separately if desired (or the corresponding XDG path). Removing a bundled starter entry currently requires editing `tracked_repositories.json`; there is no `remove` command yet.

## Development

```bash
python3 -m unittest discover -s tests -v
```

Tests use temporary directories and mocked GitHub responses. They require no GitHub account and make no network calls.

Contributions are welcome: include a reproducible example, installed package/executable name, and tests for new detection mappings. Do not include credentials or personal configuration in issues or commits.

## License

MIT. See [LICENSE](LICENSE).

## Versioning and Debian package

Current application version: **0.2.0**. Run `gitapps --version`.
See [CHANGELOG.md](CHANGELOG.md) for the version policy and changes.

Build a DEB on Debian/Ubuntu with Python 3.10+ and `dpkg-deb` (from `dpkg`):

```bash
python3 scripts/build_deb.py
sudo apt install ./dist/gitapps_0.2.0-1_all.deb
/usr/bin/gitapps --version
```

The package is architecture-independent (`all`) and installs to `/usr/lib/gitapps`
with the command `/usr/bin/gitapps`. No pip packages are needed. It does not install
or upgrade any of the apps you track. Subsequent DEBs can be upgraded with the same
`apt install ./...deb` command; no GitApps APT repository is provided yet.

If you previously used `install.py`, `~/.local/bin/gitapps` may take precedence.
Inspect `command -v gitapps` and `ls -l ~/.local/bin/gitapps`; remove that old symlink
only if it belongs to GitApps, then run `hash -r` to use the packaged command.
The DEB intentionally does not modify files in users' home directories.

Remove the package with `sudo apt remove gitapps`. Your tracking configuration stays
in your user configuration directory. Release files and build outputs belong in
`dist/`; source installs can still use `python3 install.py`.

### Standalone DEB (bundled Python)

The standalone variant bundles the Python interpreter and standard library using
PyInstaller. End users do not need Python or pip; the DEB declares no package
Dependencies. Building it requires PyInstaller, which is a build-time dependency:

```bash
python3 -m venv .venv
.venv/bin/pip install pyinstaller==6.16.0
.venv/bin/python scripts/build_deb.py --standalone
sudo apt install ./dist/gitapps_0.2.0-1_amd64.deb
```

This is an architecture-specific Linux package. It still relies on the operating
system's glibc and basic system libraries; it is not a universal static binary.
Build on the oldest supported distribution. The supplied workflow is configured to build on
Ubuntu 22.04 for amd64 and test installation; its first successful run must be
verified before claiming support for that environment. The locally tested binary
was built on Ubuntu 26.04 (glibc 2.43), not on Ubuntu 22.04. DEB version detection uses the
system's dpkg-query; CLI detection uses the installed application's own command.

## Self-update checks (0.3.0)

GitApps itself is tracked by default. `gitapps check` compares the running version
with its latest release. When a newer release has exactly one architecture-matching
DEB, interactive terminals ask `Download the GitApps update? [y/N]`. Acceptance saves
the DEB to `~/Downloads/gitapps` without overwriting existing files. Size and, when
provided, GitHub's SHA-256 digest are checked. Installation remains manual; the
command is printed. Noninteractive checks only print a link. Version 0.2.0 needs
one manual upgrade to obtain this behavior. No periodic/background checks run.
