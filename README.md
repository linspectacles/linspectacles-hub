<p align="center">
  <img src="assets/linspectacles-logo.png" alt="LinSpectacles penguin X-ray roundel" width="180">
</p>

# LinSpectacles

**Linux Inspection Suite**

**Expose. Explore. Explain.**

LinSpectacles is a modular Linux inspection ecosystem built around focused, read-only inspection utilities. Standalone-capable **applets** inspect Linux subsystems independently; **LinSpectacles Hub** provides an optional integrated workbench for discovering, organizing and using them together; optional **Hub Modules** extend the workbench itself.

Current Hub release: **0.2.2**

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
- **Module API 8**, with compatibility for earlier Module APIs.
- Logical-module **Enabled** and **Dashboard** controls.
- Permissive offline module catalogue: uncatalogued installed modules remain valid.
- Runtime mode owns the single **User** component location: Source Portable uses the Hub tree; Source Integrated and Packaged use XDG user data. The known **Package-managed/system** source is discovered separately; duplicate physical copies remain visible in Configuration while ordinary navigation follows the user's User/Package-managed preference.
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

### Documentation, About and contextual help

The Hub has no Help or Tools menu. **F1** opens Hub documentation. **Configuration → About** is the single About surface and provides README, License, Repository and Issues links. Enabled modules may contribute compact contextual actions above **Launch Standalone...**; Encyclopedia's **What's This?** uses this surface.

### Hub shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+,` | Previous applet |
| `Ctrl+.` | Next applet |
| `Ctrl+F` | Focus applet search |
| `Ctrl+W` | Dashboard |
| `F5` | Launch active applet standalone |
| `F1` | Hub documentation |
| `Shift+F1` | What's This? when provided by Encyclopedia |

<p align="center">
  <a href="https://github.com/brunonlinespace/brunonlinespace/blob/main/linspectacles/linspectacles-hub.png">
    <img
      src="https://raw.githubusercontent.com/brunonlinespace/brunonlinespace/main/linspectacles/linspectacles-hub.png"
      alt="LinSpectacles Hub screenshot"
      width="900"
    >
  </a>
</p>

## Applets

An **applet** is a focused inspection application that can run independently or integrate into LinSpectacles Hub.

Applets do not depend on the Hub and must not import `linspectacles.*` merely to function standalone.

### Applet discovery

LinSpectacles discovers applets from exactly two sources:

1. the runtime-owned **User** component location; and
2. the known **Package-managed/system** location.

User storage is not an independent folder preference:

- **Source — Portable:** `<Hub>/applets/`
- **Source — Integrated:** `${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/`
- **Packaged:** `${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/`

The current Fedora package-managed provider reads RPM applets from `/usr/libexec/linspectacles/applets/` (or the packaged system root). LinSpectacles does not silently scan other manual stores.

If User and Package-managed sources both contain the same logical applet ID, **both copies remain discovered and visible in Configuration**. Ordinary sidebar navigation shows the enabled copy from the global **Prefer User / Prefer Package-managed** setting. If only one enabled copy exists, that copy is shown regardless of preference. Versions are never compared and no persistent applet registry is created.

A normal User applet looks like:

```text
<user-root>/applets/my_applet/
  applet.json
  __init__.py
  applet.py
  standalone.py
```

### Applet management

Use **Configuration... → Applets** to inspect discovered copies and manage the runtime-owned User source. The Hub-owned page includes permanent applet search; `Ctrl+F` focuses search, and type-to-search works from Dashboard/sidebar navigation contexts without requiring Applet Organizer.

**Add Applet...**, drag-and-drop installation, **Remove**, and **Open User Applets Folder** operate only on the active User source. Package-managed applets remain visible but are package-provider owned and cannot be deleted by LinSpectacles.

For source builds, **Configuration → Runtime** can migrate the Hub between Portable and Integrated. Configuration is copied to the target runtime; manual applets/modules may be copied optionally; existing destination component folders are never overwritten; the old side is left intact; desktop integration is removed/created as appropriate; and the Hub restarts using the target paths.

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

**0.2.2** corrects Hub window-title ownership: the desktop application identity remains **LinSpectacles Hub**, while the active Hub window title now reports only its current context, allowing the desktop shell to present **Dashboard — LinSpectacles Hub** or **Applet Name — LinSpectacles Hub** without duplicating the application name. Configuration follows the same context-only title rule.

## Configuration storage

**Source — Portable** stores host preferences beneath the Hub tree:

```text
config/
```

**Source — Integrated** and **Packaged** use:

```text
${XDG_CONFIG_HOME:-~/.config}/linspectacles/
```

Manual applets/modules likewise follow runtime ownership: internal for Source Portable, XDG user data for Integrated/Packaged. Module data is namespaced within the active configuration model so one module cannot accidentally share another module's state.

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
