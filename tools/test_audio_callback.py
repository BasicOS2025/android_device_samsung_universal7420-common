#!/usr/bin/env python3
"""Run the real WB-AMR callback with a one-byte ASan allocation."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'hardware/audio/ril_interface.c').read_text()
start = source.index('static int ril_internal_wb_amr_callback(')
end = source.index('static int ril_connect_if_required(', start)
callback = source[start:end]
harness = r'''
#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#define __unused __attribute__((unused))
typedef void *HRilClient;
static void (*_wb_amr_callback)(void *, int);
static void *_wb_amr_data;
static int calls;
static int received;
static void capture(void *context, int value) {
    assert(context == &calls);
    ++calls;
    received = value;
}
''' + callback + r'''
int main(void) {
    _wb_amr_callback = capture;
    _wb_amr_data = &calls;
    unsigned char *packet = malloc(1);
    assert(packet);
    packet[0] = 2;
    assert(ril_internal_wb_amr_callback(NULL, packet, 1) == 0);
    assert(calls == 1 && received == 2);
    assert(ril_internal_wb_amr_callback(NULL, NULL, 1) == -1);
    assert(ril_internal_wb_amr_callback(NULL, packet, 0) == -1);
    assert(ril_internal_wb_amr_callback(NULL, packet, 4) == -1);
    assert(calls == 1);
    _wb_amr_callback = NULL;
    assert(ril_internal_wb_amr_callback(NULL, packet, 1) == -1);
    free(packet);
    return 0;
}
'''
with tempfile.TemporaryDirectory() as temporary:
    work = Path(temporary)
    (work / 'callback.c').write_text(harness)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(work / 'callback.c'), '-o', str(work / 'callback')], check=True)
    subprocess.run([str(work / 'callback')], check=True)
print('PASS: actual WB-AMR callback handles one-byte payload and rejects invalid inputs under ASan/UBSan')
