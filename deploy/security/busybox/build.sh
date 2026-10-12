#!/bin/sh
set -eu
# Rebuild the pinned Alpine recipe with the upstream-reviewed URL guard.
# Inputs: /backport/wget-CVE-2025-60876.patch; output: /out/busybox.
# Keep the original package version; scanners require a digest-bound backport/VEX record.
aports_commit=a0257ffd167404ef7bf92d0e20f98f3693465d54
patch_sha256=5e477d2d6f7a485547eca2d56e0ab477d42b06219cb8cd4daed3bb32a14d695c
mkdir -p /build /out /build/distfiles
export SRCDEST=/build/distfiles
cd /build
git init -q aports
git -C aports remote add origin https://github.com/alpinelinux/aports.git
git -C aports fetch --depth=1 --filter=blob:none origin "$aports_commit"
test "$(git -C aports rev-parse FETCH_HEAD)" = "$aports_commit"
git -C aports checkout FETCH_HEAD -- main/busybox
SOURCE_DATE_EPOCH=$(git -C aports show -s --format=%ct FETCH_HEAD)
export SOURCE_DATE_EPOCH
cp -R aports/main/busybox recipe
printf '%s  %s\n' "$patch_sha256" /backport/wget-CVE-2025-60876.patch | sha256sum -c -
cp /backport/wget-CVE-2025-60876.patch recipe/
cd recipe
# Original source+config+all patches retain Alpine's SHA512 verification.
# The upstream-reviewed URL guard is appended after the unchanged vendor patches.
printf '\nsource="$source wget-CVE-2025-60876.patch"\nsha512sums="$sha512sums\n%s  wget-CVE-2025-60876.patch\n"\n' "$(sha512sum wget-CVE-2025-60876.patch | cut -d ' ' -f 1)" >> APKBUILD
# Build all original variants via Alpine's own recipe and configuration.
JOBS=4 MAKEFLAGS=-j4 abuild -F fetch verify unpack prepare build
# Alpine check() performs this final relink with static utmps/skarnet before tests.
# Invoke only that relink as a custom abuild command, preserving abuild CFLAGS/LDFLAGS.
# This avoids exporting a binary with additional dynamic-library requirements.
cat >> APKBUILD <<'RELINK'
liqvera_final_link() {
    local _extra_cflags="$(pkg-config --cflags --static libutmps)"
    local _extra_libs="-Wl,--push-state,-Bstatic $(pkg-config --libs --static libutmps) -Wl,--pop-state"
    make -C "$_dyndir" KBUILD_OUTPUT="$_dyndir" CONFIG_EXTRA_CFLAGS="$_extra_cflags" CONFIG_EXTRA_LDLIBS="$_extra_libs"
}
RELINK
JOBS=4 MAKEFLAGS=-j4 abuild -F liqvera_final_link
/bin/busybox --list-full > /out/original-applets.txt
src/build-dynamic/busybox --list-full > /out/patched-applets.txt
cmp /out/original-applets.txt /out/patched-applets.txt
cp src/build-dynamic/busybox /out/busybox
cp src/busybox-*/LICENSE /out/LICENSE
chmod 0755 /out/busybox
sha256sum /out/busybox > /out/busybox.sha256
# Keep an exact GPL-corresponding source/recipe bundle beside the output.
tar -czf /out/busybox-corresponding-source.tar.gz -C /build --exclude=recipe/src --exclude=recipe/pkg recipe distfiles
