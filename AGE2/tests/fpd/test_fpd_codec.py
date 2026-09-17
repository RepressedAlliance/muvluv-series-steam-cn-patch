from __future__ import annotations

import struct
from pathlib import Path
import tempfile
import unittest
import zlib

from AGE2.tools.fpd.extract_fpd import safe_path
from AGE2.tools.fpd.fpd_codec import (
    ENTRY_SIZE,
    HEADER_SIZE,
    FpdEntry,
    parse_pack,
    xor_bytes,
)


class FpdCodecTests(unittest.TestCase):
    def test_v1_absolute_name_offsets(self) -> None:
        keys = [0x123456789ABCDEF]
        names = b"root/first.webp\0root/second.egpack\0"
        names_start = HEADER_SIZE + 2 * ENTRY_SIZE
        data_start = names_start + len(names)
        entries = b"".join(
            struct.pack(">QQQQ", names_start + offset, i, 1, 0)
            for i, offset in enumerate((0, len(b"root/first.webp\0")))
        )
        header = b"FPD\0" + struct.pack(">IQQ", 1, 2, data_start)
        header += bytes(HEADER_SIZE - len(header))
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "pack.bin"
            package.write_bytes(header + xor_bytes(entries + names, keys) + b"ab")
            version, parsed_start, parsed = parse_pack(package, keys)
        self.assertEqual((version, parsed_start), (1, data_start))
        self.assertEqual(parsed, [FpdEntry("root/first.webp", 0, 1, 0),
                                  FpdEntry("root/second.egpack", 1, 1, 0)])

    def test_synthetic_index_roundtrip(self) -> None:
        keys = [0x00112233445566778899AABBCCDDEEFF]
        name = b"root/assets/example.egpack\0"
        names = zlib.compress(name)
        payload = b"example payload"
        encrypted_payload = xor_bytes(payload, keys)
        index_size = ENTRY_SIZE + len(names)
        data_start = HEADER_SIZE + index_size
        entry = struct.pack(">QQQQ", 0, 0, len(encrypted_payload), 0)
        encrypted_index = xor_bytes(entry + names, keys)
        header = (
            b"FPD\0"
            + struct.pack(">IQQ", 2, 1, data_start)
            + bytes(HEADER_SIZE - 24)
        )
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "pack.bin"
            package.write_bytes(header + encrypted_index + encrypted_payload)
            version, parsed_start, entries = parse_pack(package, keys)

        self.assertEqual(version, 2)
        self.assertEqual(parsed_start, data_start)
        self.assertEqual(
            entries,
            [FpdEntry("root/assets/example.egpack", 0, len(payload), 0)],
        )

    def test_xor_is_its_own_inverse(self) -> None:
        keys = [0x123456789ABCDEF00123456789ABCDEF, 0xA5]
        payload = bytes(range(255))
        self.assertEqual(xor_bytes(xor_bytes(payload, keys), keys), payload)

    def test_member_path_rejects_traversal_and_absolute_forms(self) -> None:
        base = Path("safe")
        self.assertEqual(
            safe_path(base, "root/assets/a.egpack"),
            base / "root" / "assets" / "a.egpack",
        )
        for value in ("../escape", "/absolute", r"C:\\escape", r"..\\escape"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_path(base, value)


if __name__ == "__main__":
    unittest.main()
