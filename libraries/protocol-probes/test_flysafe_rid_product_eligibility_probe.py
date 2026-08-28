import unittest

from flysafe_rid_product_eligibility_probe import (
    UnsafeInputError,
    reject_credential_bearing_input,
    sanitize_background_response,
    sanitize_product_response,
)


class ProductEligibilityProbeTests(unittest.TestCase):
    def test_product_response_is_minimized(self):
        source = {
            "code": 0,
            "data": [
                {
                    "id": 139,
                    "name": "DJI Mini 5 Pro",
                    "slug": "dji-mini-5-pro",
                    "support_unlock_type": ["Geo", "Rid"],
                    "internal_note": "must not be emitted",
                },
                {"id": 1, "name": "Another Aircraft", "support_unlock_type": ["Geo"]},
            ],
        }
        result = sanitize_product_response(source)
        self.assertEqual(result["record_count"], 2)
        self.assertTrue(result["eligibility_known"])
        self.assertEqual(len(result["matches"]), 1)
        self.assertTrue(result["matches"][0]["supports_rid"])
        self.assertNotIn("internal_note", result["matches"][0])

    def test_public_catalog_does_not_claim_eligibility(self):
        source = {"drones": [{"name": "DJI Mini 5 pro", "slug": "dji-mini-5-pro"}]}
        # The public endpoint's payload is intentionally adapted before this helper in
        # anonymous_probe; this test covers an equivalent list response directly.
        result = sanitize_product_response(source["drones"])
        self.assertEqual(len(result["matches"]), 1)
        self.assertFalse(result["eligibility_known"])
        self.assertIsNone(result["matches"][0]["supports_rid"])

    def test_rejects_token_bearing_export(self):
        with self.assertRaises(UnsafeInputError):
            reject_credential_bearing_input(
                {"request": {"headers": {"Authorization": "Bearer do-not-read"}}}
            )

    def test_mainland_background_gate(self):
        result = sanitize_background_response(
            {"code": 0, "data": {"background_type": 0, "status": 4, "qualify": 1, "country": 156}}
        )
        self.assertTrue(result["mainland_rid_card_gate"])
        self.assertFalse(result["abroad_rid_card_gate"])

    def test_abroad_background_gate(self):
        result = sanitize_background_response(
            {"data": {"background_type": 3, "status": 4, "qualify": 1, "country": 840}}
        )
        self.assertFalse(result["mainland_rid_card_gate"])
        self.assertTrue(result["abroad_rid_card_gate"])
        self.assertFalse(result["country_is_china"])


if __name__ == "__main__":
    unittest.main()
