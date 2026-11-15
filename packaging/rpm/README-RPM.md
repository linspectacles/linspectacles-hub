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
- `/usr/share/applications/linspectacles-hub.desktop` — desktop integration
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
When the same logical component ID exists in the XDG User source and the RPM-managed source, both copies remain discovered; normal presentation follows the User/Package-managed preference without comparing versions.

## Build on Fedora

Run:

```bash
./packaging/rpm/build-rpm-fedora.sh
```

The script does not use `sudo` or install dependencies. It expects Fedora RPM
build and desktop/AppStream validation tools to already be installed. Finished
RPM/SRPM files are copied to `dist-rpm/`.

The application identifies itself as `0.2.2`; the RPM package is **`linspectacles-hub`** with `Version: 0.2.2`, `Release: 1`.


### 0.2.2 contextual window titles

- Keeps the desktop application identity **LinSpectacles Hub**.
- Uses context-only Qt window titles so KDE can present **Dashboard — LinSpectacles Hub** or **Applet Name — LinSpectacles Hub** without duplicating the application name.
- Uses **Configuration** as the Configuration dialog's context-only title.
- Leaves Hub runtime, component management, shortcuts and Module API behavior unchanged.


### 0.2.1 contextual-help label / README correction

- Corrects the Hub contextual Encyclopedia action label to **What's This?**.
- Keeps complete release history in the nested `linspectacles/README.md`; root Current release now contains only the actual current release.
- Adds the requested Hub screenshot to the root README Interface section.
- Leaves 0.2.0 Hub behavior otherwise unchanged.

### 0.2.0 Hub command/identity consolidation

- Desktop identity is **LinSpectacles Hub** and the desktop entry is `linspectacles-hub.desktop`.
- Removes visible Help/Tools menus; Documentation remains on `F1`.
- `Ctrl+W` opens Dashboard; `F5` launches the active applet standalone.
- Configuration → About is the sole About surface and exposes README, License, Repository and Issues.
- Module API 8 adds applet-contextual sidebar actions; legacy Encyclopedia What's This? is bridged automatically.

### 0.1.12 restore original tab-page frame

- Restores the pre-0.1.9 `QTabWidget::pane` border exactly (`1px solid #333333`).
- Leaves tab-button styling, Cgroups tree styling and Runtime/Startup behavior unchanged.
- No runtime, discovery, component-management or table behavior changes.

### 0.1.11 Runtime/Startup consolidation

- Merges the standalone Startup Configuration tab into Runtime as a Startup section.
- Preserves Lazy-load utilities behavior and persistence unchanged.
- Base Configuration order becomes Applets, Modules, optional module pages, Runtime, Appearance, About.
- No runtime migration, discovery, component-management or styling behavior changes.

### 0.1.10 tab-frame and tree-style correction

- Restores the existing individual tab-button borders and removes the surrounding `QTabWidget::pane` border instead.
- Adds the Cgroups Inspector 0.0.6 `QTreeWidget` background/frame rule to the Hub stylesheet.
- No runtime, discovery, module-management or table-sorting behavior changes.

### 0.1.9 Configuration clarity

- Reorders Configuration tabs to Applets, Modules, optional module pages, Startup, Runtime, Appearance, About.
- Simplifies Applets column labels/order and keeps Layer then Favourite at the far right.
- Adds click-to-sort Applets/Modules headers and removes individual tab outlines.

### 0.1.8 module-management simplification

- Hub Module enablement is logical-ID based; User/Package-managed preference selects the runtime copy.
- Configuration puts Module first and shows physical installed copies separately for provenance/removal.
- Sidebar title readability is restored without abandoning compact version/source provenance.

### 0.1.7 component-model consolidation

- Dashboard Inspection Coverage now reports applet Source directly.
- Configuration distinguishes provider/source provenance from generic Manual/Managed ownership.
- Duplicate-instance discovery, Manual/Managed preference, runtime migration and package ownership behavior are otherwise unchanged.

### 0.1.6 runtime-owned Manual storage

- Packaged runtime remains integrated and uses XDG for configuration and Manual applets/modules.
- Source Portable/Integrated migration is implemented only for source builds; packaged runtime exposes no mode switch.
- Manual-versus-Managed duplicate presentation from 0.1.5 remains unchanged.

### 0.1.4 runtime-classification correction

Integrated source trees are now recognized from existing desktop integration that points to the exact `main.py`, including Suite Pythoine's launcher metadata. Packaged/RPM classification is unchanged and Suite Pythoine itself requires no change.

### 0.1.2 runtime/path model

- Classifies the Hub runtime independently as Source Portable, Source Integrated, or Packaged.
- Packaged Hub state remains XDG-backed; the current RPM launcher remains a supported packaged-provider declaration.
- Generalizes component ownership internally to Manual versus Managed while retaining RPM as the currently implemented managed provider/source label.
- Does not add runtime migration, source-mode switching, launcher mutation, Manual-vs-Managed presentation preference, or component-policy changes.

### 0.1.1 Hub implementation decomposition

- Refactor-only source organization release; runtime behavior and packaging layout are unchanged.
- Decomposes the former monolithic Hub implementation into focused main-window, configuration, Dashboard, navigation, applet-host and module-host units.
- Retains the `linspectacles.host` compatibility import surface.

### 0.1.0 explicit manual/RPM component sources

- Uses the XDG Manual source plus the known RPM/system Managed source.
- Does not scan any other manual locations as fallbacks.
- Keeps Manual and RPM copies with the same logical ID separately visible in Configuration while normal presentation follows the Manual/Managed preference.
- Add, Remove and Open Folder act only on the XDG Manual source; RPM payloads remain DNF/RPM-owned.
- Applet navigation shows compact `version · source` provenance beneath the title.
- No persistent component registry is introduced.

### 0.0.11 applet table / tab visual parity

- Applies Kernel Modules alternating-row table styling and Linux ResMon full rounded tab corners.
- No runtime, Module API, discovery, applet, module, or packaging-layout changes.

### 0.0.10 Dashboard text-entry focus correction

- Prevents Hub Dashboard type-to-search from hijacking printable input from module-owned text fields such as Encyclopedia search.
- No Module API, discovery, applet, module, or packaging-layout changes.

### 0.0.9 single-table Organizer / shared Portable discovery

Module API 7 lets optional modules contribute columns/actions to the one Hub-owned Applets table. Applet Organizer 0.0.4 uses that API for Favourite/Category rather than stacking another grid. Portable mode now reads shared XDG User and System (RPM) component stores after its own Portable store, while all Portable installs/removals/configuration remain local to the portable tree.

### 0.0.8 Hub-owned applet navigation / Module API 6

The Hub now owns applet search independently of Applet Organizer, adds Configuration → Applets search and drag/drop ZIP installation, and exposes Module API 6 so optional modules can enhance that existing Applets page. RPM/user component discovery, precedence and package-manager ownership remain unchanged.

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
