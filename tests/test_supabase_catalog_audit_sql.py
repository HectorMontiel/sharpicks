import re
import unittest
from pathlib import Path


SQL_PATH = Path(__file__).resolve().parents[1] / "supabase" / "auditoria_catalogo_readonly.sql"


class SupabaseCatalogAuditSqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")
        cls.statements = [
            line.strip()
            for line in cls.sql.splitlines()
            if line.strip() and not line.lstrip().startswith("--")
        ]

    def test_audit_is_wrapped_in_read_only_transaction(self):
        self.assertEqual(self.statements[0].upper(), "BEGIN TRANSACTION READ ONLY;")
        self.assertEqual(self.statements[-1].upper(), "ROLLBACK;")

    def test_no_mutating_or_procedural_statement_is_present(self):
        forbidden = re.compile(
            r"^(?:INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE|TRUNCATE|CALL|DO)\b",
            re.IGNORECASE,
        )
        for statement in self.statements:
            self.assertIsNone(forbidden.search(statement), statement)

    def test_audit_covers_security_catalogs_without_application_rows(self):
        for expected in (
            "pg_catalog.pg_extension",
            "pg_catalog.pg_policy",
            "pg_catalog.pg_options_to_table",
            "pg_catalog.pg_proc",
            "pg_catalog.pg_trigger",
            "has_table_privilege",
            "has_sequence_privilege",
            "has_function_privilege",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.sql)
        self.assertNotRegex(self.sql, r"(?im)^\s*(?:FROM|JOIN)\s+(?!pg_catalog\.)\w+")


if __name__ == "__main__":
    unittest.main()
