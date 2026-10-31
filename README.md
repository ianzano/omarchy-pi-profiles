# Pi Profiles for Omarchy

A Quickshell bar plugin for [pi-profiles](https://github.com/chaychoong/pi-profiles).
The bar shows only the official Pi logo. Click to open a compact profile list;
hover to see the default profile.

- Click a profile row to launch it in the configured Omarchy terminal.
- Click the home icon beside a profile to set it as the default.
  A small Default label identifies the current selection.
- Click the trash icon to remove a profile with an inline confirmation. This permanently removes the
  profile directory, including its sessions; removing the default clears it.
- Refresh on opening, every ten seconds, or with a middle click on the bar button.
- Uses Omarchy theme colors, supports scrolling and Escape to dismiss.

## Screenshots

The actual QML menu rendered with example profiles.

| Profile list | Removal confirmation |
| --- | --- |
| ![Pi profile list with default indicator and direct actions](docs/screenshots/profiles.png) | ![Explicit confirmation before deleting a profile](docs/screenshots/confirmation.png) |

Regenerate these images with `python3 tools/screenshots.py` on an Omarchy system.
Rendering uses an isolated environment and does not read or modify your profiles.

## Install

Requires Omarchy's Quickshell bar, Python 3, pi, and `ppi` (`npm install -g pi-profiles`).
The desktop must have `ppi` on PATH or in the mise shims directory.

Install directly with Omarchy:

```sh
omarchy plugin add https://github.com/ianzano/omarchy-pi-profiles.git --enable
```

This clones the repository into `~/.config/omarchy/plugins/ianzano.pi-profiles/`
and enables the widget in the right bar section by default. Omarchy may ask
where to place it during interactive installation.

To install from a local checkout:

```sh
git clone https://github.com/ianzano/omarchy-pi-profiles.git
cd omarchy-pi-profiles
python3 install.py
```

The manual installer adds the widget beside the system tray, backs up
`shell.json` to `shell.json.bak.pi-profiles-<timestamp>`, and saves existing
plugin files under `~/.config/omarchy/plugin-backups/`. Reinstalling preserves
bar placement. Omarchy normally hot-reloads plugins; if an older version
remains visible, run `omarchy restart shell`.

`manifest.json`, `Panel.qml`, `backend.py`, and `pi-logo.svg` live at the
repository root so Omarchy can install the repository directly without running
`install.py`. The repository name is `omarchy-pi-profiles`; the plugin ID and
installed directory name are `ianzano.pi-profiles`.

## Update

For installations made with `omarchy plugin add`:

```sh
omarchy plugin update ianzano.pi-profiles
```

For manual installs, pull the repository and run `python3 install.py` again.
The manual installer copies runtime files rather than creating a Git checkout;
Omarchy's update command applies to installations made through its plugin manager.

## Remove

```sh
omarchy plugin remove ianzano.pi-profiles
```

To hide the bar widget without uninstalling it:

```sh
omarchy plugin disable ianzano.pi-profiles
```

Removing or disabling the plugin leaves your Pi profiles and sessions untouched.

## Validation

```sh
omarchy plugin validate .
python3 -m unittest discover -p test_backend.py -v
python3 test_ui.py
```

UI tests require a Wayland session. Tests use temporary profiles and do not
modify your real profiles. They cover default selection, removal confirmation
and cancellation, and independent launches of the same profile.

## Local data

The plugin discovers profiles using the installed `ppi` CLI and honors
`PPI_PI_ROOT`. It never reads auth files. Profile names and paths are discovered
locally at runtime; screenshots use example profiles.

## License

[MIT](LICENSE). The official Pi logo retains its upstream ownership; see [BRANDING.md](BRANDING.md).
