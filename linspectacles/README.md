# LinSpectacles Hub — implementation and release notes

<p align="center"><img src="../assets/linspectacles-logo.png" alt="LinSpectacles penguin X-ray roundel" width="180"></p>

> Repository front page: [`../README.md`](../README.md)

**Version 0.2.3** · Organisation ID: **linspectacles** · Publisher/editor: **brunonlinespace** · GPLv3-or-later

**Expose. Explore. Explain.**

Dark-only, read-only Linux inspection utilities with removable standalone applets and an optional Portable/Integrated source Hub runtime.


### 0.2.2 — contextual Hub window titles

- Separates desktop application identity from per-window title content. The Qt application/display identity remains **LinSpectacles Hub**.
- The main Hub window now uses the active context only as its Qt window title: **Dashboard** on Dashboard and the selected applet's own name for an active applet. This prevents desktop environments that append the application name from producing duplicated Hub branding.
- Configuration uses the context-only window title **Configuration** for the same reason.
- Leaves applet discovery, runtime classification, migration, shortcuts, Module API 8, Dashboard data, component management and styling unchanged.


### 0.2.1 — contextual-help label and README publication correction

- Corrects the Hub contextual Encyclopedia action label from **What's This...** to **What's This?**.
- Restores the root README publication policy: its Current release section now contains the actual current release only; the historical release record remains here in the nested README.
- Adds the requested LinSpectacles Hub screenshot block at the end of the root README Interface section.
- Leaves Hub 0.2.0 runtime, discovery, migration, component management, shortcuts, About behavior and Module API 8 behavior otherwise unchanged.

### 0.2.0 — Hub identity and command-surface consolidation

- Identifies the desktop application as **LinSpectacles Hub** for source and packaged launchers.
- Removes the visible Help and Tools menus; `F1` remains Hub Documentation.
- Changes Dashboard to `Ctrl+W`; `F5` launches the active applet standalone.
- Makes Configuration → About the single About surface, including Build, Configuration path and links ordered README → License → Repository → Issues.
- Adds Module API 8 contextual sidebar actions above Launch Standalone; current Encyclopedia What's This? contributions are bridged from the legacy Help API.
- Keeps `Ctrl+,` / `Ctrl+.` applet cycling and `Ctrl+F` search unchanged.

### 0.1.12 — restore original tab-page frame

- Restores the original pre-0.1.9 `QTabWidget::pane` frame exactly: `border: 1px solid #333333;`.
- Leaves individual `QTabBar::tab` styling unchanged from 0.1.11.
- Preserves the Cgroups Inspector 0.0.6 `QTreeWidget` parity rule unchanged.
- No Runtime/Startup, discovery, component-management, table, sorting, navigation or Module API behavior changes are included.

### 0.1.11 — Runtime/Startup configuration consolidation

- Merges the former standalone **Startup** Configuration tab into **Runtime** as a dedicated Startup section.
- Preserves the existing **Lazy-load utilities** control, explanatory text, persistence key and save behavior unchanged.
- Canonical Configuration order is now **Applets → Modules → optional module-owned pages → Runtime → Appearance → About**.
- No runtime migration, discovery, component-management, Module API, applet lifecycle, table behavior or stylesheet changes are included.

### 0.1.10 — tab-frame and tree-style correction

- Corrects the 0.1.9 border interpretation: individual tab-button borders are restored, while the surrounding `QTabWidget::pane` border is removed.
- Adds the Cgroups Inspector 0.0.6 `QTreeWidget` rule exactly to the Hub stylesheet: dark inventory background/foreground, `#252526` alternate background, `1px #333333` border and `4px` radius.
- No Configuration ordering/sorting, runtime, discovery, component-management, Module API or applet lifecycle changes are included.

### 0.1.9 — Configuration table and tab clarity

- Configuration tabs now default to **Applets → Modules → optional module-owned pages → Startup → Runtime → Appearance → About**.
- Individual tab outlines are removed while the existing selected/hover presentation is retained.
- Configuration → Applets starts with **Applet**, followed by Enabled, Source, Owner, Version and Editor; Organizer **Layer** then **Favourite** sit at the far right.
- The former **Ownership** and **Provider / Location** headings are simplified to **Owner** and **Source**.
- Applets and Modules tables support ascending/descending sorting by clicking column headers. Sorting is presentation-only and never rewrites module Dashboard order.
- No runtime migration, component discovery, module enablement, Module API, applet lifecycle or theme-policy changes are included.

### 0.1.8 — module-management and navigation clarity

- Hub Module **Enabled** state is now stored once per logical module ID; the User/Package-managed preference selects which installed implementation runs.
- Configuration → Modules now puts **Hub Module** first and shows physical installed copies separately for provenance and User-copy removal.
- Dashboard Hub Module installed/enabled counts now reflect logical modules rather than duplicate physical copies.
- Normal UI terminology uses **User** and **Package-managed**; provider/location details remain visible where useful.
- Sidebar applet titles are larger and bold by default while retaining a compact secondary version/source line.
- Organizer group headings no longer add extra indentation to applet rows.
- No runtime migration, discovery, Module API, applet-loading or theme behavior changes are included.

