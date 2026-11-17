Name:           linspectacles-hub
Version:        0.2.3
Release:        1%{?dist}
Summary:        Linux Inspection Suite
License:        GPL-3.0-or-later
URL:            https://github.com/linspectacles/linspectacles-hub
Vendor:         LinSpectacles
Packager:       brunonlinespace
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
Requires:       python3
Requires:       python3-pyqt6

%description
LinSpectacles is a modular, read-only Linux Inspection Suite. This RPM packages
the LinSpectacles Hub application only. Configuration and module storage
remain user-owned. Applets and Hub Modules may be installed either in user-owned
XDG stores or as immutable system components managed by RPM/DNF.

%prep
%autosetup

%build
# Pure Python shell; no compilation step is required.

%install
rm -rf "%{buildroot}"
install -d "%{buildroot}%{_libexecdir}/linspectacles"
install -d "%{buildroot}%{_libexecdir}/linspectacles/applets"
install -d "%{buildroot}%{_libexecdir}/linspectacles/modules"
install -m 0755 main.py "%{buildroot}%{_libexecdir}/linspectacles/main.py"
install -m 0644 suite-pythoine-extension.json "%{buildroot}%{_libexecdir}/linspectacles/"
install -m 0644 README.md APPLET-SDK.md MODULE-SDK.md LICENSE "%{buildroot}%{_libexecdir}/linspectacles/"
cp -a linspectacles "%{buildroot}%{_libexecdir}/linspectacles/"
cp -a assets "%{buildroot}%{_libexecdir}/linspectacles/"
find "%{buildroot}%{_libexecdir}/linspectacles" -type d -name __pycache__ -prune -exec rm -rf {} +
find "%{buildroot}%{_libexecdir}/linspectacles" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

install -d "%{buildroot}%{_bindir}"
sed 's|@LIBEXECDIR@|%{_libexecdir}|g' packaging/rpm/linspectacles-launcher > "%{buildroot}%{_bindir}/linspectacles"
chmod 0755 "%{buildroot}%{_bindir}/linspectacles"

install -Dm0644 packaging/rpm/linspectacles-hub.desktop \
  "%{buildroot}%{_datadir}/applications/linspectacles-hub.desktop"
install -Dm0644 assets/linspectacles-icon.png \
  "%{buildroot}%{_datadir}/icons/hicolor/512x512/apps/linspectacles.png"
install -Dm0644 packaging/rpm/io.github.linspectacles.LinSpectacles.metainfo.xml \
  "%{buildroot}%{_metainfodir}/io.github.linspectacles.LinSpectacles.metainfo.xml"

desktop-file-validate "%{buildroot}%{_datadir}/applications/linspectacles-hub.desktop"
appstreamcli validate --no-net "%{buildroot}%{_metainfodir}/io.github.linspectacles.LinSpectacles.metainfo.xml"

%files
%license %{_libexecdir}/linspectacles/LICENSE
%doc %{_libexecdir}/linspectacles/README.md
%doc %{_libexecdir}/linspectacles/APPLET-SDK.md
%doc %{_libexecdir}/linspectacles/MODULE-SDK.md
%{_bindir}/linspectacles
%{_libexecdir}/linspectacles/main.py
%{_libexecdir}/linspectacles/suite-pythoine-extension.json
%{_libexecdir}/linspectacles/linspectacles/
%{_libexecdir}/linspectacles/assets/
%dir %{_libexecdir}/linspectacles/applets
%dir %{_libexecdir}/linspectacles/modules
%{_datadir}/applications/linspectacles-hub.desktop
%{_datadir}/icons/hicolor/512x512/apps/linspectacles.png
%{_metainfodir}/io.github.linspectacles.LinSpectacles.metainfo.xml

%changelog
* Tue Nov 17 2026 brunonlinespace - 0.2.3-1
- Scope the Hub stylesheet to the Hub window, leaving native file and folder choosers unstyled.
- Use unparented native choosers for Add Applet, Add Module and User Component Location.
- Replace the root README with the supplied version and update release metadata.

* Sun Nov 15 2026 brunonlinespace - 0.2.2-1
- Separate contextual Hub window titles from the LinSpectacles Hub desktop identity.
- Show Dashboard or the active applet name without duplicating the application name in KDE titlebars.
- Use Configuration as the context-only Configuration dialog title.

