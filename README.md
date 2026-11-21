# GitApps

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