### 0.1.7 — component-model consolidation

- Updates Applet Organizer interoperability for source-qualified applet instances while keeping Favourite/Layer organization logical-ID based.
- Inspection Coverage now displays **Source** so Manual and Managed copies are distinguishable in the native Dashboard.
- Configuration → Applets and Modules now show **Management** separately from Source: Manual components are Hub-managed; Managed components remain package-provider owned.
- Installed/enabled/loaded Dashboard counters continue to count physical discovered applet instances; module enabled/installed counters continue to reflect resolved physical module instances.
- Per-instance applet enable/disable and duplicate module mutual exclusion remain unchanged.
- No runtime migration, source-selection, theme, navigation-style, Module API version or applet-loading behavior changes are included.

### 0.1.6 — Source runtime migration

- Source Portable owns internal config/applets/modules; Source Integrated and Packaged own XDG config/manual components.
- Configuration → Runtime can migrate Source Portable ↔ Integrated safely.
- Migration copies config, optionally copies applets/modules, never overwrites component conflicts, keeps the old side, updates source desktop integration, persists the target mode and restarts.
- Packaged runtimes cannot switch mode.

### 0.1.5 — Manual/Managed presentation preference

- Adds a global **Prefer Manual / Prefer Managed** setting under **Configuration → Runtime**.
- Discovery remains instance-complete; Configuration continues to show every discovered Manual and Managed applet/module copy.
- Ordinary applet navigation shows the preferred enabled ownership class when both Manual and Managed copies share a logical ID. If only one enabled copy remains, that copy is shown.
- Duplicate Hub Modules use the preference only when no explicit per-instance enabled choice already exists; explicit module enablement remains authoritative.
- Version strings are informational only and are never compared to choose a component copy.
- No runtime migration/switching, desktop-launcher mutation, discovery-path change, theme work, Organizer redesign or applet/module API change is included.

### 0.1.4 — integrated-source detection correction

- Detects an existing desktop integration that points to this exact source tree, including Suite Pythoine's `X-Suite-Pythoine-PortableMain` metadata.
- An integrated source Hub therefore resolves as **Source — Integrated** and uses XDG Hub configuration/data roots even when no `--suite-pythoine` argument is supplied.
- A source tree with no matching desktop integration remains **Source — Portable** and continues to use its internal Hub state.
- Packaged runtime detection remains unchanged and still takes precedence.
- No Suite Pythoine changes, path-name guessing, migration behavior, component-source policy, navigation, styling, Module API or applet/module lifecycle changes are included.

### 0.1.3 — superseded launch-flag correction

- Attempted to classify Suite Pythoine source launches through the optional `--suite-pythoine` argument.
- Superseded by 0.1.4 because existing Suite Pythoine launch paths do not guarantee that argument.


### 0.1.2 — explicit runtime/path model

- Adds `runtime.py` as the authority for Hub deployment classification: **Source — Portable**, **Source — Integrated**, or **Packaged**.
- `paths.py` now resolves Hub-owned configuration/data roots from that runtime model rather than directly equating packaging with path ownership.
- Source Portable keeps Hub state beneath the source tree; Source Integrated and Packaged use XDG config/data roots.
- Adds the root `linspectacles-runtime.json` source marker and a read-only **Configuration → Runtime** page showing the resolved runtime, config/data paths and desktop-integration expectation.
- Generalizes component ownership internally from RPM-specific origin to **Manual** versus **Managed** while retaining `RPM` as the current managed provider/source label.
- Preserves 0.1.1 component discovery, duplicate presentation, manual-location selection, applet/module lifecycle, Module API, styles and navigation. No runtime migration/switching or launcher mutation is performed.


### 0.1.1 — Hub implementation decomposition

- Refactor-only release: no intentional runtime, UI, discovery, component-management, Module API, applet lifecycle or styling changes.
- Splits the former monolithic `host.py` into focused implementation units for the main window, Configuration, Dashboard, navigation, applet hosting and module hosting.
- Keeps `linspectacles.host` as a compatibility import surface so existing launchers/callers continue to resolve `Linspectacles` and `run` unchanged.
- Method bodies and moved UI-class bodies are mechanically preserved from 0.1.0; the refactor is structural preparation for later runtime/deployment work.


### 0.1.0 — explicit manual/RPM component sources

- Manual component storage is owned by runtime mode: Source Portable uses the Hub tree; Source Integrated and Packaged use XDG user data.
- Discovers exactly that manual source plus the known RPM/system source; no other manual filesystem locations are scanned.
- Preserves Manual and RPM copies with the same logical applet/module ID as separate discovered instances instead of silently shadowing one.
- Applet sidebar rows use a compact two-line identity: applet title plus `version · source`, allowing the user to launch either Manual or RPM copy directly.
- Add/Remove/Open Folder operate only on the runtime-owned Manual source. Managed content remains package-provider owned.
- Manual component location is no longer separately user-selected; changing Source runtime mode is the only supported way to move between internal and XDG manual storage.
- Duplicate Hub Module copies are both listed but may not execute simultaneously; enabling one source explicitly disables the other copy of the same logical module ID.
- No persistent applet/module registry is introduced. Discovery remains manifest-first filesystem scanning of the two authorized sources.


