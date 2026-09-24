Name:           linspectacles-hub
Version:        0.0.7
Release:        2%{?dist}
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

install -Dm0644 packaging/rpm/linspectacles.desktop \
  "%{buildroot}%{_datadir}/applications/linspectacles.desktop"
install -Dm0644 assets/linspectacles-icon.png \
  "%{buildroot}%{_datadir}/icons/hicolor/512x512/apps/linspectacles.png"
install -Dm0644 packaging/rpm/io.github.linspectacles.LinSpectacles.metainfo.xml \
  "%{buildroot}%{_metainfodir}/io.github.linspectacles.LinSpectacles.metainfo.xml"

desktop-file-validate "%{buildroot}%{_datadir}/applications/linspectacles.desktop"
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
%{_datadir}/applications/linspectacles.desktop
%{_datadir}/icons/hicolor/512x512/apps/linspectacles.png
%{_metainfodir}/io.github.linspectacles.LinSpectacles.metainfo.xml

%changelog
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
