# LinSpectacles Module SDK — API v8

> **0.0.7 terminology/packaging:** host-only extensions are called **Hub Modules**, and the Dashboard card is **Hub State**. Existing Module API v1-v6 symbol names such as `add_suite_state_item()` are retained unchanged for source compatibility. Packaged runtimes may discover immutable Package-managed/system modules in addition to the runtime-owned User store.


Hub Modules are optional capabilities of the **LinSpectacles host**. They are deliberately different from applets:

- **Applet**: a standalone inspector; must remain usable outside LinSpectacles and must not import `linspectacles.*`.
- **Hub Module**: an optional host enhancement; it may depend on the documented Hub Module API and never appears in the sidebar.

Examples of appropriate Hub Modules include an Encyclopedia/What's This layer, relationship/correlation tools, Snapshot & Compare, combined diagnostic reports, or privacy/redaction helpers.

## Discovery and activation

Hub Modules are discovered from exactly two sources: the runtime-owned **User** location and the known immutable **Package-managed/system** location. Source Portable reads/writes `<Hub>/modules/`; Source Integrated and Packaged read/write `${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/`. The current managed Fedora provider uses `/usr/libexec/linspectacles/modules/`. No other manual locations are scanned.

If both sources contain the same logical module ID, both physical copies remain visible in **Configuration → Modules**, but enablement belongs to the logical module ID only. The global **User / Package-managed** preference selects which installed implementation runs; versions are never compared and both implementations are never loaded simultaneously. Discovery reads `module.json` only. Python is imported **only for the resolved implementation of an enabled logical module**. Package-managed modules remain package-provider owned and are not deleted by the Hub.

## Required files

```text
<active-module-store>/my_module/
  module.json
  module.py
```

`__init__.py` and local support files are optional. The declared entrypoint is loaded directly, so `__init__.py` does not need to re-export the factory.

## Manifest

```json
{
  "schema": 1,
  "module_api": 8,
  "id": "my-module",
  "name": "My Hub Module",
  "version": "0.0.1",
  "author": "brunonlinespace",
  "editor": "brunonlinespace",
  "entrypoint": "module.py",
  "factory": "create_module",
  "enabled_by_default": false,
  "description": "Optional host capability"
}
```

The current host provides **Module API 8** and remains backward-compatible with earlier Module API modules. Modules that only need earlier services may keep their existing API declaration. Modules that use contextual sidebar actions must declare `"module_api": 8`; Applets-table columns/actions remain API 7 services.

## Factory and lifecycle

The entrypoint must export:

```python
def create_module(context):
    return MyModule(context)
```

The returned object may optionally expose:

```python
def activate(self):
    ...

def deactivate(self):
    ...
```

The host calls `activate()` after construction and `deactivate()` before unloading when present.

## ModuleContext — API v8

The context is intentionally narrow. It does **not** expose the `QMainWindow`, sidebar, or private host widgets.

### Contextual actions — API v8

Hub 0.2.0 has no visible Help or Tools menu. A module that needs a compact action for the currently active applet may contribute it immediately above **Launch Standalone...**:

```python
context.add_contextual_action(
    "whats-this",
    "What's This?",
    self.open_whats_this,
    "Shift+F1",
)
```

Contextual actions are shown only while an applet is active. The Hub owns the button, placement, shortcut registration and cleanup; the module owns only the callback.

`context.add_menu_action("help", ...)` and `context.add_menu_action("tools", ...)` remain compatibility shims for pre-0.2.0 modules but no longer create visible menus. The historical Encyclopedia `What's This?` Help contribution is bridged automatically to the contextual-action surface so existing Encyclopedia releases continue to work. New modules should not use the legacy menu API.

### Dashboard

```python
context.add_dashboard_widget(widget)
```

Dashboard contributions occupy a quiet host-owned area above the built-in coverage/state section. The area disappears when empty. A module should not reproduce sidebar navigation there. Their vertical order follows the persistent **Configuration → Modules → Up / Down** order.