### 0.0.11 — applet table and tab visual parity

- Applies the Kernel Modules authoritative alternating-row colour to Hub-owned `QTableWidget` styling: `alternate-background-color: #252526`.
- Applies the Linux ResMon authoritative full rounded-tab treatment: `border-radius: 4px` on `QTabBar::tab`.
- Preserves all 0.0.10 Hub behavior, including the Dashboard text-entry focus correction, Module API 7 and component discovery.

### 0.0.10 — Dashboard text-entry focus correction

- Fixes the Hub-owned Dashboard type-to-search path so it does not steal printable keystrokes from focused text-entry controls contributed by Hub Modules.
- In particular, the Encyclopedia Dashboard search field now retains focus and receives typed text instead of redirecting the first character to the sidebar **Search applets...** field.
- Keeps Hub applet search, `Ctrl+F`, sidebar navigation, Module API 7 and module/applet behavior otherwise unchanged.

### 0.0.9 — single-table Organizer integration and portable shared discovery

- Replaces the 0.0.8/Organizer 0.0.3 stacked Applets-page Organization grid with **Module API 7** table contributions. Applet Organizer 0.0.4 contributes only **Favourite** and **Category** columns plus **Manage Categories…** to the Hub's one canonical Applets table.
- Keeps API 6 Applets-page widget extensions available for compatibility, but the official Organizer no longer uses them.
- Portable mode now discovers components in three ordered tiers: **Portable → User/XDG → System (RPM)** for both applets and Hub Modules.
- The Portable store remains the only writable install/remove target and portable configuration remains under the portable root; shared User/XDG and System (RPM) fallbacks are read-only from that session.
- RPM mode remains **User/XDG → System (RPM)** with user writes and package-manager-owned system components.
- Component source labels and duplicate-ID precedence are preserved explicitly across both applets and Modules.

### 0.0.8 — Hub-owned applet navigation and Module API 6

- Makes the sidebar **Search applets...** field permanent Hub UI rather than an Applet Organizer-owned surface.
- Adds **Ctrl+F** to focus/select applet search and conservative type-to-search from Dashboard/sidebar navigation contexts without stealing ordinary inspector keystrokes.
- Adds Hub-owned search to **Configuration → Applets**.
- Adds drag-and-drop applet ZIP installation to the Applets page using the same trust prompt and writable user/portable destination as **Add Applet...**.
- Replaces the generic **Open Applets Folder** action with selection-aware **Open Portable Folder** / **Open User Folder** actions shown only for writable applet copies; RPM-owned applets never expose an action into `/usr/libexec`.
- Introduces **Module API 6** `add_applets_extension()` so optional Modules can enhance the existing Applets page without creating a competing Configuration tab. APIs 1–5 remain supported.
- Applet Organizer 0.0.3 is the first API 6 consumer: its favourites/category controls move into Configuration → Applets and its standalone Dashboard card becomes a compact **Hub State** contribution.
- 0.0.8 itself did not change component discovery precedence; 0.0.9 supersedes that limitation for Portable discovery.

### 0.0.7-r1 — official Hub Module catalogue correction

Adds **Boot Environment** and **System Identity** to the built-in permissive offline Hub Module catalogue. They were already valid/discoverable installed Modules, but were missing from the known-module catalogue. No component discovery, runtime precedence, module API, applet, or packaging behaviour changes.

### 0.0.7 — packaged component discovery

- RPM-installed Hub sessions now discover applets from both the writable user store `${XDG_DATA_HOME:-~/.local/share}/linspectacles/applets/` and the immutable system store `/usr/libexec/linspectacles/applets/`.
- Hub Modules are discovered from the corresponding user and system stores: `${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/` and `/usr/libexec/linspectacles/modules/`.
- A valid user/portable component takes precedence over a system-installed component with the same logical ID. This preserves the existing portable/testing workflow while allowing official applets and modules to be packaged independently through RPM/COPR.
- Configuration now identifies each installed component as **User**, **Portable**, or **System (RPM)**. System-installed applets/modules can be enabled, disabled and used normally but cannot be deleted by LinSpectacles; removal belongs to DNF.
- Adding an applet or module writes only to the active runtime store: XDG User in RPM mode, Portable beside the Hub in Portable mode. From 0.0.9, Portable discovery also reads lower-priority XDG User and System (RPM) fallbacks without writing to them.
- The Hub RPM reserves `/usr/libexec/linspectacles/applets/` and `/usr/libexec/linspectacles/modules/` as immutable component locations but still ships no applet/module payload itself.
- No applet is made dependent on the Hub, and existing Module API v1-v5 compatibility names remain unchanged.

### 0.0.6-r1 — Hub package cleanup

- Removes the temporary RPM `Obsoletes` rules for `linspectacles` and `linspectacles-suite`. The Hub package now owns only the **`linspectacles-hub`** package identity, allowing the bare `linspectacles` name to become the standard-install meta-package later without collision.
- The Configuration About page and Help → About dialog now identify the running host precisely as **LinSpectacles Hub**, with **Linux Inspection Suite** retained as the descriptor.
- The ordinary desktop/window presentation remains **LinSpectacles**, the executable remains **`linspectacles`**, and runtime/XDG paths are unchanged.
- Suite Pythoine integration remains on the existing `linspectacles` component ID and `suite-pythoine-extension.json` contract.

