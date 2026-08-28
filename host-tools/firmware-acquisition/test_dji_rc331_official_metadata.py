import unittest

import dji_rc331_official_metadata as subject


class Rc331MetadataTests(unittest.TestCase):
    def test_targets_are_hard_locked(self):
        self.assertEqual(subject.PRODUCT_ID, "rc331")
        self.assertEqual(subject.TARGET_VERSIONS, ("10.00.0700", "10.00.0800"))

    def test_module_delta(self):
        older = {
            "product_version": "10.00.0700",
            "modules": [
                {"module_id": "0100", "module_version": "1", "size": 3, "md5": "a"},
                {"module_id": "0200", "module_version": "1", "size": 4, "md5": "b"},
            ],
        }
        newer = {
            "product_version": "10.00.0800",
            "modules": [
                {"module_id": "0100", "module_version": "2", "size": 3, "md5": "c"},
                {"module_id": "0300", "module_version": "1", "size": 5, "md5": "d"},
            ],
        }
        delta = subject.compare_configs(older, newer)
        self.assertEqual([item["module_id"] for item in delta["changed_modules"]], ["0100"])
        self.assertEqual([item["module_id"] for item in delta["added_modules"]], ["0300"])
        self.assertEqual([item["module_id"] for item in delta["removed_modules"]], ["0200"])

    def test_duplicate_module_is_refused(self):
        config = {
            "modules": [
                {"module_id": "0100"},
                {"module_id": "0100"},
            ]
        }
        with self.assertRaises(subject.common.FormatError):
            subject._module_index(config)

    def test_config_source_omits_opaque_path_and_query(self):
        source = subject._public_config_source(
            {
                "host": "example.djicdn.com",
                "path": "/opaque/segments/rc331_0000_v10.00.0800.pro.cfg.sig",
                "query": "must-not-survive",
                "redirect_count": 1,
            }
        )
        self.assertEqual(
            source,
            {
                "host": "example.djicdn.com",
                "filename": "rc331_0000_v10.00.0800.pro.cfg.sig",
                "query": "omitted",
                "redirect_count": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
