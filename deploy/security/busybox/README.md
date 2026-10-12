# BusyBox URL validation backport

The Alpine 3.23/3.24 BusyBox 1.37.0 packages retain CVE-2025-60876. Liqvera builds the original Alpine recipe at commit `a0257ffd167404ef7bf92d0e20f98f3693465d54` with [the upstream-reviewed URL guard](https://lists.busybox.net/pipermail/busybox/2025-November/091840.html). The local patch SHA-256 is `5e477d2d6f7a485547eca2d56e0ab477d42b06219cb8cd4daed3bb32a14d695c`.

All original configurations and distribution patches are verified with Alpine's SHA-512 manifest. The recipe builds its original variants, then reproduces the final static utmps/skarnet relink from its check phase. The dynamic binary retains all 304 original applets; no upstream package version is invented. The full BusyBox test suite is not a build gate. Targeted URL validation tests run separately without network access beyond a private loopback listener.

The final images install the binary after their last APK operation and retain the exact corresponding source/recipe archive, GPL license, applet inventories and build-output hash under `/usr/local/share/liqvera-security/busybox/`. A later APK reinstall can replace this patched binary and requires rebuilding/rechecking the image. Review and retire this backport when a vendor-fixed release is available.

The regression accepts ordinary and percent-encoded paths, and rejects raw controls/spaces and proxy-host header injection before opening a connection. Version-based scanners may still match 1.37.0; retain raw findings and bind the fixed disposition to the actual image and binary digests.