### 0.0.6 — LinSpectacles Hub identity

- Keeps the visible application identity **LinSpectacles — Linux Inspection Suite**, the tagline **Expose. Explore. Explain.**, application ID `linspectacles`, desktop identity and `/usr/bin/linspectacles` command unchanged.
- Adopts **Hub** for the host application's technical/distribution identity: Fedora/COPR package **`linspectacles-hub`** and repository **`https://github.com/linspectacles/linspectacles-hub`**.
- This original 0.0.6 build temporarily obsoleted the prior experimental package names, `linspectacles` and `linspectacles-suite`, so DNF/COPR could complete the one-time Hub rename. That temporary migration rule is removed in 0.0.6-r1 before the finalized package taxonomy is introduced.
- Keeps the immutable RPM payload under `/usr/libexec/linspectacles`, user-owned XDG configuration/applet/module stores, and all normal runtime privilege behaviour unchanged.
- Direct host wording is updated from Suite to Hub where it identifies the host application. **Linux Inspection Suite** remains the product descriptor. Host-only **Suite Modules** and **Suite State** are renamed **Hub Modules** and **Hub State** in the current UI/documentation; compatibility API symbol names are retained.
- `suite-pythoine-extension.json` and the `--suite-pythoine` launch flag are intentionally retained: **Suite Pythoine** is the external product name. Its LinSpectacles component ID remains `linspectacles`, so this rename does not require a Pythoine recognition change.


### 0.0.5-exp1-r4 — RPM package rename

- Renames the Fedora/COPR RPM package from **`linspectacles`** to **`linspectacles-suite`**.
- Adds RPM **Provides/Obsoletes** compatibility for the former `linspectacles` package so DNF can replace an installed exp1-r3 package during repository upgrade.
- Keeps the application command `/usr/bin/linspectacles`, desktop identity, runtime paths, XDG configuration, applet/module stores, and application behavior unchanged.

### 0.0.5-exp1-r3 — RPM package/software-center metadata refinement

- RPM metadata declares **Vendor: LinSpectacles** and **Packager: brunonlinespace** for package frontends.
- AppStream metadata includes the System category, search keywords, VCS URL, provided `linspectacles` binary, and an explicit development-release description for richer repository/software-center presentation.
- No screenshot URLs are invented; screenshots remain absent until stable hosted assets are supplied.
- Runtime architecture is unchanged from `0.0.5-exp1-r2`.

### 0.0.5-exp1-r2 — RPM metadata validation hotfix

- AppStream developer ID is now the valid reverse-DNS `io.github.linspectacles`.
- Desktop entry uses the single primary `System` category, removing the duplicate-main-category validator hint.
- Runtime architecture is unchanged from exp1-r1.

### 0.0.5-exp1-r1 — RPM build-path hotfix

- Fixes the RPM `%install` stage when the project/build source path contains spaces.
- Quotes all `%{buildroot}` install/validation paths in the spec.
- Uses a user-owned cache RPM topdir by default instead of nesting `.rpmbuild` under the source tree, avoiding path-tokenization problems from project folder names.
- No runtime architecture or UI behavior changes from `0.0.5-exp1`.

### 0.0.5-exp1 — RPM Experiment 1

- Adds an explicit runtime-path layer while preserving the existing portable layout. Portable launches still use root-level `config/`, `applets/` and `modules/`.
- An RPM launcher sets `LINSPECTACLES_INSTALL_MODE=rpm`; in that mode all mutable Suite state is user-owned: configuration under `${XDG_CONFIG_HOME:-~/.config}/linspectacles/` and portable applets/modules under `${XDG_DATA_HOME:-~/.local/share}/linspectacles/`.
- The RPM payload contains the Hub application only. It does **not** install applets or modules into `/usr/share/linspectacles/`, and normal Add/Remove/Refresh/Launch operations require no root privileges.
- Adds an experimental Fedora RPM build kit under `packaging/rpm/`. The RPM installs immutable Suite code under `/usr/libexec/linspectacles`, a launcher under `/usr/bin`, and standard desktop/icon/AppStream integration files.
- RPM package installation/upgrades remain package-manager operations; once installed, normal LinSpectacles operation and portable component management are entirely user-space.
- No applet API, Module API, navigation, Dashboard, inspection or applet-ID behavior is intentionally changed from `0.0.4-r1`.

### 0.0.4-r1

- Fixes **Configuration → Modules** column sizing to match the full-width behavior already established for **Configuration → Applets**. The **Suite Module** column stretches to consume the available width while Installed/Enabled/Dashboard/Version/Editor remain content-sized.
- The sizing policy is reapplied after module discovery/Refresh so the table does not collapse short of the panel width after Refresh, Add or Remove operations.
- No module catalogue, ordering, enablement, Dashboard visibility, applet, navigation, or inspection behavior is otherwise changed.

### 0.0.4

