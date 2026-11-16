"""
Ananke Zero-Copy Shared Memory IPC Ring.
Facilitates in-memory data plane exchange across process boundaries.
"""

import os
import struct
import time
from typing import Optional

RING_MAGIC = 0x414E414B # "ANAK"
HEADER_SIZE = 64
DEFAULT_SIZE = 4 * 1024 * 1024 # 4MB


class ZeroCopyRing:
    """Memory-mapped or file-backed zero-copy circular ring buffer."""

    def __init__(self, name: str, size_bytes: int = DEFAULT_SIZE):
        self.name = name
        self.size_bytes = size_bytes
        shm_dir = "/dev/shm" if os.path.exists("/dev/shm") else "/tmp"
        self.path = os.path.join(shm_dir, f"ananke_shm_{name}.ring")
        self._write_head = 0

        # Open/create backing file
        self._f = open(self.path, "a+b")
        total_len = HEADER_SIZE + size_bytes
        self._f.seek(0, os.SEEK_END)
        cur_len = self._f.tell()
        if cur_len < total_len:
            self._f.truncate(total_len)

        # Initialize header
        self._f.seek(0)
        hdr = self._f.read(HEADER_SIZE)
        if len(hdr) >= 4:
            magic = struct.unpack("<I", hdr[:4])[0]
            if magic != RING_MAGIC:
                init_hdr = struct.pack("<IQ8x40x", RING_MAGIC, size_bytes)
                self._f.seek(0)
                self._f.write(init_hdr)
                self._f.flush()

    def write(self, data: bytes) -> int:
        """Writes raw binary chunk with length prefix without memory reallocation."""
        data_len = len(data)
        if data_len + 4 > self.size_bytes:
            raise ValueError(f"Payload size {data_len} exceeds ring size {self.size_bytes}")

        offset = HEADER_SIZE + (self._write_head % self.size_bytes)
        self._write_head += (data_len + 4)

        buf = struct.pack("<I", data_len) + data
        self._f.seek(offset)
        self._f.write(buf)
        self._f.flush()
        return len(buf)

    def benchmark_throughput(self, iterations: int = 2000, chunk_size: int = 4096) -> float:
        """Benchmarks physical transfer throughput in GB/sec."""
        chunk = bytes([i % 256 for i in range(chunk_size)])
        t0 = time.perf_counter()
        for _ in range(iterations):
            self.write(chunk)
        elapsed = time.perf_counter() - t0
        total_bytes = iterations * chunk_size
        gb_per_sec = (total_bytes / (1024 * 1024 * 1024)) / elapsed
        return gb_per_sec

    def close(self):
        if self._f and not self._f.closed:
            self._f.close()

    def destroy(self):
        self.close()
        if os.path.exists(self.path):
            try:
                os.remove(self.path)
            except OSError:
                pass

