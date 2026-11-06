import json
import unittest

from tools.release_asset_inventory import build_snapshot


class ReleaseAssetInventoryTests(unittest.TestCase):
    def test_snapshots_metadata_and_marks_model_archives_private_candidates(self):
        payload = {
            "tag_name": "modelos-latest",
            "name": "Modelos entrenados",
            "published_at": "2026-10-30T12:00:00Z",
            "assets": [{
                "name": "modelos-liga.tar.gz",
                "size": 120,
                "content_type": "application/x-gtar",
                "digest": "sha256:" + "a" * 64,
                "state": "uploaded",
                "created_at": "2026-10-30T12:00:00Z",
                "updated_at": "2026-10-30T12:00:00Z",
                "download_count": 3,
                "url": "https://example.invalid/download",
            }],
        }
        result = build_snapshot(payload, "org/repo", "2026-10-30T13:00:00Z")
        asset = result["assets"][0]
        self.assertEqual(result["summary"]["asset_count"], 1)
        self.assertEqual(result["summary"]["total_size_bytes"], 120)
        self.assertIn("private_candidate", asset["classification_candidates"])
        self.assertEqual(asset["digest"], "sha256:" + "a" * 64)
        self.assertEqual(asset["decision_state"], "review_required")
        self.assertNotIn("url", asset)
        self.assertNotIn("example.invalid", json.dumps(result))

    def test_reports_missing_digest_and_preserves_unclassified_asset_for_review(self):
        result = build_snapshot({"assets": [{
            "name": "notes.txt", "size": 1, "content_type": "text/plain"
        }]}, "org/repo", "fixed-time")
        self.assertEqual(result["summary"]["assets_without_digest"], 1)
        self.assertEqual(result["assets"][0]["classification_candidates"], ["review_required"])


if __name__ == "__main__":
    unittest.main()