- Adds a Hub-owned **Launch Standalone...** button directly above **Configuration...** whenever an applet is the active view; Dashboard and non-applet Suite surfaces keep it hidden. The same action is available from the applet sidebar context menu. It starts the applet's declared `standalone.py` as a separate process/window and does not detach or move the embedded instance.
- **Configuration** places the Applet Organizer's contributed page before **Applets** when that module is enabled. The base sequence is therefore **Organizer → Applets → Appearance → Startup**, followed by other contributed module pages, **Modules**, and **About**.
- Fixes **Configuration → Applets** column sizing after Refresh, Add or Remove: the Applet column remains stretched to consume the available width while Enabled/Version/Editor retain content-sized columns.
- Dashboard **Inspection Coverage** adds **Enabled Only** and **Loaded Only** checkboxes, in that order. With both selected the filters combine using AND semantics; Suite State counts remain unfiltered.
- Applet manifest identity rules remain unchanged from r4: current `linspectacles-<applet-id>` and legacy `<applet-id>` forms are accepted; mistaken `linspector-<applet-id>` is rejected.

### 0.0.3-r4

- Corrects the prefixed applet manifest identity introduced in r3: the supported current form is **`linspectacles-<applet-id>`**, not `linspector-<applet-id>`.
- Legacy unprefixed **`<applet-id>`** manifests remain supported and normalize to the same logical applet identity as the corresponding `linspectacles-<applet-id>` form.
- The mistaken **`linspector-<applet-id>`** form is explicitly rejected so it cannot silently fall through as a legacy ID.
- No other Suite, applet, module, navigation, Dashboard, Configuration or inspection behaviour is changed.

### 0.0.3-r3

- Superseded r3 behaviour: this revision mistakenly introduced **`linspector-<applet-id>`** as the prefixed identity form; r4 corrects it to **`linspectacles-<applet-id>`**.
- r3 normalized that mistaken form with legacy IDs; r4 preserves normalization only for the corrected `linspectacles-` form and legacy unprefixed IDs.
- No applet payload, module behavior, navigation layout, Dashboard behavior or inspection logic is otherwise changed.

### 0.0.3-r2

- Corrects the then-current host repository under the LinSpectacles GitHub organisation while retaining the organisation URL **`https://github.com/linspectacles/`**.
- Keeps author/editor/publisher metadata in the component descriptor but removes those fields from the visible About presentations.
- Dashboard **Inspection Coverage** columns now stretch to occupy the available table width.
- No applet, module, navigation, inspection, or other Dashboard behaviour is changed.

### 0.0.3-r1

- Refreshes the displayed product-brand capitalization to **LinSpectacles** throughout the host and current documentation while retaining the internal `linspectacles` organization/package identity.
- Adds **About** as the final **Configuration** tab, using the same About-page layout convention as the current Scheduler and Interrupts inspectors.
- Confirms metadata: author/editor/publisher **brunonlinespace**, organisation ID **`linspectacles`**, and organisation URL **`https://github.com/linspectacles/`**.
- No inspection, applet, module, navigation, or Dashboard behaviour is otherwise changed.

### 0.0.3

- Rebrands the program as **LinSpectacles** with the product line **Linux Inspection Suite** across the titlebar, Dashboard, About dialog, host identity and current documentation.
- Adopts organisation ID **`linspectacles`** and GitHub organisation **`https://github.com/linspectacles`** while retaining **brunonlinespace** as publisher/editor.
- Renames the portable host package/configuration/assets to the LinSpectacles identity and uses the supplied LinSpectacles icon/logo assets.
- Retains the **Expose. Explore. Explain.** tagline and the existing 0.0.2 host behaviour otherwise.

### 0.0.2

- Previous identity release updating the program/product labels across the Dashboard, titlebar, About dialog and documentation.
- Replaces the former taglines with **Expose. Explore. Explain.**
- Previous identity metadata update; **brunonlinespace** remains publisher/editor.
- Fixes About-dialog spacing and margins so long identity/configuration text does not overlap surrounding content.
- Dashboard **Inspection Coverage** and **Configuration → Applets** now list applets alphabetically by displayed applet name (A→Z), without changing sidebar/navigation organisation.

### 0.0.1-exp9-r6-r2

- Corrects the first Organizer integration performance path: sidebar search/navigation refresh no longer rediscover applet folders or rebuild Dashboard state on every keystroke, and sidebar rebuilds no longer emit `applets.changed` feedback into the Organizer.
- Dashboard is now a fixed top sidebar button. Organizer search is always below Dashboard and cannot displace it.
- Organizer category headings are normal case, bold, and use the Suite blue instead of all-caps headings.
- Configuration → Modules removes module categories and the numeric Dashboard Order column. Installed module row position itself is the Dashboard/module order; Up/Down visibly moves the selected reorderable row. Catalogue-only rows remain informational below installed rows.
- **Privileged Helpers** is the only currently fixed/non-reorderable module. **System Pulse** is reorderable again.
- Modules remains the final management/module Configuration tab before About and the offline module catalogue remains permissive with Uncatalogued fallback for unknown installed modules.

### 0.0.1-exp9-r6-r1

