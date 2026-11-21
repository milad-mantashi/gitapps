# Changelog

Versions follow Semantic Versioning (MAJOR.MINOR.PATCH). During 0.x development,
minor releases may change behavior; patch releases contain compatible fixes.
The Python `__version__` constant is the source of truth for the CLI and DEB builder.
DEB versions append a packaging revision (for example, `0.2.0-1`).

## 0.2.0 — 2026-11-21

- Add `gitapps --version`.
- Add a rootless DEB builder and system-wide `/usr/bin/gitapps` command.
- Document installation, upgrades and package removal.

## 0.1.0 — 2026-11-21

Initial published snapshot (retrospective version label; no 0.1.0 release tag).

- Register GitHub repositories, list them, and check stable Releases.
- Detect versions using CLI output and Debian package metadata.
- Support the Happ package-name mapping and LocalSend build metadata.
- Show manual download links for new versions, including closed-source apps.