* Sun Nov 15 2026 brunonlinespace - 0.2.1-1
- Correct the contextual Encyclopedia action label to What's This?.
- Restore root README current-release-only policy and add the requested Hub screenshot.
- Preserve Hub 0.2.0 runtime and command behavior otherwise unchanged.

* Sun Nov 15 2026 brunonlinespace - 0.2.0-1
- Consolidate Hub desktop identity, shortcuts, About and contextual help surfaces.
- Remove visible Help/Tools menus; keep F1 documentation and add Module API 8 contextual actions.
- Map Ctrl+W to Dashboard and F5 to Launch Standalone for the active applet.

* Tue Nov 10 2026 brunonlinespace - 0.1.12-1
- Restore the original pre-0.1.9 Configuration tab-page border.
- Leave individual tab buttons and the Cgroups tree-style parity rule unchanged.
- Leave Runtime/Startup, discovery, component management and table behavior unchanged.

* Tue Nov 10 2026 brunonlinespace - 0.1.11-1
- Merge the standalone Startup Configuration tab into Runtime as a Startup section.
- Preserve Lazy-load utilities behavior and persistence unchanged.
- Leave runtime migration, discovery, component management and styling unchanged.

* Tue Nov 10 2026 brunonlinespace - 0.1.10-1
- Restore the individual tab-button borders removed in 0.1.9 and remove the surrounding tab-page frame instead.
- Add the Cgroups Inspector 0.0.6 QTreeWidget frame/background parity rule to the Hub stylesheet.
- Leave runtime, discovery, component management and Configuration table behavior unchanged.

* Tue Nov 10 2026 brunonlinespace - 0.1.9-1
- Reorder Configuration tabs and remove individual tab outlines.
- Put Applet first, simplify Source/Owner headings, and place Layer/Favourite last.
- Add view-only click-to-sort behavior to Applets and Modules tables.

* Tue Nov 10 2026 brunonlinespace - 0.1.8-1
- Make Hub Module enablement logical-ID based; User/Package-managed preference selects the runtime implementation.
- Put Module first in Configuration and show physical installed copies separately for provenance/removal.
- Improve sidebar title readability and remove Organizer-induced applet indentation.
- Adopt User / Package-managed terminology in normal component-management UI.

* Mon Nov 09 2026 brunonlinespace - 0.1.7-1
- Consolidate instance-aware Manual/Managed component presentation and management provenance.
- Add Source to Dashboard Inspection Coverage and Management ownership to Configuration tables.
- Preserve runtime/source-selection, Module API and applet loading behavior.

* Mon Nov 09 2026 brunonlinespace - 0.1.6-1
- Make Manual storage runtime-owned: source Portable uses the Hub tree; Integrated/Packaged use XDG.
- Add safe Source Portable/Integrated migration with optional component copy and explicit conflict handling.
- Manage source desktop integration during migration while packaged runtimes remain non-switchable.

* Mon Nov 09 2026 brunonlinespace - 0.1.5-1
- Add global Manual-versus-Managed preference for duplicate logical component IDs.
- Keep Configuration instance-complete while normal applet presentation follows the preference.
- Resolve duplicate module defaults through the preference without comparing versions; explicit per-instance enablement remains authoritative.

* Mon Nov 09 2026 brunonlinespace - 0.1.4-1
- Detect integrated source trees from existing desktop integration for the exact main.py.
- Preserve unintegrated direct source as Portable and packaged runtime behavior unchanged.
- No Suite Pythoine modification or path-name inference is required.

* Mon Nov 09 2026 brunonlinespace - 0.1.2-1
- Introduce explicit Source Portable, Source Integrated and Packaged runtime classification.
- Resolve Hub configuration/data roots from the runtime model without adding migration or mode switching.
- Generalize component ownership internally to Manual versus Managed while retaining RPM as the current managed provider.

* Mon Nov 09 2026 brunonlinespace - 0.1.1-1
- Refactor only: decompose the former monolithic Hub host implementation into focused source units.
- Preserve 0.1.0 runtime, UI, discovery, component-management and Module API behavior.
- Keep linspectacles.host as a compatibility import surface.

* Mon Nov 09 2026 brunonlinespace - 0.1.0-1
- Replace runtime-dependent component fallback discovery with one user-selected manual source plus the known RPM/system source.
- Keep Manual and RPM copies with the same logical ID visible as separate source-qualified instances.
- Make Add, Remove and Open Folder operate only on the selected manual source.
- Add compact version/source provenance to applet navigation rows.