- r1 hotfix: initialize Module API v5 navigation-provider state before the first sidebar rebuild, fixing the r6 startup AttributeError.

- Core applet sidebar is alphabetical and no longer exposes applet Up/Down ordering.
- Previous/next applet shortcuts are now `Ctrl+,` / `Ctrl+.`; `F5` returns to Dashboard.
- Suite Module API v5 adds the optional host-owned navigation organizer contract, module-state inspection and applet activation service.
- Configuration keeps **Modules** after module-contributed pages and before **About**, and Modules is now a permissive offline catalogue/manager showing known installed and uninstalled modules plus unknown installed modules as **Uncatalogued**.
- Dashboard ordering controls are disabled for fixed/non-reorderable module contributions.
- No module catalogue function performs network, store, download or automatic installation activity.

### 0.0.1-exp9-r5

- Removes the old host-hardcoded **System Identity** Dashboard card. System identity is now expected to be supplied by its independent Suite Module when installed/enabled, so the shell no longer duplicates that capability.
- Makes the built-in **Dashboard vertically scrollable**, allowing module-contributed cards and the built-in coverage/state area to extend naturally beyond the current viewport.
- **Configuration → Modules** now separates **Enabled** from **Dashboard**. Enabled controls whether module Python is activated; Dashboard independently shows/hides that module's Dashboard contributions without disabling its menus, configuration pages, events or other host features. Existing installations migrate with Dashboard visibility shown by default.
- Dashboard visibility applies generically to module cards, Suite State lines, Inspection Coverage columns and legacy Summary annotations.
- Adds Hub-level applet cycling in visible sidebar order: **Ctrl+Shift+,** selects the previous applet and **Ctrl+Shift+.** selects the next applet. Cycling wraps and deliberately skips Dashboard; from Dashboard the shortcuts enter the last/first applet respectively.
- Suite Module API remains **v4**; existing modules require no source changes. Applets and Suite Module payloads remain independently released and are not reissued by this shell-only revision.

### 0.0.1-exp9-r4

- Adds **Suite Module API v4** while preserving API v1/v2/v3 compatibility. API v4 adds generic named **Inspection Coverage columns** so a module can expose meaningful per-applet state under its own column heading instead of reducing it to a generic Summary annotation.
- API v3 Summary annotations remain supported for older modules, but the host no longer displays a Summary column unless an enabled legacy module actually contributes one.
- This Suite source ZIP is now deliberately **shell-only**. Applets and Suite Modules have independent release cadences and are installed separately into the active applet/module stores. Portable mode uses root-level `applets/` and `modules/`; RPM mode uses the user-owned XDG data tree. Empty stores are created automatically on first run.
- No applet or Suite Module implementation is bundled or reissued by this Suite-only revision.

### 0.0.1-exp9-r3

- Adds **Suite Module API v3** while preserving API v1/v2 compatibility. API v3 adds generic Configuration-tab, Suite State-line and Inspection Coverage-summary contribution points, plus navigation to a contributed Configuration page.
- **Configuration → Modules** now has **Up / Down** controls. The saved module order is authoritative for module-contributed Dashboard sections and contributed Configuration pages.
- Inspection Coverage gains a generic **Summary** column for compact module-provided applet annotations.
- Bundled **Privileged Helpers 0.0.2** removes its standalone Dashboard card. Its helper count/status is appended to **Suite State**, applicable applets receive **Helper** in Inspection Coverage → Summary, and central management now lives in **Configuration → Helpers**.
- The Helpers page intentionally stays compact: helper inventory plus Refresh, Details, Install/Update/Reinstall and Remove actions. Publisher/path/ownership/mode/SHA-256 facts and the Standard access vs With helper comparison live behind **Details...**.
- **Tools → Privileged Helpers...** remains as a shortcut and now opens Configuration directly on the Helpers tab.
- Existing inspector applet implementations are unchanged from exp9-r2; no standalone applet packages are reissued for this Suite/module UI revision.

### 0.0.1-exp9-r2

- Adds **Suite Module API v2** while keeping API v1 modules compatible. API v2 adds `context.get_applet_metadata()`, a manifest-only capability that lets enabled Suite Modules inspect declarative applet capabilities without importing applet code or triggering applet scans.
- Bundles **Privileged Helpers 0.0.1** as an optional, disabled-by-default Suite Module. It consumes Privileged Helper Contract v1 declarations generically rather than hard-coding individual applets.
- Privileged Helpers provides central helper inventory, installed/update-repair state, ownership/mode/hash facts, and the applet-declared **Standard access vs With helper** comparison.
- Helper install/update/repair/remove is explicit and PolicyKit-mediated. Installing a helper never activates privilege; elevated sessions remain controlled by the applet's own dedicated Privileged Inspection window.
- Central helper installation is restricted to read-only, window-ephemeral contracts with a SHA-256-verified packaged payload and direct `/usr/libexec/linspectacles-*` target. The hash is presented as package consistency, not as third-party publisher authentication.
- All bundled inspector applet implementations are preserved byte-for-byte from exp9-r1. Current independently issued applet packages, such as SELinux Inspector 0.0.4-r4, can be installed into the applet store normally.

