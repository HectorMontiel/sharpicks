import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.asset_inventory import _classify, build_inventory


class AssetInventoryTests(unittest.TestCase):
    def test_classification_is_candidate_only_and_overlapping(self):
        classes, evidence = _classify("modelos/modelo_tda.joblib")
        self.assertEqual(
            classes,
            ["generated", "private_candidate", "review_required"],
        )
        self.assertIn("model artifact", evidence)

    def test_historical_csv_requires_review(self):
        classes, _ = _classify("historico_partidos.csv")
        self.assertIn("historical", classes)
        self.assertIn("private_candidate", classes)
        self.assertIn("review_required", classes)

    def test_contract_can_be_shared_without_auto_approval(self):
        classes, _ = _classify("sharpicks_contracts/v1.py")
        self.assertIn("shareable_contract_candidate", classes)
        self.assertIn("review_required", classes)

    def test_git_tree_inventory_includes_sparse_omitted_blob_without_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "tracked.txt").write_text("tree content", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "fixture"],
                cwd=root,
                check=True,
            )
            (root / "tracked.txt").unlink()
            inventory = build_inventory(root, "HEAD")
            self.assertEqual(inventory["summary"]["tracked_blobs"], 1)
            self.assertEqual(len(inventory["revision"]), 40)
            self.assertEqual(inventory["revision_requested"], "HEAD")
            self.assertEqual(inventory["assets"][0]["path"], "tracked.txt")
            self.assertGreater(inventory["assets"][0]["size_bytes"], 0)

    def test_json_serialization_contains_no_file_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "private.csv").write_text("DO_NOT_COPY_CONTENT", encoding="utf-8")
            subprocess.run(["git", "add", "private.csv"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "fixture"],
                cwd=root,
                check=True,
            )
            report = json.dumps(build_inventory(root, "HEAD"))
            self.assertNotIn("DO_NOT_COPY_CONTENT", report)


if __name__ == "__main__":
    unittest.main()