Dashboard presentation is controlled by the host independently of module activation. **Configuration → Modules → Dashboard** can hide a module's Dashboard contributions while leaving the enabled module active. This host visibility gate applies to direct Dashboard widgets, Hub State items, Inspection Coverage columns and legacy Summary annotations. Modules do not need to implement their own duplicate show/hide preference for these host surfaces.


### Configuration and Dashboard host surfaces — API v3/v4

API v3 lets modules integrate into existing Suite surfaces without obtaining private host widgets.

```python
context.add_configuration_page("helpers", "Helpers", self.create_helpers_page)
```

The factory is called when Configuration opens and receives the tab widget as its parent. It must return a `QWidget`. The host owns tab placement and cleanup. Contributed module pages follow **Modules** in module order and precede **Runtime**. A contributed page may optionally expose `can_close_configuration()` returning `True`, `False`, or `(allowed, message)` to block Configuration from closing while an explicit operation is still active. Applet-related enhancements should use the API v7 Applets-table columns/actions below rather than creating a competing Organizer/Applets tab or inventory.

```python
context.open_configuration_page("helpers")
```

Opens Configuration directly on that module-owned page. This is useful for module-owned navigation from Dashboard or another documented host surface.

### Applets-table columns and actions — API v7

API v7 is the preferred integration for applet organizers because it preserves one Hub-owned inventory and selection model. A Module may add compact columns directly to the existing **Configuration → Applets** table:

```python
context.add_applets_column(
    "favourite", "Favourite", self.is_favourite, self.set_favourite,
    kind="check", editable=True,
)
context.add_applets_column(
    "category", "Category", self.category_for, self.set_category,
    kind="text", editable=self.category_editable,
)
```

The value provider receives an applet ID. The change callback receives `(applet_id, value)`. `kind` is `"text"` or `"check"`; `editable` may be a bool or an applet-ID callable. The Hub continues to own the row, selection, search, enablement, source/version/editor fields, ZIP installation, removal and lifecycle.

A Module may also contribute a compact action beside the existing table controls:

```python
context.add_applets_action("manage-categories", "Manage Categories…", self.manage_categories)
```

The callback may accept the Configuration dialog as a parent for a module-owned dialog. It must not reach into private Hub widgets.

### Applets-page extensions — API v6

API v6 adds a narrow extension point for optional Modules that enhance applet organization without taking ownership of the Hub's Applets UI:

```python
context.add_applets_extension("organization", "Organization", self.create_organization_widget)
```

The factory receives the Hub-owned **Configuration → Applets** page as its parent and must return a `QWidget`. The Hub retains applet discovery, search, enablement, ZIP/drag-and-drop installation, removal and runtime/source presentation. The extension is placed inside the existing Applets page and is cleaned up automatically when the Module is disabled.

This is intentionally different from `add_configuration_page()`: an applet organizer should enhance the canonical Applets surface rather than create a second applet-management destination.

```python
context.add_suite_state_item("Privileged helpers", self.summary_text)
```

The provider is called when Dashboard state is refreshed. It returns the compact value appended to the built-in **Hub State** card.

```python
context.add_coverage_annotation(self.coverage_annotation)
```

API v3 compatibility: the provider receives one host-known applet record (`id`, `name`, `version`, `enabled`, `loaded`) and returns short text for a legacy **Inspection Coverage → Summary** cell. The Summary column is shown only while at least one enabled legacy module contributes an annotation.

The Dashboard's host-owned **Enabled Only** and **Loaded Only** controls filter which applet rows are displayed in Inspection Coverage. They do not change applet enabled/load state and do not alter the Hub State totals. When both are selected, only applets satisfying both conditions are shown.

API v5 adds purpose-specific columns:

```python
context.add_coverage_column("Helper", self.helper_state)
```

The provider receives the same host-known applet record and returns the exact cell text for that named column (or an empty value/`None`, rendered as `—`). Columns are ordered by the persistent Module order. This is preferable when the value has its own meaning such as helper state, relationship count or snapshot status. It avoids hiding useful state behind a generic Summary label.

These surfaces are generic. The host does not special-case individual modules or applet capabilities.

### Applet state

