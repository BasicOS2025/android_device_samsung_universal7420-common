# LineageOS 24 / Android 17 reference comparison

References examined:

- `LineageOS/android_device_samsung_z3s`, `lineage-24.0`,
  `94abd47d5e7884a00a1f73971ebe851c8bb9352b`.
- Its declared dependency `LineageOS/android_device_samsung_universal9830-common`,
  `lineage-24.0`, `f8db0251719ed30b92ce6765611af5c4d1826ead`.
- `LineageOS/android_kernel_samsung_universal9830`, `lineage-24.0`,
  `97369af7bbd66581d3e993fea083f3eed02d3c20` (Linux 4.19.325).

Applied to the 7420 port after checking the current platform implementation:

1. Select each device's init library using `libinit.vendor_init_lib` Soong config.
   Current `system/core/init/Android.bp` reads this setting for whole-static
   linkage. The old `TARGET_INIT_VENDOR_LIB` assignment is removed.
2. Enable `libui.legacy_gralloc`. The 7420 BSP uses gralloc module API 0.2;
   current libui uses this setting to define `LEGACY_GRALLOC`.
3. Enable `libion.legacy_impl`. The 7420 kernel exposes the legacy ION handle
   interface in `drivers/staging/android/uapi/ion.h`; the platform flag selects
   `ion_legacy.c` and legacy headers instead of the modern ION API.

Not transferred: S20 boot header v2, dynamic partitions, AVB, DTBO layout, CPU
instruction extensions, Mali drivers, audio DSP settings, or kernel. Those are
specific to Exynos 990. The 7420 port retains its own boot format and partitions.

These configuration changes have not yet passed a complete ROM build or a phone
boot test. The separate DTBH/boot-tool binary-format tests remain successful.
