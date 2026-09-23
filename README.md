# LinSpectacles — Linux Inspection Suite

<p align="center">
  <img src="assets/linspectacles-logo.png" alt="LinSpectacles penguin X-ray roundel" width="180">
</p>

**Linux Inspection Suite**

**Expose. Explore. Explain.**

LinSpectacles is a modular, portable Linux inspection host for focused, read-only inspection utilities. Standalone-capable **applets** inspect Linux subsystems; optional **Suite Modules** extend the host itself without becoming sidebar inspectors.

Current release: **0.0.4-r1**

Repository: <https://github.com/linspectacles/linspectacles-suite>

## What LinSpectacles is

LinSpectacles keeps the Suite shell separate from the inspectors it hosts.

The shell provides the Dashboard, sidebar navigation, portable configuration, applet discovery and loading, Suite Module infrastructure, common presentation settings, and integration points. Individual applets remain independently launchable and own their own inspection logic and runtime requirements.

The current Suite source release is deliberately **shell-only**: applet and Suite Module payloads are installed separately and can follow their own release cadence.

## Highlights

- Modular, portable **Linux inspection host** with a dark interface.
- Standalone-capable **applets** discovered from the root-level `applets/` store.
- **Launch Standalone...** for the active applet, both above Configuration and from the sidebar context menu.
- Manifest-first applet discovery: discovery reads `applet.json` without importing applet code.
- Optional **lazy loading** so enabled applets are imported only when first opened.
- Built-in **Dashboard** showing host-known applet coverage and Suite/session state without triggering applet scans.
- Dashboard **Enabled Only** and **Loaded Only** filters for Inspection Coverage.
- Portable host preferences, including metadata font and per-applet hidden-column state.
- Independent **Suite Modules** for host-level capabilities that are not standalone inspectors.
- **Module API 5**, with compatibility for Module API 1, 2, 3 and 4.
- Separate module **Enabled** and **Dashboard** controls.
- Reorderable module Dashboard/configuration contributions where the module permits it.
- Module-contributed Tools/Help actions, Dashboard widgets, Configuration pages, Suite State items and Inspection Coverage data.
- Offline module catalogue/manager; unknown installed modules remain discoverable rather than being rejected by a whitelist.
- Explicit separation between applet inspection work and Suite Module host extensions.
- Portable integration metadata for **Suite Pythoine**.
- The LinSpectacles host itself remains unprivileged.

## Interface

### Dashboard

Dashboard is the Suite's only built-in content page.

It reports host-known state without opening applets or running their scans. The built-in surfaces include:

- installed applet count
- enabled applet count
- applets loaded in the current session
- lazy-loading state
- enabled/installed Suite Module state
- **Inspection Coverage** for discovered applets

Inspection Coverage can be filtered with **Enabled Only** and **Loaded Only**. When both are selected, both conditions must be satisfied.

Enabled Suite Modules may also contribute Dashboard content, Suite State items, and additional Inspection Coverage columns. Their Dashboard contributions can be hidden without disabling the module itself.

### Sidebar

Dashboard remains fixed at the top of the sidebar.

Enabled applets appear as the inspection views beneath it. The host can also accept a navigation model from an enabled organizer module while retaining host ownership of applet activation and lifecycle.

When an applet is active, **Launch Standalone...** starts the applet's declared standalone launcher as a separate process. The embedded applet remains in place.

### Help and Tools

The built-in **Help** menu provides:

- Documentation
- GitHub Repository
- Raise an Issue
- About LinSpectacles

**Tools** is an extension point and remains hidden unless an enabled Suite Module contributes an action.

## Applets

An **applet** is a focused inspection application that can run independently or integrate into LinSpectacles.

LinSpectacles discovers applets from:

```text
applets/
```

A standard applet provides:

```text
applets/my_applet/
  applet.json
  __init__.py
  applet.py
  standalone.py
```

The applet factory returns a Qt widget for embedded use. The declared `standalone.py` remains the independent launcher.

Applets must not import `linspectacles.*`; the standalone boundary is intentional.

### Applet management

Use **Configuration... → Applets** to:

- enable or disable an installed applet
- add an applet ZIP
- remove an applet
- refresh discovery
- open the applets folder

Disabling an applet hides it without deleting its files. Removing it deletes that applet folder from the portable copy.

ZIP installation requires one top-level applet directory and a valid manifest. Applet discovery itself does not execute applet code.

### Applet identity

Newly prefixed applet manifests may use:

```text
linspectacles-<applet-id>
```

Legacy unprefixed IDs remain accepted.

For host configuration, navigation and Module API consumers, the prefixed and legacy forms resolve to the same logical applet identity. The mistaken historical `linspector-<applet-id>` prefix is not accepted.

### Inspection behavior

Applet scan behavior belongs to the applet.

Potentially expensive or policy-sensitive inspection can remain behind an explicit applet Scan action even when Suite lazy loading is disabled. The Dashboard does not cause an applet scan merely to report coverage state.

Official non-live inspector applets may expose **Export...** for already-collected data. Export must not silently trigger additional inspection.

## Suite Modules

A **Suite Module** extends the LinSpectacles host rather than inspecting a Linux subsystem as a standalone application.

Modules live in:

```text
modules/
```

A standard module provides:

```text
modules/my_module/
  module.json
  module.py
```

Discovery reads `module.json` only. Python is imported only when the module is enabled.

