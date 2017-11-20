#!/usr/bin/env python3

import sys
import asyncio
import pathlib
import argparse
import functools
import subprocess
from asyncio.subprocess import PIPE, STDOUT
from tempfile import NamedTemporaryFile
from http.client import HTTPConnection

from olympusphotosync import cli, oishare, utils

try:
    from tm1637 import TM1637
except ImportError:
    TM1637 = None

# A TM1637 is used to optionally display progress.
tm1637 = None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--iface', metavar='str', required=True, help='wireless interface name')
    p.add_argument('-s', '--ssid', metavar='str', required=True, help='ssid of camera wifi network')
    p.add_argument('-p', '--password', metavar='str', required=True, help='wifi password')
    p.add_argument('-e', '--newer', metavar='str', default=(None, None), help=argparse.SUPPRESS)
    p.add_argument('--tm1637-clk-dio', metavar='int', type=int, nargs=2, default=(23, 24), help=argparse.SUPPRESS)
    p.add_argument('destdir', type=pathlib.Path, help='destination directory')
    args = p.parse_args()

    # Create a wpa_supplicant config file.
    wpa_conf_fh = NamedTemporaryFile()
    subprocess.run(['wpa_passphrase', args.ssid], input=args.password.encode('utf8'), stdout=wpa_conf_fh, check=True)

    global tm1637
    try:
        if TM1637 and args.tm1637_clk_dio:
            tm1637 = TM1637(*args.tm1637_clk_dio)
            tm1637.clear()
    except:
        pass

    if tm1637:
        download_func = functools.partial(download_reporter_tm1637, tm1637=tm1637)
    else:
        download_func = download_reporter_basic

    # Sync only files newer than the specified filename (e.g. PA290946.JPG)
    if isinstance(args.newer, str):
        args.newer = (utils.parse_filename(args.newer), 'name')

    try:
        loop = asyncio.get_event_loop()
        main_task = asyncio.ensure_future(main_coro(args, wpa_conf_fh, download_func))
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        main_task.cancel()
    finally:
        del wpa_conf_fh
        tm1637.clear()


async def main_coro(args, wpa_conf_fh, download_func):
    # Set when wifi is connected - cleared when disconnected.
    ev_connected = asyncio.Event()

    proc_wpa = await asyncio.create_subprocess_exec('wpa_supplicant', '-i', args.iface, '-c', wpa_conf_fh.name)
    proc_iw  = await asyncio.create_subprocess_exec('iw', 'event', stdout=PIPE, stderr=STDOUT)

    try:
        await asyncio.gather(
            asyncio.ensure_future(iw_listen(proc_iw, ev_connected)),
            asyncio.ensure_future(on_connect(args.destdir, args.iface, ev_connected, download_func, args.newer)),
        )
    finally:
        proc_iw.terminate()
        proc_wpa.terminate()


async def iw_listen(proc, ev_connected):
    while True:
        line = await proc.stdout.readline()
        if line:
            if b': connected to' in line:
                ev_connected.set()
            elif b': disconnected ' in line:
                ev_connected.clear()


def download_reporter_tm1637(conn, fh, entry, num_entries, num_entry, tm1637):
    remaining = min(99, (num_entries - num_entry))
    print('GET: %s size:%s progress:%d/%d' % (fh.name, entry.size, num_entry, num_entries))

    display_data = [remaining // 10, remaining % 10, 9, 9]
    tm1637.show(display_data)
    tm1637.show_colon()

    total_bytes = entry.size
    data_read = 0
    for data in oishare.download(conn, entry, chunksize=65536):
        data_read += len(data)

        done = 100 - 100 * data_read // total_bytes
        display_data[2] = done // 10
        display_data[3] = done % 10

        fh.write(data)
        tm1637.show(display_data)


def download_reporter_basic(conn, fh, entry, num_entries, num_entry):
    print('GET: %s size:%s progress:%d/%d' % (fh.name, entry.size, num_entry, num_entries))
    for data in oishare.download(conn, entry, chunksize=65536):
        fh.write(data)


async def on_connect(destdir, iface, ev_connected, download_func, newer):
    while True:
        await ev_connected.wait()

        proc_dhcp = await asyncio.create_subprocess_exec('udhcpc', '-i', iface, '--quit', '-f', '-s', './alpine/udhcpc.sh')
        await proc_dhcp.wait()

        conn = HTTPConnection('192.168.0.10', '80', 10)

        try:
            entries = oishare.find_entries(conn, '/DCIM/100OLYMP')
            entries = oishare.filter_entries(entries, newer, (None, None))
            entries = list(entries)

            cli.cmd_sync(conn, entries, destdir, download_func=download_func)
        except:
            # TODO: handle more gracefully
            pass
        finally:
            ev_connected.clear()
            if tm1637:
                tm1637.clear()


if __name__ == '__main__':
    main()
