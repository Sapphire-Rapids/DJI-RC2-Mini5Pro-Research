import os
import tempfile
import unittest
from pathlib import Path

from patch_cnxn_gate import analyze, create_copy, encode_mov_wzr


EXACT_V07 = Path(os.environ["RC2_ADBD_V07"]) if "RC2_ADBD_V07" in os.environ else None
ADJACENT = Path(os.environ["RC2_ADBD_ADJACENT"]) if "RC2_ADBD_ADJACENT" in os.environ else None
EXPECTED_SHA256 = "b300d9bb90f5941fe2952bc9f6dacc30e639a498be4435f59a4ae95134bd5422"


class PatchTests(unittest.TestCase):
    def test_known_instruction_vector(self):
        self.assertEqual(encode_mov_wzr(bytes.fromhex("f5a79f1a")), bytes.fromhex("f5031f2a"))

    @unittest.skipUnless(EXACT_V07, "set RC2_ADBD_V07 to test the excluded exact-v07 sample")
    def test_exact_v07_and_adjacent_build_site_and_control_flow(self):
        samples = [EXACT_V07]
        if ADJACENT:
            self.assertEqual(EXACT_V07.read_bytes(), ADJACENT.read_bytes())
            samples.append(ADJACENT)
        for sample in samples:
            with self.subTest(sample=sample):
                _, plan = analyze(sample)
                self.assertEqual(plan["input_sha256"], EXPECTED_SHA256)
                self.assertEqual(plan["patch_vaddr"], "0x90460")
                self.assertEqual(plan["patch_file_offset"], "0x90460")
                self.assertEqual(plan["gate_branch_vaddr"], "0x90488")
                self.assertEqual(plan["branch_target"], "0x904d8")
                self.assertEqual(plan["before_hex"], "f5a79f1a")
                self.assertEqual(plan["before_disasm"], "cset w21, lt")
                self.assertEqual(plan["after_hex"], "f5031f2a")
                self.assertEqual(plan["after_disasm"], "mov w21, wzr")

    @unittest.skipUnless(EXACT_V07, "set RC2_ADBD_V07 to test the excluded exact-v07 sample")
    def test_copy_changes_only_the_one_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "adbd.patched"
            plan = create_copy(EXACT_V07, output)
            original = EXACT_V07.read_bytes()
            patched = output.read_bytes()
            changed = [i for i, pair in enumerate(zip(original, patched)) if pair[0] != pair[1]]
            self.assertEqual(changed, [0x90461, 0x90462, 0x90463])
            self.assertEqual(plan["changed_offsets"], ["0x90461", "0x90462", "0x90463"])
            with self.assertRaisesRegex(ValueError, "dbg_cnt < 1 cset"):
                analyze(output)


if __name__ == "__main__":
    unittest.main()
