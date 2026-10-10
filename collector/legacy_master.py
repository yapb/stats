"""Legacy UDP master server queries (community masters).

Same wire protocol game clients use against Steam masters: 0x31, region,
seed address, filter. Paginates through seed chaining until 0.0.0.0:0.
"""

from __future__ import annotations

import socket
import struct

REGION_ALL = 0xFF


def query(host, port, gamedir, timeout=8.0, max_batches=500):
    """All "ip:port" strings the master reports for one gamedir."""
    filt = f"\\gamedir\\{gamedir}".encode("ascii")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    found = []
    seed = b"0.0.0.0:0"
    try:
        for _ in range(max_batches):
            sock.sendto(b"\x31\xff" + seed + b"\x00" + filt + b"\x00", (host, port))
            try:
                data, _ = sock.recvfrom(8192)
            except socket.timeout:
                break
            if len(data) < 6 or data[:6] != b"\xff\xff\xff\xff\x66\x0a":
                break
            batch = []
            body = data[6:]
            for i in range(0, len(body) - 5, 6):
                ip = socket.inet_ntoa(body[i:i + 4])
                (p,) = struct.unpack(">H", body[i + 4:i + 6])
                batch.append((ip, p))
            if not batch:
                break
            if batch[-1] == ("0.0.0.0", 0):
                found.extend(s for s in batch if s != ("0.0.0.0", 0))
                break
            found.extend(batch)
            seed = f"{batch[-1][0]}:{batch[-1][1]}".encode("ascii")
    finally:
        sock.close()
    deduped = []
    seen = set()
    for ip, p in found:
        addr = f"{ip}:{p}"
        if addr not in seen:
            seen.add(addr)
            deduped.append(addr)
    return deduped
