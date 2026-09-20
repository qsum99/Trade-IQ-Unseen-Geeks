"""Unit tests: core_schemas envelope contracts (api.md §3)."""
import unittest


class TestSchemas(unittest.TestCase):
    def test_envelope_shape(self):
        from samarth_work.core_schemas.schemas import envelope

        out = envelope({"a": 1}, request_id="r1")
        self.assertTrue(out["success"])
        self.assertEqual(out["data"], {"a": 1})
        self.assertEqual(out["meta"], {"request_id": "r1"})
        self.assertIsNone(out["error"])

    def test_error_envelope_shape(self):
        from samarth_work.core_schemas.schemas import error_envelope

        out = error_envelope("BAD", "msg")
        self.assertFalse(out["success"])
        self.assertIsNone(out["data"])
        self.assertEqual(out["error"]["code"], "BAD")


if __name__ == "__main__":
    unittest.main()