### 0.0.1-exp9-r1

- Configuration now gives **Suite Modules** their own dedicated final tab, ordered **Applets → Appearance → Startup → Modules**, keeping applet management and Suite-extension management visually distinct. Module behaviour and API v1 are otherwise unchanged.

### 0.0.1-exp9

- Adds **Suite Module API v1** as a generic, versioned host-extension layer separate from standalone inspector applets.
- Suite Modules are discovered manifest-first from the active module store (root-level `modules/` in portable mode; `${XDG_DATA_HOME:-~/.local/share}/linspectacles/modules/` in RPM mode). Disabled modules are not imported and modules never appear in the sidebar.
- **Configuration → Modules** provides enable/disable, Add Module, Remove, Refresh and Open Modules Folder controls. User-installed modules remain disabled until explicitly enabled.
- API v1 provides generic Help/Tools menu contributions, quiet Dashboard widget contributions, applet state/current-selection access, portable namespaced module storage, status reporting and a small event bus. Module contributions are automatically cleaned up when disabled/removed.
- The **Tools** menu remains hidden unless an enabled module contributes to it; the Dashboard module area remains hidden when empty.
- No Suite Module is bundled yet: this revision establishes the framework before Encyclopedia or other modules are introduced.
- All eight bundled inspector applet implementations are preserved byte-for-byte from 0.0.1-exp8. No separate applet packages are reissued with this Suite-only revision.

### 0.0.1-exp8

- Rebuilds the built-in Dashboard as an inspection overview rather than an app launcher: branded header, host-level system identity, non-invasive applet coverage table, and Suite/session state.
- Dashboard does **not** import/open applets or trigger any applet scan. Enabled/disabled and loaded/not-loaded states come only from the host registry/session.
- Configuration tab order in exp8 was **Applets → Appearance → Startup**; exp9-r1 adds **Modules** as the final dedicated tab.
- All eight bundled applet implementations are preserved unchanged from 0.0.1-exp7-r1.

### 0.0.1-exp7-r1

- Hotfix: SELinux Inspector now correctly re-exports its `create_applet` factory from the package root so the LinSpectacles applet loader can instantiate it. No SELinux inspection behavior changed.

### 0.0.1-exp7

- Resource Monitor is intentionally **decoupled from LinSpectacles** while ResMon GUI/TUI development continues independently; the LinSpectacles package no longer includes a Resource Monitor applet or `psutil` dependency.
- Adds **SELinux Inspector 0.0.1** as a removable standalone applet with Status, Booleans, Process Contexts, Recent Denials and File Context Check views.
- Recent SELinux AVC/USER_AVC denials are **not scanned automatically**. Users can scan normally, or explicitly choose **Scan with Privileged Access...** when audit permissions require it. The privileged path runs only `ausearch` through `pkexec`; the LinSpectacles GUI itself remains unprivileged and no SELinux policy/settings are changed.
- File Context Check compares the current label with the policy expectation using read-only tools and never runs `chcon` or `restorecon`.
- SELinux Inspector participates in the existing metadata-font preference, right-click column visibility and Plain Text-first export system.

### 0.0.1-exp6

- **Configuration → Appearance** now lets the user choose the actual installed font and size used by metadata/details panes with Qt's native font chooser; the selection is persisted portably and applied to loaded applets. The applet text panes also apply a local font QSS override so the suite's global UI stylesheet cannot force the proportional interface font back onto metadata.
- Every inspector applet except the then-bundled Resource Monitor now has **Export...** as the far-right top action. Export uses already-collected data only, defaults to **Plain Text**, and also offers CSV, JSON and Markdown. Boot Inspector exports its cached boot summary and critical chain; Environment Variables redacts likely secret/token/password values in exports. Scan-only applets keep Export disabled until a successful scan.
- Right-click the left-table column header in inspector applets to tick/untick visible columns. At least one column must remain visible, and choices are stored per applet in the active user configuration.
- Resource Monitor kept its existing sampler/logic in exp6 and received the standard applet framing; it is decoupled from LinSpectacles as of exp7.
- TUI work remains intentionally deferred; no curses/TUI runtime is added in this revision.

### 0.0.1-exp5-r1

- Metadata/details text panes now default to Qt generic `Monospace` at 10 pt with `QFont.StyleHint.Monospace`, matching the reference PyQt inspector.

UI/metadata refinement: Help now follows the Pad-family sequence (Documentation, repository, issue reporting, About); host titlebar naming no longer duplicates the application display name; applet management is folded into **Configuration...** on an **Applets** tab; inspector metadata panes use the platform fixed-width system font; and AppImage discovery now correctly parses common versioned filenames and reads ELF architecture metadata.

### 0.0.1-exp4

Architecture revision: Resource Monitor returns to modular applet status and can be enabled, disabled, removed or run standalone like every other utility. The host now opens on a non-duplicative Dashboard that reports applet/lazy-loading status but does not repeat sidebar navigation controls. Boot Inspector no longer probes systemd on construction; boot analysis runs only after the user presses **Scan Boot**. Resource Monitor's live sampler activates only while its applet is selected.

### 0.0.1-exp3-r1

