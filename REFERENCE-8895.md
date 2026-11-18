# Android 16 reference comparison

Reference: universal8895 on Codeberg, common `lineage-23.2`, commit
`57bbd96d96622e5e7aaf968007b3a771120450a1`.

https://codeberg.org/universal8895/android_device_samsung_universal8895-common

The reference provides its fstab in the first-stage ramdisk and marks `/system`
with `first_stage_mount`. Our previous fstab marked `/system` as `recoveryonly`
and was installed only under vendor, making it unavailable to first-stage init.
The 7420 port now provides its own fstab in the ramdisk and enables the system
first-stage mount. EFS remains a normal checked mount, rather than recovery-only.
All 7420 block-device paths, partition sizes and userdata filesystem options
remain device-specific.

Already present in this port: non-A/B product inheritance, disabling early GL
preload for legacy Mali, legacy LMKD without PSI, and mixed 64/32-bit architecture.

The current Samsung Soong defaults consume
`samsungVars.target_specific_header_path`. The port now sets this explicitly,
while retaining the legacy header variable needed by older Make modules.

The supplied reference kernel is Linux 4.4.302, with cgroup BPF and filesystem
encryption enabled. The 7420 baseline is Linux 3.10.108; its feature availability
must be checked independently instead of copying the 8895 configuration.

Not transferred: 8895 GCC toolchain selection, kernel, proprietary binaries,
partition sizes, synthetic metadata partition, encryption flags, or modem/IMS
settings. These require independent 7420 evidence and testing. Android 16 source
configuration is a reference, not proof of Android 17 compatibility or 7420 boot.
