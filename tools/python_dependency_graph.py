"""Static, non-executing Python dependency and side-effect inventory.

The output is evidence for review, not a complete runtime call graph. The
analyzer deliberately records constructs it cannot resolve rather than
importing project modules or executing any project code.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}
SUBPROCESS_CALLS = {"run", "call", "Popen", "check_call", "check_output"}
FILE_READ_CALLS = {
    "open", "read_csv", "read_json", "read_pickle", "read_parquet", "read_excel",
    "read_text", "read_bytes", "load", "loadtxt", "genfromtxt", "load_workbook",
}
FILE_WRITE_CALLS = {
    "to_csv", "to_json", "to_pickle", "to_parquet", "to_excel", "write_text",
    "write_bytes", "dump", "savefig", "save", "write",
}
ENV_ATTRS = {"getenv"}
WORKFLOW_PYTHON = re.compile(r"(?m)^\s*(?:python|python3(?:\.\d+)?)\s+([^\s\\]+\.py)(?:\s|$)")
RESPONSIBILITY_HINTS = {
    "core_predictive": ("predict", "prediction", "engine", "motor", "selector", "scor", "alpha_finder", "edge_engine"),
    "data_ingestion": ("scraper", "scrape", "ingest", "fetch", "actualizar", "fuente", "backfill", "historico"),
    "odds_and_markets": ("odds", "cuota", "market", "mercado", "linea", "lines"),
    "statistics": ("stats", "statistic", "estadistica", "data_health"),
    "machine_learning": ("model", "modelo", "feature", "train", "entren", "calibr", "ensemble", "inferencia"),
    "evaluation_and_backtesting": ("backtest", "ledger", "resultado", "evaluacion", "evaluation", "recalib", "autopsia"),
    "pick_management": ("pick", "apuesta", "seleccion", "liquidar", "pronostico"),
    "integrations": ("supabase", "telegram", "webhook", "cloudflare", "stripe", "mercadopago", "brevo"),
    "presentation": ("web", "export", "streamlit", "frontend", "vista", "tablas_web"),
    "automation": ("job", "cron", "pipeline", "workflow", "relevo", "bot_"),
    "observability": ("radar", "monitor", "alert", "vigia", "health", "metric"),
    "configuration": ("config", "settings", "environment", "secret"),
    "testing": ("test", "smoke", "fixture", "mock"),
}


@dataclass
class ModuleFacts:
    path: str
    module: str
    imports: list[dict[str, Any]] = field(default_factory=list)
    unresolved_imports: list[dict[str, Any]] = field(default_factory=list)
    dynamic_imports: list[dict[str, Any]] = field(default_factory=list)
    subprocess_calls: list[dict[str, Any]] = field(default_factory=list)
    file_references: list[dict[str, Any]] = field(default_factory=list)
    environment_variables: list[dict[str, Any]] = field(default_factory=list)
    top_level_calls: list[dict[str, Any]] = field(default_factory=list)
    has_main_guard: bool = False
    syntax_error: str | None = None
    responsibility_hints: list[str] = field(default_factory=list)


def _module_name(path: Path) -> str:
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _constant_string(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _safe_path(value: str) -> str:
    # File-like APIs can also accept remote URLs; never copy their query strings
    # or userinfo into a public audit report.
    if "://" in value:
        return "<remote-url-redacted>"
    value = value.split("?", 1)[0].split("#", 1)[0]
    value = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|sk_(?:live|test)_[A-Za-z0-9]{16,})\b", "[REDACTED]", value)
    return re.sub(
        r"(?i)(token|secret|password|api[_-]?key|authorization)([=/ :]+)[^/&?\s]+",
        r"\1\2[REDACTED]",
        value,
    )


def _literal_value(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = _call_name(node.value)
        return f"{head}.{node.attr}" if head else node.attr
    return ""


def _executable_kind(name: str) -> str:
    if name in {"python", "python2", "python3", "python3.12", "pypy", "pypy3"}:
        return "python"
    if name in {"sh", "bash", "zsh", "cmd", "powershell", "pwsh"}:
        return "shell"
    if name in {"node", "deno", "npm", "npx"}:
        return "javascript-runtime"
    if name == "git":
        return "git"
    return "other" if name else "dynamic"


def _resolve_relative(module: str, is_package: bool, level: int, imported: str | None) -> str:
    components = module.split(".") if module else []
    package = components if is_package else components[:-1]
    keep = len(package) - (level - 1)
    if keep < 0:
        return ""
    base = package[:keep]
    suffix = imported.split(".") if imported else []
    return ".".join(base + suffix)


def _has_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and _constant_string(test.comparators[0]) == "__main__"
    )


class _FactsVisitor(ast.NodeVisitor):
    def __init__(self, facts: ModuleFacts, module_index: dict[str, list[str]], is_package: bool):
        self.facts = facts
        self.module_index = module_index
        self.is_package = is_package
        self.scope_depth = 0

    def _resolve(self, name: str, node: ast.AST, kind: str, text: str) -> None:
        if not name:
            self.facts.unresolved_imports.append({"line": node.lineno, "kind": kind, "name": text, "reason": "relative import escaped package root"})
            return
        matches = self.module_index.get(name, [])
        if matches:
            for path in matches:
                self.facts.imports.append({"line": node.lineno, "target": name, "path": path, "kind": kind, "text": text})
        else:
            self.facts.unresolved_imports.append({"line": node.lineno, "kind": kind, "name": name, "text": text})

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._resolve(alias.name, node, "import", alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = node.module or ""
        if node.level:
            base = _resolve_relative(self.facts.module, self.is_package, node.level, base)
        if base:
            self._resolve(base, node, "from", node.module or "." * node.level)
        elif node.level:
            self._resolve("", node, "from", node.module or "." * node.level)
        for alias in node.names:
            if alias.name == "*":
                continue
            child = f"{base}.{alias.name}" if base else alias.name
            if child in self.module_index:
                self._resolve(child, node, "from-submodule", child)

    def visit_If(self, node: ast.If) -> None:
        if _has_main_guard(node):
            self.facts.has_main_guard = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for item in [*node.decorator_list, *node.args.defaults, *[x for x in node.args.kw_defaults if x is not None]]:
            self.visit(item)
        self.scope_depth += 1
        for item in node.body:
            self.visit(item)
        self.scope_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for item in [*node.decorator_list, *node.bases, *[keyword.value for keyword in node.keywords]]:
            self.visit(item)
        # Class bodies execute during import, so they remain at top-level scope.
        for item in node.body:
            self.visit(item)

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        leaf = name.rsplit(".", 1)[-1]
        line = node.lineno

        if name in {"importlib.import_module", "__import__"}:
            module_name = _constant_string(node.args[0]) if node.args else None
            if module_name:
                if module_name.startswith("."):
                    package = _constant_string(node.args[1]) if len(node.args) > 1 else None
                    if package:
                        resolved = _resolve_relative(package, True, len(module_name) - len(module_name.lstrip(".")), module_name.lstrip("."))
                        self._resolve(resolved, node, "dynamic-relative", module_name)
                    else:
                        self.facts.dynamic_imports.append({"line": line, "call": name, "reason": "relative import has no literal package"})
                else:
                    self._resolve(module_name, node, "dynamic", module_name)
            else:
                self.facts.dynamic_imports.append({"line": line, "call": name, "reason": "module name is not a literal string"})

        if (name.startswith("subprocess.") and leaf in SUBPROCESS_CALLS) or name in {"os.system", "os.popen"}:
            command = _literal_value(node.args[0]) if node.args else None
            executable_kind = "dynamic"
            if isinstance(command, str):
                executable = Path(command.strip().split(maxsplit=1)[0]).name.lower() if command.strip() else ""
                executable_kind = _executable_kind(executable)
            elif isinstance(command, (list, tuple)) and command and isinstance(command[0], str):
                executable_kind = _executable_kind(Path(command[0]).name.lower())
            self.facts.subprocess_calls.append({"line": line, "call": name, "executable_kind": executable_kind, "command_is_literal": command is not None})
        if name == "runpy.run_module":
            module_name = _constant_string(node.args[0]) if node.args else None
            if module_name:
                self._resolve(module_name, node, "runpy", module_name)
            else:
                self.facts.dynamic_imports.append({"line": line, "call": name, "reason": "runpy module name is not a literal"})
        elif name == "runpy.run_path":
            value = _constant_string(node.args[0]) if node.args else None
            self.facts.dynamic_imports.append({"line": line, "call": name, "target": _safe_path(value) if value else None, "reason": "dynamic execution or path-based module loading"})
        elif name in {"exec", "eval"}:
            self.facts.dynamic_imports.append({"line": line, "call": name, "reason": "dynamic code execution"})
        elif name.startswith("importlib.") and leaf in {"spec_from_file_location", "module_from_spec", "exec_module", "find_spec"}:
            self.facts.dynamic_imports.append({"line": line, "call": name, "reason": "importlib runtime discovery or loading"})

        if name in {"os.getenv", "os.environ.get"}:
            env_name = _constant_string(node.args[0]) if node.args else None
            self.facts.environment_variables.append({"line": line, "name": env_name, "source": name})
        if leaf in FILE_READ_CALLS | FILE_WRITE_CALLS or name in {"Path.open", "io.open"}:
            arg = node.args[0] if node.args else None
            literal = _constant_string(arg)
            mode = "write" if leaf in FILE_WRITE_CALLS or (name in {"open", "io.open"} and len(node.args) > 1 and (_constant_string(node.args[1]) or "r").startswith(("w", "a", "x"))) else "read"
            if literal is not None:
                self.facts.file_references.append({"line": line, "mode": mode, "api": name, "path": _safe_path(literal)})
            elif leaf in FILE_READ_CALLS | FILE_WRITE_CALLS:
                self.facts.file_references.append({"line": line, "mode": mode, "api": name, "path": None})

        if self.scope_depth == 0:
            self.facts.top_level_calls.append({"line": line, "call": name or "<dynamic-call>"})
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _call_name(node.value) == "os.environ":
            self.facts.environment_variables.append({
                "line": node.lineno,
                "name": _constant_string(node.slice),
                "expression": ast.unparse(node)[:200],
            })
        self.generic_visit(node)


def _module_index(files: list[Path], root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for path in files:
        rel = path.relative_to(root)
        name = _module_name(rel)
        if name:
            index[name].append(rel.as_posix())
    return {name: sorted(paths) for name, paths in index.items()}


def _responsibility_hints(path: str) -> list[str]:
    """Return weak filename/path hints only; never infer an authoritative owner."""
    lowered = path.lower()
    return [
        category
        for category, tokens in RESPONSIBILITY_HINTS.items()
        if any(token in lowered for token in tokens)
    ]


def _declared_import_roots(root: Path) -> set[str]:
    """Approximate direct import roots declared by requirements.txt."""
    path = root / "requirements.txt"
    if not path.exists():
        return set()
    aliases = {
        "scikit-learn": "sklearn",
        "beautifulsoup4": "bs4",
        "pillow": "PIL",
        "pyyaml": "yaml",
    }
    roots: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", line)
        if not match or line.lstrip().startswith(("#", "-")):
            continue
        distribution = match.group(1).lower().replace("_", "-")
        roots.add(aliases.get(distribution, distribution.replace("-", "_")))
    return roots


def _collect_workflow_scripts(root: Path, known_paths: set[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return {}
    for path in sorted(workflow_dir.glob("*.y*ml")):
        content = path.read_text(encoding="utf-8", errors="replace")
        for match in WORKFLOW_PYTHON.finditer(content):
            script = Path(match.group(1)).as_posix()
            found[script].append(path.relative_to(root).as_posix())
    return {script: sorted(set(workflows)) for script, workflows in found.items() if script in known_paths}


def _cycles(nodes: set[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        adjacency[source].append(target)
    index = 0
    indexes: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    components: list[list[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indexes[node] = lowlink[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for target in adjacency[node]:
            if target not in indexes:
                strongconnect(target)
                lowlink[node] = min(lowlink[node], lowlink[target])
            elif target in active:
                lowlink[node] = min(lowlink[node], indexes[target])
        if lowlink[node] == indexes[node]:
            component: list[str] = []
            while True:
                item = stack.pop()
                active.remove(item)
                component.append(item)
                if item == node:
                    break
            if len(component) > 1 or any(s == node and t == node for s, t in edges):
                components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indexes:
            strongconnect(node)
    return sorted(components)


def _reachable(start: str, adjacency: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    queue = deque(adjacency.get(start, []))
    while queue:
        item = queue.popleft()
        if item in seen:
            continue
        seen.add(item)
        queue.extend(adjacency.get(item, []))
    return sorted(seen)


def analyze_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = sorted(path for path in root.rglob("*.py") if not (set(path.relative_to(root).parts) & SKIP_DIRS))
    index = _module_index(files, root)
    facts: list[ModuleFacts] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        module = _module_name(Path(rel))
        item = ModuleFacts(path=rel, module=module, responsibility_hints=_responsibility_hints(rel))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=rel)
            _FactsVisitor(item, index, path.name == "__init__.py").visit(tree)
        except SyntaxError as exc:
            item.syntax_error = f"line {exc.lineno}: {exc.msg}"
        facts.append(item)

    modules = {item.module for item in facts if item.module}
    edges = sorted({(item.module, imp["target"]) for item in facts for imp in item.imports if item.module})
    adjacency: dict[str, list[str]] = defaultdict(list)
    incoming: Counter[str] = Counter()
    for source, target in edges:
        adjacency[source].append(target)
        incoming[target] += 1

    path_to_module = {item.path: item.module for item in facts}
    known_paths = set(path_to_module)
    workflow_scripts = _collect_workflow_scripts(root, known_paths)
    main_paths = sorted(item.path for item in facts if item.has_main_guard)
    entry_paths = sorted(set(main_paths) | set(workflow_scripts))
    entrypoints: list[dict[str, Any]] = []
    for path in entry_paths:
        module = path_to_module.get(path, "")
        entrypoints.append({
            "path": path,
            "module": module,
            "source": "workflow" if path in workflow_scripts else "__main__ guard",
            "workflows": workflow_scripts.get(path, []),
            "transitive_modules": _reachable(module, adjacency) if module else [],
        })

    duplicates = {name: paths for name, paths in index.items() if len(paths) > 1}
    declared_roots = _declared_import_roots(root)
    unresolved_roots: Counter[str] = Counter()
    unresolved_classes: Counter[str] = Counter()
    for module_fact in facts:
        for unresolved in module_fact.unresolved_imports:
            name = unresolved.get("name", "")
            root_name = name.split(".", 1)[0]
            unresolved_roots[root_name] += 1
            if root_name in sys.stdlib_module_names:
                unresolved_classes["stdlib"] += 1
            elif root_name in declared_roots:
                unresolved_classes["declared_direct_dependency"] += 1
            else:
                unresolved_classes["optional_or_unclassified"] += 1
    summary = {
        "python_files": len(files),
        "modules": len(modules),
        "resolved_import_edges": len(edges),
        "unresolved_import_statements": sum(len(item.unresolved_imports) for item in facts),
        "dynamic_import_or_execution_sites": sum(len(item.dynamic_imports) for item in facts),
        "subprocess_sites": sum(len(item.subprocess_calls) for item in facts),
        "file_reference_sites": sum(len(item.file_references) for item in facts),
        "environment_access_sites": sum(len(item.environment_variables) for item in facts),
        "top_level_call_sites": sum(len(item.top_level_calls) for item in facts),
        "syntax_errors": sum(item.syntax_error is not None for item in facts),
        "duplicate_module_names": len(duplicates),
        "cyclic_components": 0,
        "entrypoints": len(entrypoints),
        "workflow_script_paths": len(workflow_scripts),
        "unresolved_stdlib_imports": unresolved_classes["stdlib"],
        "unresolved_declared_dependency_imports": unresolved_classes["declared_direct_dependency"],
        "unresolved_other_imports": unresolved_classes["optional_or_unclassified"],
    }
    hint_counts: Counter[str] = Counter(hint for item in facts for hint in item.responsibility_hints)
    summary["modules_without_responsibility_hints"] = sum(not item.responsibility_hints for item in facts)
    cycle_list = _cycles(modules, edges)
    summary["cyclic_components"] = len(cycle_list)
    try:
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    return {
        "schema_version": 1,
        "repository_revision": revision,
        "summary": summary,
        "module_collisions": duplicates,
        "cycles": cycle_list,
        "top_incoming_modules": [{"module": name, "count": count} for name, count in incoming.most_common(30)],
        "top_unresolved_import_roots": [{"root": name, "count": count} for name, count in unresolved_roots.most_common(50)],
        "declared_direct_import_roots": sorted(declared_roots),
        "responsibility_hint_counts": dict(sorted(hint_counts.items())),
        "workflow_scripts": workflow_scripts,
        "entrypoints": entrypoints,
        "modules": [item.__dict__ for item in facts],
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Resultado del grafo estático de imports Python",
        "",
        f"- **SHA analizado:** `{report.get('repository_revision') or 'no disponible'}`",
        "- **Estado:** OBSERVADO; análisis estático, no grafo de ejecución completo.",
        "- **Método:** AST de archivos Python; no importa ni ejecuta SharPicks.",
        "",
        "## Métricas",
        "",
        "| Medida | Resultado |",
        "|---|---:|",
    ]
    labels = {
        "python_files": "Archivos Python",
        "modules": "Módulos/nombres de módulo",
        "resolved_import_edges": "Aristas locales resueltas",
        "unresolved_import_statements": "Import statements no resueltos localmente",
        "unresolved_stdlib_imports": "No locales de biblioteca estándar",
        "unresolved_declared_dependency_imports": "No locales de dependencias directas declaradas",
        "unresolved_other_imports": "No locales opcionales/no clasificados",
        "dynamic_import_or_execution_sites": "Sitios de import/evaluación dinámica",
        "subprocess_sites": "Llamadas a subprocess/os.system",
        "file_reference_sites": "Referencias estáticas a archivos",
        "environment_access_sites": "Lecturas candidatas de entorno",
        "top_level_call_sites": "Llamadas candidatas durante import",
        "syntax_errors": "Errores de parseo AST",
        "duplicate_module_names": "Nombres de módulo duplicados",
        "cyclic_components": "Componentes cíclicos",
        "entrypoints": "Entry points con __main__ o workflow",
        "workflow_script_paths": "Scripts Python llamados literalmente por workflow",
        "modules_without_responsibility_hints": "Módulos sin pista heurística por nombre/ruta",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {summary[key]} |")
    lines += ["", "Las etiquetas siguientes son pistas heurísticas por nombre/ruta; requieren confirmación por imports, I/O y efectos reales.", "", "| Pista de responsabilidad | Módulos/archivos coincidentes |", "|---|---:|"]
    for category, count in report["responsibility_hint_counts"].items():
        lines.append(f"| `{category}` | {count} |")
    lines += ["", "## Entry points detectados", "", "| Archivo | Descubrimiento | Workflows | Módulos transitivos resueltos |", "|---|---|---|---:|"]
    for entry in report["entrypoints"]:
        workflows = ", ".join(f"`{name}`" for name in entry["workflows"]) or "—"
        lines.append(f"| `{entry['path']}` | {entry['source']} | {workflows} | {len(entry['transitive_modules'])} |")
    lines += [
        "",
        "El conteo de `__main__ guard` incluye scripts históricos, pruebas y herramientas de análisis; no significa que todos estén activos en producción. Los 44 scripts de workflows son los comandos literales que el analizador pudo asociar a los 18 YAML.",
    ]
    lines += ["", "## Módulos con mayor cantidad de importadores", "", "| Módulo | Importadores locales |", "|---|---:|"]
    for item in report["top_incoming_modules"][:20]:
        lines.append(f"| `{item['module']}` | {item['count']} |")
    lines += ["", "## Raíces de imports que no resuelven a archivo local", "", "| Raíz | Referencias |", "|---|---:|"]
    for item in report["top_unresolved_import_roots"][:30]:
        lines.append(f"| `{item['root']}` | {item['count']} |")
    lines += ["", "## Componentes cíclicos", ""]
    if report["cycles"]:
        for component in report["cycles"]:
            lines.append("- " + ", ".join(f"`{name}`" for name in component))
    else:
        lines.append("No se detectaron ciclos en las aristas locales resueltas.")
    lines += [
        "",
        "## Limitaciones",
        "",
        "- Un import no resuelto puede ser biblioteca estándar, dependencia de terceros, import relativo especial, paquete namespace o dependencia opcional; no se etiqueta automáticamente como error.",
        "- Imports dinámicos con valor calculado, plugins, rutas por configuración y ejecución shell sólo quedan marcados, no resueltos transitivamente.",
        "- Referencias de archivo son strings literales/calls conocidos; no demuestran I/O real ni distinguen con certeza datos de rutas de URL/identificadores.",
        "- Llamadas top-level son candidatas observadas sintácticamente; no prueban que el módulo se importe ni el efecto externo exacto.",
        "- Los entrypoints por workflow se detectan para comandos `python <archivo.py>` literales; comandos construidos, módulos `-m` y scripts descargados requieren revisión adicional.",
        "- No se ejecutó ningún módulo de SharPicks ni se contactaron servicios.",
        "",
        "El detalle reproducible por módulo, líneas, aristas y sitios pendientes está en `python_dependency_graph.json`.",
        "Reproducir con `python tools/python_dependency_graph.py --json docs/auditoria/python_dependency_graph.json --markdown docs/auditoria/01_GRAFO_ARQUITECTURA.md`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=Path("docs/auditoria/python_dependency_graph.json"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/auditoria/01_GRAFO_ARQUITECTURA.md"))
    args = parser.parse_args()
    report = analyze_tree(args.root)
    json_path = args.root / args.json
    md_path = args.root / args.markdown
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
