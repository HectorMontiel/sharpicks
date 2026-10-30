import ast
import tempfile
import unittest
from pathlib import Path

from tools.python_dependency_graph import ModuleFacts, _FactsVisitor, _cycles, _resolve_relative, _safe_path, analyze_tree


class PythonDependencyGraphTests(unittest.TestCase):
    def test_relative_import_resolution(self):
        self.assertEqual(_resolve_relative("pkg.sub.mod", False, 1, "helpers"), "pkg.sub.helpers")
        self.assertEqual(_resolve_relative("pkg.sub.mod", False, 2, "helpers"), "pkg.helpers")
        self.assertEqual(_resolve_relative("pkg.mod", False, 3, "helpers"), "")

    def test_ast_finds_nested_local_and_dynamic_imports_and_side_effects(self):
        source = """
import pkg.local
from . import sibling
import importlib
import importlib.util

def call_later():
    import pkg.nested
    importlib.import_module(name)
    importlib.util.spec_from_file_location('runtime', plugin_path)
    open('inside.csv')

os.getenv('API_KEY')
os.environ['BOT_TOKEN']
open('data.csv')
subprocess.run(['python', 'job.py'])
"""
        facts = ModuleFacts(path="pkg/mod.py", module="pkg.mod")
        index = {"pkg.local": ["pkg/local.py"], "pkg.nested": ["pkg/nested.py"], "pkg": ["pkg/__init__.py"], "pkg.sibling": ["pkg/sibling.py"]}
        _FactsVisitor(facts, index, False).visit(ast.parse(source))
        self.assertEqual({item["target"] for item in facts.imports}, {"pkg.local", "pkg", "pkg.sibling", "pkg.nested"})
        self.assertEqual(len(facts.dynamic_imports), 2)
        self.assertEqual({"API_KEY", "BOT_TOKEN"}, {item["name"] for item in facts.environment_variables})
        self.assertTrue(any(item.get("path") == "data.csv" for item in facts.file_references))
        self.assertEqual(len(facts.subprocess_calls), 1)
        self.assertTrue(any(item["call"] == "open" for item in facts.top_level_calls))

    def test_cycle_detection_reports_strongly_connected_component(self):
        cycles = _cycles({"a", "b", "c", "isolated"}, [("a", "b"), ("b", "a"), ("b", "c")])
        self.assertEqual(cycles, [["a", "b"]])

    def test_report_does_not_copy_command_or_dynamic_code_arguments(self):
        source = "exec('DO_NOT_COPY_SECRET_LITERAL')\nsubprocess.run(['worker', '--token', 'DO_NOT_COPY_SECRET_LITERAL'])\n"
        facts = ModuleFacts(path="entry.py", module="entry")
        _FactsVisitor(facts, {}, False).visit(ast.parse(source))
        serialized = str(facts.__dict__)
        self.assertNotIn("DO_NOT_COPY_SECRET_LITERAL", serialized)
        self.assertTrue(facts.dynamic_imports)
        self.assertTrue(facts.subprocess_calls)
        self.assertEqual(facts.subprocess_calls[0]["executable_kind"], "other")

    def test_path_redaction_hides_remote_query_and_recognizable_tokens(self):
        self.assertEqual(_safe_path("https://user:pass@example.test/data.csv?token=value"), "<remote-url-redacted>")
        safe = _safe_path("artifacts/ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456")
        self.assertNotIn("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456", safe)

    def test_tree_analysis_resolves_transitive_local_imports_without_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pkg").mkdir()
            (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            (root / "pkg" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "entry.py").write_text("from pkg import core\nif __name__ == '__main__':\n    print(core.VALUE)\n", encoding="utf-8")
            report = analyze_tree(root)
            self.assertEqual(report["summary"]["python_files"], 3)
            self.assertEqual(report["summary"]["resolved_import_edges"], 2)
            self.assertEqual(report["entrypoints"][0]["path"], "entry.py")
            self.assertIn("pkg.core", report["entrypoints"][0]["transitive_modules"])


if __name__ == "__main__":
    unittest.main()
