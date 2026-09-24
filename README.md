<p align="center">
  <img src="assets/linspectacles-logo.png" alt="LinSpectacles penguin X-ray roundel" width="180">
</p>

# LinSpectacles

**Linux Inspection Suite**

**Expose. Explore. Explain.**

LinSpectacles is a modular Linux inspection ecosystem built around focused, read-only inspection utilities. Standalone-capable **applets** inspect Linux subsystems independently; **LinSpectacles Hub** provides an optional integrated workbench for discovering, organizing and using them together; optional **Hub Modules** extend the workbench itself.

Current Hub release: **0.0.7-r1**

Repository: <https://github.com/linspectacles/linspectacles-hub>

## What LinSpectacles Hub is

LinSpectacles Hub is the integrated workbench for the LinSpectacles applet family. It is useful when several inspectors are installed, but it is deliberately **not required** for an applet to run.

The Hub provides the Dashboard, sidebar navigation, configuration, applet discovery/loading, Hub Module infrastructure, common presentation settings and integration points. Each applet retains its own inspection logic, runtime requirements and standalone launcher.

The Hub source release is deliberately **Hub-only**: applet and Hub Module payloads are released separately and can follow their own version and packaging cadence.

> **Applets inspect. The Hub connects, organizes and contextualizes.**

## Highlights

- Optional integrated **LinSpectacles Hub** with a dark interface.
- Standalone-capable applets remain independently usable outside the Hub.
- **Launch Standalone...** for the active embedded applet.
- Manifest-first discovery: applet/module metadata is read without importing component Python code.
- Optional **lazy loading** so enabled applets are imported only when first opened.
- Built-in **Dashboard** reports host-known state without triggering applet scans.
- **Inspection Coverage** with Enabled Only and Loaded Only filters.
- Independent **Hub Modules** for workbench capabilities that are not standalone inspectors.
- **Module API 5**, with compatibility for Module APIs 1–4.
- Separate module **Enabled** and **Dashboard** controls.
- Permissive offline module catalogue: uncatalogued installed modules remain valid.
- Portable/user components can override system/RPM components with the same logical ID.
- RPM-managed system components are visible to the Hub but remain owned by DNF/RPM.
- Portable integration metadata for **Suite Pythoine**.
- The Hub itself remains unprivileged.
- No automatic/background network access is required by the Hub.

## Interface

### Dashboard

Dashboard is the Hub's only built-in content page. It reports host-known state without opening applets or running their scans.

Built-in surfaces include:

- installed applet count
- enabled applet count
- applets loaded in the current session
- lazy-loading state
- enabled/installed Hub Module state
- **Inspection Coverage** for discovered applets
- **Hub State** for host-level/session information

Inspection Coverage can be filtered with **Enabled Only** and **Loaded Only**. When both are selected, both conditions must be satisfied.

Enabled Hub Modules may contribute Dashboard content, Hub State items and additional Inspection Coverage information. Their Dashboard contributions can be hidden without disabling the module itself.

### Sidebar

Dashboard remains fixed at the top of the sidebar.

Enabled applets appear beneath it as inspection views. An enabled organizer module may provide a richer navigation model while the Hub retains ownership of applet activation and lifecycle.

When an applet is active, **Launch Standalone...** starts its declared standalone launcher as a separate process. The embedded instance remains in place.

### Help and Tools

The built-in **Help** menu provides documentation, repository/issue links and **About LinSpectacles Hub**.

**Tools** is an extension point and remains hidden unless an enabled Hub Module contributes an action.

## Applets

An **applet** is a focused inspection application that can run independently or integrate into LinSpectacles Hub.

Applets do not depend on the Hub and must not import `linspectacles.*` merely to function standalone.

### Applet discovery

In **portable mode**, applets live in the source/runtime tree:

```text
applets/
```

A normal portable applet looks like:

```text
applets/my_applet/
  applet.json
  __init__.py
  applet.py
  standalone.py
```

In **RPM mode**, the Hub merges two stores:

```text
${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/
/usr/libexec/linspectacles/applets/
```

The first is user-owned. The second is immutable system content managed by RPM/DNF. If both contain the same logical applet ID, the valid user copy takes precedence.

### Applet management

Use **Configuration... → Applets** to inspect discovered applets and manage user/portable copies.

The Hub can enable/disable installed applets, add portable applet ZIPs, refresh discovery and launch applets standalone. User/portable applets may be removed by the Hub. System/RPM applets are identified as **System (RPM)** and are not deleted by LinSpectacles; removal belongs to the package manager.

ZIP installation requires one top-level applet directory and a valid manifest. Discovery itself does not execute applet code.

### Applet identity

Current prefixed manifests may use:

```text
linspectacles-<applet-id>
```

Legacy unprefixed IDs remain accepted and normalize to the same logical applet identity. The mistaken historical `linspector-<applet-id>` form is not accepted.

### Inspection behavior

Applet scan behavior belongs to the applet.

Potentially expensive or policy-sensitive acquisition can remain behind an explicit applet Scan action even when Hub lazy loading is disabled. Dashboard/coverage presentation does not trigger applet scans merely to populate host state.

## Hub Modules

A **Hub Module** extends the LinSpectacles workbench rather than inspecting a Linux subsystem as a standalone application.

Modules never become sidebar applets.

### Module discovery

In portable mode:

```text
modules/
```

A normal module looks like:

```text
modules/my_module/
  module.json
  module.py
```

In RPM mode, the Hub merges:

```text
${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/
/usr/libexec/linspectacles/modules/
```

A valid user copy takes precedence over a system/RPM copy with the same logical module ID.

Discovery reads `module.json` first. Python is imported only when the module is enabled.

