"""A2S_RULES fetcher with GoldSrc and Source split-packet support.

python-a2s only understands Source style fragments, so GoldSrc servers with
long rule lists (every server with plugins, exactly the ones worth counting)
die there with BrokenMessageError. This implements the same flow by hand:
challenge handling, both split formats, bzip2 payloads.
"""

from __future__ import annotations

import bz2
import socket
import struct
import time
import zlib

A2S_RULES = 0x56
S2C_CHALLENGE = 0x41
S2A_RULES = 0x45
S2A_INFO_SOURCE = 0x49
S2A_PLAYER = 0x44


class RulesError(Exception):
    pass


def fetch_rules(addr, timeout=1.5, goldsrc=True, attempts=3):
    """Return rules dict for one "host:port" addr. Raises on failure."""
    host, _, port = addr.rpartition(":")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        data = _challenge_flow(sock, (host, int(port)), attempts)
        header = struct.unpack("<i", data[:4])[0]
        if header == -1:
            return _parse(data, compressed=False)
        if header == -2:
            return _collect_and_parse(sock, data, timeout, goldsrc)
        raise RulesError(f"bad header {header}")
    finally:
        sock.close()


def _request(sock, server, challenge):
    sock.sendto(b"\xff\xff\xff\xff" + bytes([A2S_RULES]) + challenge, server)
    data, _ = sock.recvfrom(8192)
    if len(data) < 5:
        raise RulesError("reply too short")
    return data


def _challenge_flow(sock, server, attempts):
    challenge = b"\xff\xff\xff\xff"
    for _ in range(attempts):
        data = _request(sock, server, challenge)
        header = struct.unpack("<i", data[:4])[0]
        if header == -2:
            return data  # immediate multi-packet rules reply
        if header != -1:
            raise RulesError(f"bad header {header}")
        kind = data[4]
        if kind == S2A_RULES:
            return data  # immediate single-packet rules reply
        if kind in (S2A_INFO_SOURCE, S2A_PLAYER):
            challenge = b"\xff\xff\xff\xff"
            continue  # confused challenge: stale packet, retry from scratch
        if kind == S2C_CHALLENGE:
            challenge = data[5:9]
            continue  # ask again with the challenge attached
        raise RulesError(f"bad challenge kind {kind:#x}")
    raise RulesError("challenge loop exhausted")


def _collect_and_parse(sock, first, timeout, goldsrc):
    """Gather split datagrams until some format yields a complete coherent
    set, then parse it. Slow-but-steady fragments still complete; only a
    dead stop ends the wait."""
    order = (goldsrc, not goldsrc)
    raw = [first]
    sock.settimeout(0.4)
    deadline = time.monotonic() + max(2.0, timeout)
    while True:
        for hint in order:
            ready = _try_interpret(raw, hint)
            if ready is not None:
                payload, compressed = ready
                try:
                    return _parse(payload, compressed=compressed)
                except RulesError:
                    continue  # coherent under this hint but garbage: try next
        if time.monotonic() >= deadline:
            break
        try:
            data, _ = sock.recvfrom(8192)
        except socket.timeout:
            break
        if len(data) >= 5 and struct.unpack("<i", data[:4])[0] == -2:
            raw.append(data)
        if len(raw) > 64:
            break
    raise RulesError("incomplete split set")


def _try_interpret(raw, goldsrc):
    """Complete coherent set mapped to (payload, compressed), None when the
    set is merely incomplete, raises RulesError when incoherent."""
    packets = {}
    total = None
    compressed = False
    for data in raw:
        number, count, payload, is_comp = _split_header(data, goldsrc)
        if not 1 <= count <= 64 or not 0 <= number < count:
            raise RulesError("split set incoherent")
        if total is None:
            total = count
            compressed = is_comp
        elif count != total:
            raise RulesError("split count changed mid reply")
        packets[number] = payload
    if total is None or len(packets) < total:
        return None
    return b"".join(packets[i] for i in range(total)), compressed


def _split_header(data, goldsrc):
    if goldsrc:
        pkt = data[4]
        return (pkt >> 4) & 0xF, pkt & 0xF, data[5:], False
    seq = struct.unpack("<I", data[4:8])[0]
    total = data[8]
    number = data[9]
    return number, total, data[12:], bool(seq & 0x80000000)


def _parse(data, compressed):
    if compressed:
        size, checksum = struct.unpack("<II", data[:8])
        if size > 1024 * 1024:
            raise RulesError("decompressed size insane")
        try:
            data = bz2.decompress(data[8:])
        except Exception as e:
            raise RulesError(f"bz2 failed: {e}")
        if len(data) != size:
            raise RulesError("decompressed size mismatch")
        if zlib.crc32(data) & 0xFFFFFFFF != checksum:
            raise RulesError("decompressed checksum mismatch")
    if struct.unpack("<i", data[:4])[0] != -1 or data[4] != S2A_RULES:
        raise RulesError("bad rules reply")
    count = struct.unpack("<H", data[5:7])[0]
    out = {}
    pos = 7
    for _ in range(count):
        key, pos = _cstr(data, pos)
        if key is None:
            break
        val, pos = _cstr(data, pos)
        if val is None:
            break
        out[key] = val
    return out


def _cstr(data, pos):
    end = data.find(b"\x00", pos)
    if end < 0:
        return None, pos
    raw = data[pos:end]
    return _decode(raw), end + 1


def _decode(raw):
    for enc in ("utf-8", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")
