"""Offline regression tests for the independent FLYC parameter-name hash."""

from __future__ import annotations

import unittest

import dji_flyc_parameter_hash as subject


class RegressionVectorTests(unittest.TestCase):
    def test_all_pinned_vectors_match(self):
        for name, expected in subject.REGRESSION_VECTORS:
            with self.subTest(name=name):
                self.assertEqual(subject.dji_flyc_parameter_hash(name), expected)

    def test_little_endian_wire_form(self):
        self.assertEqual(
            subject.dji_flyc_parameter_hash_le("rid_ctrl_enable_0"),
            b"\x4f\x86\xbd\x3c",
        )
        self.assertEqual(
            subject.dji_flyc_parameter_hash_le("g_config.flying_limit.max_height_0"),
            b"\x8a\x23\x71\x03",
        )


class InvariantTests(unittest.TestCase):
    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            subject.dji_flyc_parameter_hash("")

    def test_non_string_is_rejected(self):
        with self.assertRaises(TypeError):
            subject.dji_flyc_parameter_hash(None)  # type: ignore[arg-type]

    def test_result_is_inside_u32(self):
        for name, _ in subject.REGRESSION_VECTORS:
            value = subject.dji_flyc_parameter_hash(name)
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 0xFFFFFFFF)

    def test_index_suffix_is_distinct(self):
        # The array-index ``_0`` suffix materially changes the hash, so a
        # base name and its ``_0`` form are never interchangeable on the wire.
        base = subject.dji_flyc_parameter_hash("g_config.flying_limit.max_height")
        indexed = subject.dji_flyc_parameter_hash("g_config.flying_limit.max_height_0")
        self.assertNotEqual(base, indexed)

    def test_base_and_indexed_names_map_to_their_own_hashes(self):
        # The two ``max_height`` forms resolve to two distinct, pinned hashes;
        # 0x0371238A is the ``_0`` form and 0xF412036C is the base form.
        self.assertEqual(
            subject.dji_flyc_parameter_hash("g_config.flying_limit.max_height_0"),
            0x0371238A,
        )
        self.assertEqual(
            subject.dji_flyc_parameter_hash("g_config.flying_limit.max_height"),
            0xF412036C,
        )


if __name__ == "__main__":
    unittest.main()