### Module management

Use **Configuration... → Modules** to:

- see installed and catalogue-known modules
- enable or disable an installed module
- independently show/hide its Dashboard contributions
- add a portable module ZIP
- refresh discovery
- manage contribution order where supported

New user-installed modules remain **disabled** after installation so installation and execution remain separate trust decisions.

System/RPM modules can be enabled and used normally but cannot be removed by the Hub. DNF/RPM owns their installation, update and removal.

The built-in catalogue is offline and permissive. It does not download or automatically install modules, and an unknown installed module can still appear as **Uncatalogued**.

### Module API

The current Hub provides **Module API 5** and remains compatible with APIs 1–4.

Documented module services include:

- Help and Tools menu actions
- Dashboard widgets
- Configuration contributions
- Hub State items
- Inspection Coverage annotations and named columns
- host-known applet state
- declarative applet metadata
- current-applet state and applet activation
- namespaced module storage
- status reporting
- Hub events
- optional host-owned navigation organization

Module contributions registered through the host context are tracked and cleaned up when the module is disabled or removed.

See `MODULE-SDK.md` for the complete contract.

## Configuration

The base Configuration pages are:

```text
Applets → Appearance → Startup → Modules → About
```

Enabled modules may contribute additional pages according to the Module API. Applet and Module management remain distinct.

### Applets

Manage discovered applets, enabled state and runtime/source information.

### Appearance

Choose the font used by metadata/details panes in inspector applets. The selected font is applied to loaded applets when Configuration closes.

### Startup

**Lazy-load utilities** controls whether enabled applets are imported on first use or initialized during Hub startup.

Hub Modules are separate: enabled modules activate at startup because they contribute host functionality rather than sidebar views.

### Modules

Manage Hub Module installation source, activation, Dashboard visibility and contribution order.

### About

Identifies the running host precisely as **LinSpectacles Hub**, while retaining **Linux Inspection Suite** as the product descriptor.

## Useful keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+,` | Previous Applet |
| `Ctrl+.` | Next Applet |
| `F5` | Dashboard |
| `F1` | Documentation |

Previous/Next Applet follows the current visible sidebar order, wraps at either end and skips Dashboard.

## Runtime layouts

### Portable

The Hub can run from its source/portable tree:

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

- `main.py` — stable Hub entrypoint
- `linspectacles/` — Hub implementation and detailed release/implementation notes
- `assets/` — LinSpectacles artwork
- `applets/` — portable applet store
- `modules/` — portable Hub Module store
- `config/` — portable Hub preferences and namespaced module data
- `APPLET-SDK.md` — applet integration contract
- `MODULE-SDK.md` — Hub Module integration contract
- `suite-pythoine-extension.json` — Suite Pythoine identity/launch descriptor

### RPM

The Fedora/COPR package is:

```text
linspectacles-hub
```

The executable remains:

```text
linspectacles
```

Immutable Hub code and RPM-managed components live beneath:

```text
/usr/libexec/linspectacles/
```

Mutable user state remains user-owned:

```text
${XDG_CONFIG_HOME:-~/.config}/linspectacles/
${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/
${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/
```

Normal Hub operation does not require running the GUI as root.

## Suite Pythoine

LinSpectacles remains independently runnable.

Suite Pythoine integration is exposed through the bundled descriptor:

```bash
python3 main.py --suite-pythoine
```

which launches the same application, while:

```bash
python3 main.py --component-info
```

prints the component descriptor as JSON.

The descriptor identifies LinSpectacles as a portable Linux **Extension**, with no file-routing or new-file role.

## Running from source

LinSpectacles Hub requires **Python 3** and **PyQt6**.

From the source root:

```bash
python3 main.py
```

Useful launch forms:

```bash
python3 main.py --suite-pythoine
python3 main.py --component-info
```

Applet-specific dependencies belong to the individual applets rather than to the Hub.

## Fedora RPM build

The Hub repository carries its RPM packaging under:

```text
packaging/rpm/
```

On Fedora, the included build script creates the RPM/SRPM artifacts used for COPR testing and publication. RPM packaging remains separate from normal Hub runtime behavior.

## Current release

**0.0.7-r1** completes the built-in offline Hub Module catalogue by adding **Boot Environment** and **System Identity**, which were already valid/discoverable installed Modules but were missing from the known catalogue.

The underlying 0.0.7 release introduced packaged-system component discovery. RPM-installed applets and modules can live under `/usr/libexec/linspectacles/{applets,modules}`, while user-owned XDG copies remain writable and take precedence for duplicate logical IDs.

For detailed implementation/release history, see [`linspectacles/README.md`](linspectacles/README.md).

## Configuration storage

Portable mode stores host preferences beneath:

```text
config/
```

RPM mode uses:

```text
${XDG_CONFIG_HOME:-~/.config}/linspectacles/
```

Module data is namespaced within the active configuration/data model so one module cannot accidentally share another module's state.

## Branding

The approved LinSpectacles mark is stored under `assets/` and is used for application identity and About presentation.

Project identity:

```text
LinSpectacles
Linux Inspection Suite
Expose. Explore. Explain.
```

Host identity:

```text
LinSpectacles Hub
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

LinSpectacles Hub is licensed under the **GNU General Public License v3.0 or later**.

See `LICENSE` for the complete license text.

Copyright © 2026 **brunonlinespace**.

## Links

- LinSpectacles Hub: <https://github.com/linspectacles/linspectacles-hub>
- Issues: <https://github.com/linspectacles/linspectacles-hub/issues>
- LinSpectacles organization: <https://github.com/linspectacles/>
- brunonlinespace: <https://github.com/brunonlinespace/>
