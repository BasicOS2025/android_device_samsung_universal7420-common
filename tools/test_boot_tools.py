#!/usr/bin/env python3
"""Check actual host packers against Samsung's binary layout with synthetic DTBs."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
tools = root / 'tools/dtbhtool'


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def align(value, page):
    return (value + page - 1) // page * page


with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    for binary, source, libs in [('dtbtool', 'mkdtbimg.c', ['-lfdt']),
                                  ('mkbootimg', 'mkbootimg.c', ['-lfdt', '-lcrypto'])]:
        run('cc', '-Wall', '-Wextra', '-Werror', '-Wno-deprecated-declarations',
            '-I' + str(root / 'include'), '-I' + str(tools / 'libdtbimg'),
            tools / source, tools / 'dtbimg.c', *libs, '-o', work / binary)

    dtbs = work / 'dtbs'
    dtbs.mkdir()
    # Enough entries to cross a header page; this catches incorrect offsets and
    # the upstream quadratic header-size calculation, which breaks multi-DTB images.
    for revision in range(70):
        source = work / 'fixture.dts'
        source.write_text('/dts-v1/; / { model_info-chip = <0x7420>; '
                          'model_info-platform = "android"; model_info-subtype = "samsung"; '
                          f'model_info-hw_rev = <{revision}>; model_info-hw_rev_end = <{revision}>; }};')
        run('dtc', '-I', 'dts', '-O', 'dtb', '-o', dtbs / f'{revision:03}.dtb', source)

    kernel, ramdisk = bytes(range(256)) * 17, b'RAMDISK' * 293
    (work / 'kernel').write_bytes(kernel)
    (work / 'ramdisk').write_bytes(ramdisk)
    for page in (2048, 4096):
        run(work / 'dtbtool', '-o', work / 'dt.img', '-s', page, '--dt_dir', dtbs)
        dt = (work / 'dt.img').read_bytes()
        assert struct.unpack_from('<4sII', dt) == (b'DTBH', 2, 70)
        for revision in range(70):
            chip, platform, subtype, first, last, offset, size, delimiter = struct.unpack_from('<8I', dt, 12 + revision * 32)
            assert (chip, platform, subtype, first, last, delimiter) == (0x7420, 0x50a6, 0x217584da, revision, revision, 0x20)
            payload = (dtbs / f'{revision:03}.dtb').read_bytes()
            assert offset % page == 0 and size == align(len(payload), page)
            assert dt[offset:offset + len(payload)] == payload

        run(work / 'mkbootimg', '--kernel', work / 'kernel', '--ramdisk', work / 'ramdisk',
            '--dt', work / 'dt.img', '--pagesize', page, '--base', '0x10000000',
            '--kernel_offset', '0x8000', '--ramdisk_offset', '0x01000000',
            '--tags_offset', '0x100', '--cmdline', 'console=ttySAC0', '--output', work / 'boot.img')
        boot = (work / 'boot.img').read_bytes()
        header = struct.unpack_from('<8s10I16s512s32s', boot)
        assert header[:11] == (b'ANDROID!', len(kernel), 0x10008000, len(ramdisk), 0x11000000,
                               0, 0x10f00000, 0x10000100, page, len(dt), 0)
        assert boot[page:page + len(kernel)] == kernel
        ramdisk_offset = page + align(len(kernel), page)
        dt_offset = ramdisk_offset + align(len(ramdisk), page)
        assert boot[ramdisk_offset:ramdisk_offset + len(ramdisk)] == ramdisk
        assert boot[dt_offset:dt_offset + len(dt)] == dt
        digest = hashlib.sha1()
        for payload in (kernel, ramdisk, b'', dt):
            digest.update(payload)
            digest.update(struct.pack('<I', len(payload)))
        assert header[-1][:20] == digest.digest()

    invalid = work / 'invalid'
    invalid.mkdir()
    (work / 'fixture.dts').write_text('/dts-v1/; / { model = "invalid"; };')
    run('dtc', '-I', 'dts', '-O', 'dtb', '-o', invalid / 'invalid.dtb', work / 'fixture.dts')
    result = subprocess.run([str(work / 'dtbtool'), '-o', str(work / 'bad.img'), '-s', '2048', '--dt_dir', str(invalid)])
    assert result.returncode > 0, 'Invalid DTB must be rejected without a crash'
print('PASS: DTBH entries, payload offsets, Samsung boot header, SHA-1 and invalid-DTB rejection')