* Mon Nov 09 2026 brunonlinespace - 0.0.11-1
- Apply Kernel Modules alternating-row table styling to Hub-owned tables.
- Apply Linux ResMon full rounded tab corners.
- Preserve 0.0.10 runtime behavior and input-focus correction.

* Mon Nov 09 2026 brunonlinespace - 0.0.10-1
- Prevent Dashboard type-to-search from stealing printable input from
  module-owned text-entry controls such as Encyclopedia search.
- Preserve Hub applet search, Ctrl+F, Module API 7 and component discovery.

* Thu Nov 05 2026 brunonlinespace - 0.0.9-1
- Add Module API 7 Applets-table column/action contributions while retaining APIs 1-6.
- Correct Applet Organizer integration to use the single Hub-owned Applets table.
- Let Portable mode discover lower-precedence XDG User and System (RPM) applets/modules.
- Preserve Portable-only writes/configuration and Portable > User > System precedence.

* Thu Nov 05 2026 brunonlinespace - 0.0.8-1
- Make applet search a permanent Hub capability with Ctrl+F and conservative type-to-search.
- Add Configuration -> Applets search, drag-and-drop ZIP installation and selection-aware writable-folder access.
- Add Module API 6 Applets-page extensions while retaining compatibility with APIs 1-5.
- Keep RPM/user component precedence and package-manager ownership unchanged.

* Thu Sep 24 2026 brunonlinespace - 0.0.7-2
- Complete the official offline Hub Module catalogue with Boot Environment and System Identity.
- Preserve packaged-system discovery and all runtime behavior from 0.0.7.

* Wed Sep 23 2026 brunonlinespace - 0.0.7-1
- Add packaged-system applet and Hub Module discovery beneath
  /usr/libexec/linspectacles/applets and /usr/libexec/linspectacles/modules.
- Keep user XDG component stores writable and higher priority than system
  components with the same logical ID.
- Mark component source in Configuration and prevent removal of RPM-owned
  applets/modules from the Hub; package removal remains a DNF operation.
- Preserve portable-mode discovery and existing applet/Module APIs.

* Wed Sep 23 2026 brunonlinespace - 0.0.6-2
- Remove the temporary linspectacles and linspectacles-suite Obsoletes rules so
  those package identities remain available for the finalized package taxonomy.
- Identify the host precisely as LinSpectacles Hub in About surfaces while
  keeping the normal desktop name and /usr/bin/linspectacles command unchanged.

* Wed Sep 23 2026 brunonlinespace - 0.0.6-1
- Adopt linspectacles-hub as the RPM package identity for the LinSpectacles host application.
- Move repository metadata to https://github.com/linspectacles/linspectacles-hub.
- Obsolete both prior experimental package names, linspectacles and
  linspectacles-suite, so repository upgrades can replace either one.
- Keep /usr/bin/linspectacles, desktop/AppStream identity, runtime paths, XDG
  stores, visible LinSpectacles branding and Linux Inspection Suite presentation.

* Wed Sep 23 2026 brunonlinespace - 0.0.5-0.1.exp1.r4
- Rename the RPM package from linspectacles to linspectacles-suite.
- Provide/obsolete the former linspectacles package so DNF/COPR upgrades replace
  the old package cleanly without changing the installed launcher or runtime paths.
- Runtime behavior is unchanged.

* Wed Sep 23 2026 brunonlinespace - 0.0.5-0.1.exp1.r3
- Add explicit RPM Vendor/Packager identity for local package frontends and
  enrich AppStream metadata for repository/software-center presentation.
- Runtime behavior is unchanged.

* Wed Sep 23 2026 brunonlinespace - 0.0.5-0.1.exp1.r2
- Fix Fedora metadata validation: use reverse-DNS AppStream developer ID and
  a single primary desktop category. Runtime behavior is unchanged.

* Wed Sep 23 2026 brunonlinespace - 0.0.5-0.1.exp1.r1
- Quote RPM buildroot destinations and use the revised exp1-r1 packaging so builds
  work when the source project path contains spaces.

* Wed Sep 23 2026 brunonlinespace - 0.0.5-0.1.exp1
- RPM Experiment 1: Suite shell RPM with user-owned XDG configuration,
  portable applet/module stores and no runtime writes beneath the RPM payload.
