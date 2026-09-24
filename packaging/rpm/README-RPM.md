# LinSpectacles Hub RPM packaging

This package installs **only the LinSpectacles Hub application** as an RPM.
Applets and Hub Modules may remain portable user components or be installed as
separate immutable RPM-managed system components.

## Runtime ownership

The RPM payload is immutable and is expected under standard system locations:

- `/usr/bin/linspectacles` — launcher
- `/usr/libexec/linspectacles/` — Hub code/assets/docs
- `/usr/libexec/linspectacles/applets/` — immutable system applet discovery root
- `/usr/libexec/linspectacles/modules/` — immutable system Hub Module discovery root
- `/usr/share/applications/linspectacles.desktop` — desktop integration
- `/usr/share/icons/hicolor/.../linspectacles.png` — application icon
- `/usr/share/metainfo/...` — AppStream metadata

LinSpectacles performs no normal runtime writes there. In RPM mode mutable data is:

- `${XDG_CONFIG_HOME:-~/.config}/linspectacles/linspectacles.json`
- `${XDG_CONFIG_HOME:-~/.config}/linspectacles/modules/<module-id>/`
- `${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/`
- `${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/`

Therefore adding/removing user applets/modules, changing preferences and
launching applets standalone do not require root privileges. RPM-owned system
components are never deleted by the Hub; they are installed/removed by DNF.
When the same logical component ID exists in both places, the user XDG copy wins.

## Build on Fedora

Run:

```bash
./packaging/rpm/build-rpm-fedora.sh
```

The script does not use `sudo` or install dependencies. It expects Fedora RPM
build and desktop/AppStream validation tools to already be installed. Finished
RPM/SRPM files are copied to `dist-rpm/`.

The application identifies itself as `0.0.7-r1`; the RPM package is **`linspectacles-hub`** with `Version: 0.0.7`, `Release: 2`.

### 0.0.7 packaged component discovery

RPM mode now merges user-owned XDG component stores with immutable system stores under `/usr/libexec/linspectacles/applets/` and `/usr/libexec/linspectacles/modules/`. The user store has precedence for duplicate logical IDs. Configuration exposes the source of each component and does not offer deletion of system/RPM-owned payloads. The Hub package itself creates the two system discovery roots but does not ship applet or module payloads.

### 0.0.6-r1 package cleanup

The Hub package now owns only **`linspectacles-hub`**. The temporary `Obsoletes` rules for the old `linspectacles` and `linspectacles-suite` experimental package names have been removed so those names are free for the finalized package taxonomy. The executable remains `/usr/bin/linspectacles`, the desktop/AppStream identity remains LinSpectacles, and the About surfaces identify the host precisely as **LinSpectacles Hub**.

### 0.0.6 Hub identity

The host application package became **`linspectacles-hub`**, matching the repository `https://github.com/linspectacles/linspectacles-hub`. The executable remained `/usr/bin/linspectacles`, the desktop/AppStream identity remained LinSpectacles, and mutable XDG paths were unchanged. The original 0.0.6 build temporarily obsoleted the prior experimental package names only to complete the one-time rename migration; 0.0.6-r1 removes that temporary rule.

### exp1-r1 build-path correction

The build script uses a user-owned cache RPM topdir by default, and the spec quotes all buildroot destinations, so source projects may live under directories whose names contain spaces.

### exp1-r2 metadata validation correction

The AppStream developer ID is the reverse-DNS `io.github.linspectacles`, and the desktop entry uses one primary category (`System`). This addresses the Fedora `appstreamcli validate` failure and the `desktop-file-validate` duplicate-main-category hint observed with exp1-r1.

### exp1-r3 package/software-center metadata refinement

The RPM now declares `Vendor: LinSpectacles` and `Packager: brunonlinespace` for package frontends. AppStream metadata now also carries the System category, search keywords, VCS URL, provided `linspectacles` binary, and a release description. This prepares repository-generated AppStream catalogues for richer Discover/software-center presentation. No screenshots are declared because no stable hosted screenshot assets are part of this experiment.

### exp1-r4 package rename

The RPM package is now **`linspectacles-suite`** rather than `linspectacles`. The spec declares the former `linspectacles` package as provided/obsolete so DNF can replace an installed exp1-r3 package during repository upgrade. The command remains `/usr/bin/linspectacles`, and runtime/XDG paths remain unchanged.