```python
states = context.get_applet_states()
```

Each returned record contains:

```text
id, name, version, enabled, loaded
```

This is host-known state only and **does not trigger applet loading or scans**.

Module API v2 additionally provides declarative applet metadata:

```python
records = context.get_applet_metadata()
```

Each record contains ordinary identity/state fields plus:

```text
directory   resolved applet directory
manifest    JSON-compatible contents of applet.json
```

The host reads the manifest only. It does **not** import the applet, instantiate its widget or trigger any applet scan. This capability is intended for Hub Modules that need to understand applet-declared features such as optional helper contracts, export capabilities or future declarative integrations without crawling private host state.

```python
current = context.current_applet_id()
```

Returns the selected applet ID or `None` while Dashboard is selected.

Applet IDs exposed by the host are logical IDs. A manifest declaring the newer `linspectacles-<applet-id>` form is normalized to `<applet-id>`, so modules remain compatible with legacy catalogue/configuration keys. The nested `manifest` field remains the declarative JSON as written by the applet.
The mistaken `linspector-<applet-id>` prefix from 0.0.3-r3 is rejected rather than exposed as a separate logical applet ID.

### Module storage

```python
folder = context.storage_dir
```

Each module gets a namespaced writable directory. **Source — Portable** uses:

```text
config/modules/<module-id>/
```

**Source — Integrated** and **Packaged** runtimes use:

```text
${XDG_CONFIG_HOME:-~/.config}/linspectacles/modules/<module-id>/
```

### Status

```python
context.set_status("Snapshot saved.")
```

### Events

```python
context.subscribe("selection.changed", self.on_selection)
```

API v7 currently emits:

- `selection.changed` — `applet_id`, `label`
- `applet.loaded` — `applet_id`, `name`, `version`
- `applets.changed` — `applets`
- `configuration.changed` — `applets`, `lazy_load`
- `module.activated` — `module_id`, `name`
- `module.deactivated` — `module_id`
- `modules.changed` — `modules`

Exceptions in one event subscriber are isolated so they do not prevent other modules receiving an event.

## Cleanup

Every menu action, Dashboard widget, Configuration page, Applets-table column/action, Applets-page extension, Hub State item, Inspection Coverage annotation/column and event subscription registered through `ModuleContext` is tracked by the host and removed automatically when the module is disabled or removed. `deactivate()` is still useful for module-owned timers, dialogs, files or other resources.

## Configuration and installation

Hub Modules are listed discreetly under **Configuration → Modules**. They never become sidebar items.

Users can:

- enable/disable a module;
- independently show/hide that module's Dashboard contributions;
- add a module ZIP;
- remove a module from the runtime-owned User store (Package-managed modules are removed by their package provider);
- move modules **Up / Down** to persist contribution order;
- refresh discovery;
- open the writable runtime-owned User module store.

A newly user-installed module is always left **disabled**, even if its manifest says `enabled_by_default: true`. This keeps installation and execution as separate trust decisions.

ZIP installation requires one top-level module folder, safe archive paths, a valid `module.json`, a supported API version and the declared entrypoint. Discovery never executes disabled module code.

## Compatibility rule

A new module that uses already-documented API v1–v7 services should require **no LinSpectacles source change**. A host change is appropriate only when a future module genuinely requires a new class of host capability; that capability should then be added generically and the Module API version handled deliberately rather than special-casing a module by name.

## Navigation services — API v5

API v5 adds an optional, host-owned navigation organizer contract. A module may read installed module state with `get_module_states()`, request an applet with `activate_applet(id)`, register one navigation model provider with `set_navigation_provider(provider)`, and call `refresh_navigation()` after its own configuration changes. The host continues to own the sidebar widget, applet lifecycle and activation. Removing/disabling the organizer restores the plain alphabetical sidebar immediately.

The provider returns a JSON-compatible mapping with `items` keyed by applet ID and optional `group_order`. Item metadata may include `group`, `tags`, `favorite`, and integer `order`. Unknown applets are expected to remain reachable (normally under `Unsorted`); organizer metadata is enrichment, never validation.
