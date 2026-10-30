from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import publicar_modelos as publisher


class PrivateModelPublisherTests(unittest.TestCase):
    def test_missing_destination_fails_before_gh_or_model_scan(self):
        with patch.object(publisher, "REPO", ""), \
                patch.object(publisher, "_gh") as gh, \
                patch.object(publisher, "competiciones") as scan:
            self.assertEqual(publisher.publicar(), 2)
        gh.assert_not_called()
        scan.assert_not_called()

    def test_public_sharpicks_repository_is_never_a_publish_target(self):
        with patch.object(publisher, "REPO", "HectorMontiel/sharpicks"), \
                patch.object(publisher, "_gh") as gh:
            with self.assertRaisesRegex(ValueError, "repositorio público"):
                publisher._validar_destino_privado()
        gh.assert_not_called()

    def test_unknown_or_public_repository_is_rejected(self):
        for repo_response in ('{"private": false}', '{"private": null}'):
            with self.subTest(repo_response=repo_response), \
                    patch.object(publisher, "REPO", "HectorMontiel/sharpicks-core"), \
                    patch.object(publisher, "_gh", return_value=SimpleNamespace(stdout=repo_response)):
                with self.assertRaisesRegex(ValueError, "no es un repositorio privado"):
                    publisher._validar_destino_privado()

    def test_private_repository_metadata_is_required_before_publish(self):
        with patch.object(publisher, "REPO", "HectorMontiel/sharpicks-core"), \
                patch.object(publisher, "_gh", return_value=SimpleNamespace(stdout='{"private": true}')) as gh:
            publisher._validar_destino_privado()
        gh.assert_called_once_with("api", "repos/HectorMontiel/sharpicks-core")

    def test_workflow_never_stages_models_after_failed_publication(self):
        workflow = Path(".github/workflows/retrain_leagues.yml").read_text(encoding="utf-8")
        self.assertIn("REPO_MODELOS: ${{ vars.REPO_MODELOS }}", workflow)
        self.assertIn("GH_TOKEN: ${{ secrets.CORE_RELEASE_TOKEN }}", workflow)
        self.assertIn("vars.MODELOS_CORE_CONSUMERS_READY == 'true'", workflow)
        self.assertIn("MODELOS_CORE_LISTOS_PARA_CORTE: ${{ steps.publicar.outcome == 'success' && vars.MODELOS_CORE_CONSUMERS_READY == 'true' }}", workflow)
        self.assertIn('if [ "$MODELOS_CORE_LISTOS_PARA_CORTE" = "true" ]; then', workflow)
        self.assertIn("se omiten modelos/ y .gitignore", workflow)


if __name__ == "__main__":
    unittest.main()
