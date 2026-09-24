#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$HERE/../.." && pwd)"
VERSION="0.0.7"
TOPDIR="${RPM_TOPDIR:-${XDG_CACHE_HOME:-$HOME/.cache}/linspectacles/rpmbuild-0.0.7}"
DIST_OUT="$ROOT/dist-rpm"

for tool in rpmbuild python3 desktop-file-validate appstreamcli; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing build prerequisite: $tool" >&2
        echo "On Fedora install the required RPM build/validation packages, then rerun this script." >&2
        exit 2
    fi
done

rm -rf "$TOPDIR" "$DIST_OUT"
mkdir -p "$TOPDIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} "$DIST_OUT"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SRC="$WORK/linspectacles-hub-$VERSION"
mkdir -p "$SRC"

# Copy only source/runtime material. Mutable portable stores and build outputs
# are deliberately excluded from the RPM source tarball.
for item in main.py linspectacles assets README.md APPLET-SDK.md MODULE-SDK.md LICENSE suite-pythoine-extension.json packaging; do
    cp -a "$ROOT/$item" "$SRC/"
done
find "$SRC" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$SRC" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

tar -C "$WORK" -czf "$TOPDIR/SOURCES/linspectacles-hub-$VERSION.tar.gz" "linspectacles-hub-$VERSION"
cp "$HERE/linspectacles-hub.spec" "$TOPDIR/SPECS/"

rpmbuild -ba --define "_topdir $TOPDIR" "$TOPDIR/SPECS/linspectacles-hub.spec"
find "$TOPDIR/RPMS" "$TOPDIR/SRPMS" -type f \( -name '*.rpm' -o -name '*.src.rpm' \) -exec cp -a {} "$DIST_OUT/" \;

echo "RPM artifacts: $DIST_OUT"
