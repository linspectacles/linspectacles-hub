# LinSpectacles Applet SDK

LinSpectacles discovers applets from manifest directories. Portable mode uses the root-level `applets/` directory. RPM mode merges the writable user store `${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/` with the immutable system store `/usr/libexec/linspectacles/applets/`; a valid user applet wins when both stores expose the same logical applet ID. Discovery reads `applet.json` only; Python code is not imported until an enabled applet is opened, unless lazy loading is disabled. System-installed applets are package-manager owned and are not deleted by the Hub.

## Identity

This distribution uses `linspectacles` as the Suite organisation ID and `brunonlinespace` as official applet author/editor/publisher metadata.

## Required files

```text
<active-applet-store>/my_applet/
  applet.json
  __init__.py
  applet.py
  standalone.py
```

A self-contained applet may add any local support modules it needs. It must not import `linspectacles.*`; this keeps applets independently launchable and prevents experiments from coupling themselves to the host.

## Manifest

```json
{
  "schema": 1,
  "id": "linspectacles-my-applet",
  "name": "My Applet",
  "version": "0.0.1",
  "author": "brunonlinespace",
  "editor": "brunonlinespace",
  "publisher": "brunonlinespace",
  "order": 100,
  "entrypoint": "applet.py",
  "factory": "create_applet",
  "standalone": "standalone.py"
}
```

`create_applet(parent=None)` must return a `QWidget`. LinSpectacles never needs to know the applet's implementation class.

### Applet ID compatibility

LinSpectacles accepts both applet manifest ID forms:

- newer prefixed form: `linspectacles-<applet-id>`
- legacy form: `<applet-id>`

The mistaken `linspector-<applet-id>` prefix from 0.0.3-r3 is **not accepted**. Use `linspectacles-<applet-id>` for newly prefixed manifests.

Both forms resolve to the same logical applet identity. For example, `linspectacles-kernel-modules` and `kernel-modules` are treated as the same applet ID (`kernel-modules`) by host configuration, navigation and Module API consumers. This preserves existing user settings and module/catalogue references while allowing newly packaged applets to use the prefixed identity.

## Optional lifecycle hook

A live applet may expose:

```python
def set_applet_active(self, active: bool):
    ...
```

The host calls it when the applet becomes selected or hidden. Live applets can use this hook to pause sampling while hidden. Ordinary inspectors do not need it. Resource Monitor is not bundled in the exp7 LinSpectacles line.

## Intentional scans

Applets that perform potentially expensive or policy-sensitive probes may present an explicit Scan action and remain unscanned when constructed. This behavior is independent of the host's lazy-loading preference. Official Boot Inspector, Installed Software and Python Packages follow this model. SELinux Inspector also keeps Recent Denials unscanned until the user explicitly chooses a scan.

## Standalone

Every LinSpectacles applet is standalone-capable and declares its launcher through the manifest `standalone` field (normally `standalone.py`). Run that file with Python to launch only that utility. The applet owns its dependencies and any local settings it needs.

When an applet is active in the Suite, the host exposes **Launch Standalone...** above **Configuration...** and in the applet sidebar context menu. This starts a separate standalone process/window from the declared launcher; it does not detach, re-parent or transfer the currently embedded applet instance.

## Adding and removing

Users may manually add/remove valid applet folders or use **Configuration... → Applets**. ZIP installation requires one top-level applet directory and a valid manifest. Discovery never executes applet code.

## Core boundary

Dashboard is the host's only built-in content page. Every bundled inspector utility is an applet and may be removed without changing the host. Resource Monitor is intentionally decoupled from LinSpectacles in exp7.

## Optional branding asset

An applet may include `icon.png` beside `applet.py`. Official brunonlinespace applets use the LinSpectacles mark for standalone window/application identity. The host does not require or execute the icon during discovery.
## Optional host presentation settings

Inspector applets may expose:

```python
def apply_host_settings(self, settings=None, column_visibility_callback=None):
    ...
```

The current host supplies `metadata_font` (a serialized Qt `QFont`) and the applet's persisted `hidden_columns`. The callback lets an applet report changed column visibility without importing `linspectacles.*`. Standalone launchers remain valid without this hook or without host settings.

Official table-based applets use a right-click header menu for column visibility. At least one column remains visible.

## Export

Official non-live inspector applets expose an **Export...** action at the far right of their top action row. Export operates on data already collected by the applet and must not silently trigger extra system probes. Plain text is the default format; CSV, JSON and Markdown are optional alternatives.


## Optional privileged inspection

An applet may offer an explicitly user-requested privileged inspection when ordinary read-only access is insufficient, but the **LinSpectacles host and applet GUI must remain unprivileged**. Elevation should be narrowly scoped to a fixed external command with fixed-purpose arguments, invoked without a shell, after a clear confirmation. The applet must continue to provide useful unprivileged behavior when elevation is declined or unavailable.

SELinux Inspector demonstrates this pattern for Recent Denials: **Scan with Privileged Access...** can invoke only `ausearch` through `pkexec` to read audit records. It does not run LinSpectacles as root and does not modify SELinux policy, booleans, labels, or enforcement mode.
## Hub Modules are separate

Hub-level enhancements use the independent `modules/` store and `MODULE-SDK.md`. Applets remain standalone and must not import or depend on Hub Modules.

