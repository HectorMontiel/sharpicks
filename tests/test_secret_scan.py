import json
import tempfile
import unittest
from pathlib import Path

from tools.secret_scan import scan


class RedactedSecretScanTests(unittest.TestCase):
    def test_finds_known_token_shapes_without_returning_values(self):
        secret = "ghp_" + "A" * 28
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config.env").write_text(f"TOKEN={secret}\n", encoding="utf-8")
            report = scan(root)

        serialized = json.dumps(report)
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["findings"][0], {
            "path": "config.env", "line": 1, "kind": "github_token"
        })
        self.assertNotIn(secret, serialized)
        self.assertTrue(report["values_redacted"])
        self.assertFalse(report["history_scanned"])

    def test_secret_assignment_matches_literals_but_not_code_references(self):
        literal = "S" * 32
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config.yml").write_text(
                f'client_secret: "{literal}"\n'
                "return json({access_token: data.session.refresh_token})\n",
                encoding="utf-8",
            )
            report = scan(root)
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["findings"][0]["kind"], "secret_assignment")
        self.assertNotIn(literal, json.dumps(report))

    def test_ignores_binary_artifact_extensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "model.joblib").write_bytes(b"ghp_" + b"B" * 28)
            report = scan(root)
        self.assertEqual(report["scanned_files"], 0)
        self.assertEqual(report["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