Hotfix: restores the missing `Qt` and `QTableWidgetItem` imports in the modular Installed Software applet.

## Run

```bash
python3 main.py
```

The host requires Python 3 and PyQt6. Applets own their additional requirements and may use ordinary Linux tools such as `systemd-analyze`, `systemctl`, `journalctl`, `modinfo`, RPM/dpkg/pacman, Flatpak or Snap when available. SELinux Inspector uses standard SELinux/audit tools when installed (`sestatus`, `getenforce`, `getsebool`, optional `semanage`, `ausearch`, `matchpathcon`) and can optionally invoke only `ausearch` via `pkexec` after explicit user approval. Removing an applet also removes that applet's runtime requirement from normal host use.

## Runtime/path layout

- `main.py` — stable host entrypoint.
- `linspectacles-runtime.json` — source-runtime marker; the shipped source ZIP declares **auto**; direct source use resolves Portable while existing desktop integration resolves Integrated unless the user has explicitly selected a mode.
- `linspectacles/runtime.py` — runtime classification authority.
- `linspectacles/paths.py` — resolves Hub-owned config/data roots from the runtime classification.
- **Source — Portable** uses `<Hub>/config/` for Hub preferences and namespaced module state.
- **Source — Integrated** uses `${XDG_CONFIG_HOME:-~/.config}/linspectacles/` for Hub preferences/state and XDG data roots.
- **Packaged** is always integrated and uses the same XDG mutable state while package-owned code/components remain immutable.
- 0.1.6 supersedes the temporary Shared / Portable / Custom manual-location selector: runtime mode now owns the User component location.
- `suite-pythoine-extension.json` — extension identity/launch descriptor.

There is no AppImage builder or Windows installer. The Hub itself never runs as root; the optional Privileged Helpers module can perform explicit PolicyKit-mediated install/update/remove operations for narrowly declared read-only applet helpers.

## Dashboard

Dashboard is the only built-in content page. The host itself shows LinSpectacles branding, installed/enabled applet coverage, loaded/not-loaded session state and lazy-loading/module status. Linux **System Identity is no longer hardcoded into the Hub**; when desired, that information is provided by the independent System Identity Hub Module.

The Dashboard is vertically scrollable and deliberately contains no utility-launch buttons or applet scan triggers. Enabled Hub Modules may contribute Dashboard content, but **Configuration → Modules → Dashboard** can hide those contributions without disabling the module itself. Applet navigation belongs to the sidebar; **Ctrl+,** / **Ctrl+.** cycle previous/next enabled applets in the current sidebar order.

## Suite Pythoine

LinSpectacles remains independently runnable. `main.py --suite-pythoine` launches the same application without changing its behavior, and `main.py --component-info` prints the bundled extension descriptor as JSON. The descriptor identifies LinSpectacles as a non-routing **Extension** with `main.py` as its portable entrypoint. Suite Pythoine catalogue registration can use this metadata when desired.

GitHub: `https://github.com/linspectacles/linspectacles-hub`

## Applets

Use **Configuration... → Applets** to enable/disable, add, refresh or inspect discovered applet copies. Discovery reads exactly the runtime-owned User applet store plus the known Package-managed/system applet store. User and Package-managed copies with the same logical ID remain separate Configuration rows; ordinary sidebar navigation resolves the enabled copy through the global User/Package-managed preference. Add/Remove/Open User Applets Folder apply only to the runtime-owned User store; Package-managed copies remain package-provider owned. Installed applets remain independently launchable through their own `standalone.py` and do not import `linspectacles.*`. This Hub source ZIP does not carry applet payloads.

Applet scan behaviour is owned by each independently released applet. The Hub host does not trigger an applet inspection merely to populate Dashboard coverage information.

See `APPLET-SDK.md` for the applet contract and `MODULE-SDK.md` for the current Hub Module API contract and compatibility notes.

## Hub Modules

Hub Modules enhance the LinSpectacles workbench rather than inspect a Linux subsystem. They are managed under the dedicated **Configuration... → Modules** tab and never appear in the sidebar. Discovery reads `module.json` only; disabled modules are not imported. The **Enabled** checkbox controls module activation, while the independent **Dashboard** checkbox controls whether that enabled module's Dashboard contributions are presented. Enabled modules may still contribute contextual actions, configuration pages and other documented host services while hidden from the Dashboard, and may observe host-known applet state without triggering scans.

Hub Modules are released independently from the Hub application. Discovery reads exactly the runtime-owned User module store plus the known Package-managed/system module store. Enablement is stored once per logical module ID; when both User and Package-managed implementations exist, the global source preference chooses the runtime implementation and versions are never compared. Physical copies remain visible in the Installed Copies area for provenance and User-copy removal. **Configuration → Modules → Add Module...** installs only to the runtime-owned User store, and Remove never deletes a Package-managed module. The Hub source ZIP does not bundle module payloads merely because the host API changed.

## Branding

The approved LinSpectacles mark is the half-normal, half-X-ray penguin roundel in `assets/`. The host uses it as the application icon and in the single **Configuration → About** presentation. Official standalone applets carry a local branded icon while remaining independent of the host.
