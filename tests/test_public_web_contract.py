import unittest

from sharpicks_contracts.v1 import ContractError
from sharpicks_contracts.web_v1 import WEB_EXPORT_VERSION, public_analysis, public_export


class PublicWebContractTests(unittest.TestCase):
    def test_pick_projection_preserves_site_fields_and_removes_unknowns(self):
        result = public_export({
            "generado": "2026-10-30T12:00:00Z",
            "precalculo": "2026-10-30T11:55:00Z",
            "internal_feature_vector": {"secret": 1},
            "picks": [{"id": "pick-1", "partido": "Local vs Visita", "apuesta": "Local",
                       "prob": 0.61, "cuota": 1.9, "estado": "pendiente", "vip_hay": True,
                       "debug_model": "private", "jug": [{"player": "VIP"}],
                       "ctx": {"fl": ["G", "P"], "lin": {"casa": "VIP"},
                               "sl": {"n": 10, "gf": 1.2, "private_feature": 999}}}],
        })

        self.assertEqual(result["contract_version"], WEB_EXPORT_VERSION)
        self.assertEqual(result["picks"][0]["prob"], 0.61)
        self.assertEqual(result["picks"][0]["ctx"], {"fl": ["G", "P"], "sl": {"n": 10, "gf": 1.2}})
        self.assertNotIn("internal_feature_vector", result)
        self.assertNotIn("debug_model", result["picks"][0])
        self.assertNotIn("jug", result["picks"][0])
        self.assertNotIn("lin", result["picks"][0]["ctx"])

    def test_analysis_projection_keeps_legacy_envelope(self):
        result = public_analysis({"generado": "2026-10-30T12:00:00Z",
                                  "analisis": [{"id": "an-1", "partido": "Local vs Visita",
                                                "solo_analisis": True, "unexpected": "private"}]})
        self.assertEqual(result["contract_version"], WEB_EXPORT_VERSION)
        self.assertTrue(result["analisis"][0]["solo_analisis"])
        self.assertNotIn("unexpected", result["analisis"][0])

    def test_malformed_rows_fail_closed(self):
        with self.assertRaises(ContractError):
            public_export({"picks": [None]})
        with self.assertRaises(ContractError):
            public_analysis({"analisis": {"id": "an-1"}})
        with self.assertRaises(ContractError):
            public_export({"picks": [{"ctx": []}]})
        with self.assertRaises(ContractError):
            public_export({"picks": [{"ctx": {"h2h": [["bad", "shape"]]}}]})


if __name__ == "__main__":
    unittest.main()