Suite Modules never become sidebar applets.

### Module management

Use **Configuration... → Modules** to:

- see installed and catalogue-known modules
- enable or disable an installed module
- independently show or hide its Dashboard contributions
- add a module ZIP
- remove a module
- move reorderable modules Up or Down
- refresh discovery
- open the modules folder

Newly user-installed modules are left **disabled** after installation, keeping installation and execution as separate trust decisions.

The catalogue is offline and permissive. It does not download or automatically install modules, and an unknown installed module can still appear as **Uncatalogued**.

### Module API

The current host provides **Module API 5** and remains compatible with APIs 1–4.

Documented module services include:

- Help and Tools menu actions
- Dashboard widgets
- Configuration pages
- Suite State items
- Inspection Coverage annotations and named columns
- host-known applet state
- declarative applet manifest metadata
- current-applet state and applet activation
- portable namespaced module storage
- status reporting
- Suite events
- optional host-owned navigation organization

Module contributions registered through the host context are tracked and cleaned up when the module is disabled or removed.

See `MODULE-SDK.md` for the complete contract.

## Configuration

The base Configuration pages are:

```text
Applets → Appearance → Startup → Modules → About
```

An enabled Applet Organizer module may contribute a page before **Applets**. Other enabled module-owned Configuration pages are placed after **Startup** and before **Modules**.

### Applets

Manage installed applets and their enabled state.

### Appearance

Choose the font used by metadata/details panes in inspector applets. The selected font is applied to loaded applets when Configuration closes.

### Startup

**Lazy-load utilities** controls whether enabled applets are imported on first use or initialized during Suite startup.

Suite Modules are separate: enabled modules activate at startup because they contribute host features rather than sidebar views.

### Modules

Manage Suite Module installation, activation, Dashboard visibility and contribution order.

### About

Shows LinSpectacles identity, version, organisation ID, repository, copyright and GPL licensing information.

## Useful keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+,` | Previous Applet |
| `Ctrl+.` | Next Applet |
| `F5` | Dashboard |
| `F1` | Documentation |

Previous/Next Applet follows the current visible sidebar order, wraps at either end, and skips Dashboard.

## Portable layout

The Suite uses a portable layout around `main.py`:

```text
main.py
linspectacles/
assets/
applets/
modules/
config/
APPLET-SDK.md
MODULE-SDK.md
suite-pythoine-extension.json
LICENSE
README.md
```

Key roles:

- `main.py` — stable host entrypoint
- `linspectacles/` — Dashboard host shell, configuration, applet loader and Suite Module infrastructure
- `assets/` — LinSpectacles application artwork
- `applets/` — removable standalone-capable inspection utilities
- `modules/` — optional Suite-level capabilities
- `config/` — portable host preferences and namespaced module data
- `APPLET-SDK.md` — applet integration contract
- `MODULE-SDK.md` — Suite Module integration contract
- `suite-pythoine-extension.json` — Suite Pythoine extension identity/launch descriptor

The `applets/` and `modules/` stores may be created beside the host as components are installed.

## Suite Pythoine

LinSpectacles remains independently runnable.

Suite Pythoine integration is exposed through the bundled extension descriptor:

```bash
python3 main.py --suite-pythoine
```

launches the same LinSpectacles application, while:

```bash
python3 main.py --component-info
```

prints the extension descriptor as JSON.

The descriptor identifies LinSpectacles as a portable Linux **Extension**, with no file-routing or new-file role.

## Running from source

LinSpectacles requires **Python 3** and **PyQt6**.

From the portable source root:

```bash
python3 main.py
```

Useful launch forms:

```bash
python3 main.py --suite-pythoine
python3 main.py --component-info
```

Applet-specific dependencies belong to the individual applets rather than to the host.

## Current release

Version **0.0.4-r1** is a focused shell revision.

It retains the 0.0.4 behavior and corrects **Configuration → Modules** table sizing so the **Suite Module** column stretches to use the available width while Installed, Enabled, Dashboard, Version and Editor remain content-sized, including after Refresh, Add and Remove operations.

Version 0.0.4 introduced the Suite-owned **Launch Standalone...** action for active applets, the current Configuration-page placement rules, and the Dashboard **Enabled Only / Loaded Only** coverage filters.

## Configuration storage

Host preferences are stored portably in:

```text
config/linspectacles.json
```

The configuration includes lazy-loading state, disabled applets, metadata font, per-applet hidden columns, module enabled state, module Dashboard visibility and module order.

Each Suite Module can also receive its own portable storage directory under:

```text
config/modules/<module-id>/
```

## Branding

The approved LinSpectacles mark is stored under `assets/` and is used for Suite application identity and About presentation.

The project identity is:

```text
LinSpectacles
Linux Inspection Suite
Expose. Explore. Explain.
```

Technical organisation ID:

```text
linspectacles
```

Publisher/editor identity:

```text
brunonlinespace
```

## License

LinSpectacles is licensed under the **GNU General Public License v3.0 or later**.

See `LICENSE` for the complete license text.

Copyright © 2026 **brunonlinespace**.

## Links

- LinSpectacles Suite: <https://github.com/linspectacles/linspectacles-suite>
- Issues: <https://github.com/linspectacles/linspectacles-suite/issues>
- LinSpectacles organisation: <https://github.com/linspectacles/>
- brunonlinespace: <https://github.com/brunonlinespace/>
