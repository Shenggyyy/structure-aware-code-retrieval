"""Conservative syntactic relations from a saved snapshot, never executing source."""

import ast
import io
import json
import os
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import Symbol, stable_id

RELATION_TYPES = ("containment", "import", "call", "test")
RESOLVER_CONFIG = {"version": 1, "import_roots": [".", "src"], "max_alias_hops": 12}


@dataclass(frozen=True)
class Relation:
    source: str
    target: str
    kind: str
    confidence: str
    path: str
    line: int
    expression: str

    @property
    def id(self) -> str:
        return stable_id(asdict(self))


@dataclass(frozen=True)
class RelationGraph:
    metadata: dict
    edges: tuple[Relation, ...]
    unresolved: tuple[dict, ...]


def graph_binding(index: LoadedIndex) -> dict:
    return {
        "snapshot_id": index.metadata["snapshot_id"],
        "content_hash": stable_id(
            [asdict(index.symbols[key]) for key in sorted(index.symbols)],
            [asdict(chunk) for chunk in index.chunks],
        ),
        "resolver": RESOLVER_CONFIG,
    }


def is_test(path: str) -> bool:
    value = PurePosixPath(path)
    return "tests" in value.parts or value.name.startswith("test_") or value.stem.endswith("_test")


def snapshot_sources(index: LoadedIndex) -> dict[str, str]:
    """Reconstruct line positions; omitted whitespace-only spans become blank lines."""
    files = {
        symbol.path: ["\n"] * symbol.end_line
        for symbol in index.symbols.values()
        if symbol.kind == "module"
    }
    occupied: set[tuple[str, int]] = set()
    for chunk in index.chunks:
        lines = io.StringIO(chunk.text).readlines()
        if len(lines) != chunk.end_line - chunk.start_line + 1 or chunk.path not in files:
            raise ValueError("Invalid chunk source range for relation extraction")
        for number, line in enumerate(lines, chunk.start_line):
            if (chunk.path, number) in occupied or number > len(files[chunk.path]):
                raise ValueError("Overlapping or out-of-bounds source chunks")
            occupied.add((chunk.path, number))
            files[chunk.path][number - 1] = line if line.endswith("\n") else line + "\n"
    return {path: "".join(lines) for path, lines in files.items()}


class _Resolver:
    def __init__(self, index: LoadedIndex) -> None:
        self.index = index
        self.symbols = index.symbols
        self.modules: dict[str, set[str]] = defaultdict(set)
        self.scopes: dict[str, dict[str, set[tuple[str, str]]]] = {
            key: defaultdict(set) for key in self.symbols
        }
        self.wildcards: set[str] = set()
        self.calls: list[tuple[str, ast.Call]] = []
        self.imports: list[tuple[str, str, int]] = []
        self.receivers: dict[str, str] = {}
        self.nodes = {
            (symbol.path, symbol.name, symbol.start_line, symbol.end_line): symbol.id
            for symbol in self.symbols.values()
            if symbol.kind != "module"
        }
        self.by_path = {
            symbol.path: symbol for symbol in self.symbols.values() if symbol.kind == "module"
        }
        for path, module in self.by_path.items():
            names = [module.qualified_name]
            if path.startswith("src/"):
                names.append(module.qualified_name.removeprefix("src."))
            for name in names:
                self.modules[name].add(module.id)
        for path, text in snapshot_sources(index).items():
            self.collect(ast.parse(text, filename=path), self.by_path[path])

    def bind(self, owner: Symbol, name: str, kind: str, value: str = "") -> None:
        if self.receivers.get(owner.id) == name:
            self.receivers.pop(owner.id)
        self.scopes[owner.id][name].add((kind, value))

    def import_base(self, owner: Symbol, node: ast.ImportFrom) -> str:
        module = self.by_path[owner.path].qualified_name
        if owner.path.startswith("src/"):
            module = module.removeprefix("src.")
        if not node.level:
            return node.module or ""
        package = (
            module.split(".")
            if PurePosixPath(owner.path).name == "__init__.py"
            else module.split(".")[:-1]
        )
        if node.level > len(package):
            return "__unresolved_relative_import__"
        prefix = package[: len(package) - node.level + 1]
        return ".".join([*prefix, *([node.module] if node.module else [])])

    def collect(self, node: ast.AST, owner: Symbol) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            start = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            key = (owner.path, node.name, start, node.end_lineno)
            if key not in self.nodes:
                raise ValueError("AST definitions do not match indexed symbols")
            child = self.symbols[self.nodes[key]]
            self.bind(owner, node.name, "symbol", child.id)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                arguments += [arg for arg in (node.args.vararg, node.args.kwarg) if arg]
                for argument in arguments:
                    self.bind(child, argument.arg, "blocked")
                positional = [*node.args.posonlyargs, *node.args.args]
                static = any(
                    isinstance(item, ast.Name) and item.id == "staticmethod"
                    for item in node.decorator_list
                )
                if (
                    child.kind == "method"
                    and not static
                    and positional
                    and positional[0].arg in {"self", "cls"}
                ):
                    self.receivers[child.id] = positional[0].arg
            # Decorator/default/annotation/base expressions are deliberately not call edges.
            for statement in node.body:
                self.collect(statement, child)
            return
        if isinstance(node, ast.Lambda):
            return  # Lambda scopes have no indexed symbol; do not invent an owner/binding.
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.bind(
                    owner,
                    alias.asname or alias.name.split(".")[0],
                    "import",
                    alias.name if alias.asname else alias.name.split(".")[0],
                )
                self.imports.append((owner.id, alias.name, node.lineno))
            return
        if isinstance(node, ast.ImportFrom):
            base = self.import_base(owner, node)
            for alias in node.names:
                reference = ".".join(part for part in (base, alias.name) if part)
                if alias.name == "*":
                    self.wildcards.add(owner.id)
                else:
                    self.bind(owner, alias.asname or alias.name, "import", reference)
                self.imports.append((owner.id, reference, node.lineno))
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del):
            self.bind(owner, node.id, "blocked")
            if self.receivers.get(owner.id) == node.id:
                self.receivers.pop(owner.id)
        elif isinstance(node, ast.Global | ast.Nonlocal):
            for name in node.names:
                self.bind(owner, name, "blocked")
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar) and node.name:
            self.bind(owner, node.name, "blocked")
        elif isinstance(node, ast.MatchMapping) and node.rest:
            self.bind(owner, node.rest, "blocked")
        elif isinstance(node, ast.Call):
            self.calls.append((owner.id, node))
        for child in ast.iter_child_nodes(node):
            self.collect(child, owner)

    def binding(self, scope: str, name: str) -> tuple[str, str]:
        candidates = self.scopes[scope].get(name, set())
        if any(kind == "blocked" for kind, _ in candidates):
            return "error", "shadowed_or_dynamic_binding"
        if len(candidates) > 1:
            return "error", "ambiguous_binding"
        if scope in self.wildcards:
            return "error", "wildcard_import"
        return next(iter(candidates), ("error", "unknown_name"))

    def resolve_path(self, path: str, seen: tuple[str, ...] = ()) -> tuple[str | None, str]:
        if path in seen or len(seen) >= RESOLVER_CONFIG["max_alias_hops"]:
            return None, "alias_cycle_or_depth"
        parts = path.split(".")
        if any(
            len(self.modules.get(".".join(parts[:n]), set())) > 1 for n in range(1, len(parts) + 1)
        ):
            return None, "ambiguous_module"
        for length in range(len(parts), 0, -1):
            modules = self.modules.get(".".join(parts[:length]), set())
            if len(modules) > 1:
                return None, "ambiguous_module"
            if modules:
                parent_modules = self.modules.get(".".join(parts[: length - 1]), set())
                if parent_modules:
                    parent = next(iter(parent_modules))
                    binding = self.scopes[parent].get(parts[length - 1], set())
                    if binding and binding != {("import", ".".join(parts[:length]))}:
                        return None, "module_attribute_shadowed"
                return self.members(next(iter(modules)), parts[length:], (*seen, path))
        return None, "external_or_missing_module"

    def members(
        self, target: str, parts: list[str], seen: tuple[str, ...]
    ) -> tuple[str | None, str]:
        if not parts:
            return target, "static"
        if self.symbols[target].kind not in {"module", "class"}:
            return None, "dynamic_receiver"
        kind, value = self.binding(target, parts[0])
        return self.follow(kind, value, parts[1:], seen)

    def follow(
        self, kind: str, value: str, parts: list[str], seen: tuple[str, ...]
    ) -> tuple[str | None, str]:
        if kind == "symbol":
            return self.members(value, parts, seen)
        if kind == "import":
            return self.resolve_path(".".join([value, *parts]), seen)
        return None, value

    def resolve_call(self, owner: str, node: ast.Call) -> tuple[str | None, str]:
        expression = node.func
        parts = []
        while isinstance(expression, ast.Attribute):
            parts.insert(0, expression.attr)
            expression = expression.value
        if not isinstance(expression, ast.Name):
            return None, "dynamic_receiver"
        name = expression.id
        if self.receivers.get(owner) == name and parts:
            parent = self.symbols[owner].parent_id
            assert parent is not None
            target, reason = self.members(parent, parts, ())
            return (target, "heuristic") if target else (None, reason)
        scope: str | None = owner
        while scope is not None:
            symbol = self.symbols[scope]
            # Method/free-variable name lookup skips the class namespace.
            if symbol.kind != "class" or scope == owner:
                if name in self.scopes[scope] or scope in self.wildcards:
                    kind, value = self.binding(scope, name)
                    return self.follow(kind, value, parts, ())
            scope = symbol.parent_id
        return None, "unknown_name"


def extract_graph(index: LoadedIndex) -> RelationGraph:
    start = time.perf_counter()
    resolver = _Resolver(index)
    edges: dict[str, Relation] = {}
    unresolved = []

    def add(
        source: str, target: str, kind: str, confidence: str, line: int, expression: str
    ) -> None:
        edge = Relation(
            source, target, kind, confidence, index.symbols[source].path, line, expression
        )
        edges[edge.id] = edge

    for symbol in index.symbols.values():
        if symbol.parent_id:
            add(
                symbol.parent_id, symbol.id, "containment", "static", symbol.start_line, symbol.name
            )
    for owner, reference, line in resolver.imports:
        target, confidence = resolver.resolve_path(reference)
        if target:
            add(owner, target, "import", confidence, line, reference)
        else:
            unresolved.append(
                {
                    "source": owner,
                    "kind": "import",
                    "line": line,
                    "expression": reference,
                    "reason": confidence,
                }
            )
    for owner, node in resolver.calls:
        expression = ast.unparse(node.func)
        target, confidence = resolver.resolve_call(owner, node)
        if target:
            if is_test(index.symbols[owner].path) and not is_test(index.symbols[target].path):
                add(owner, target, "test", "heuristic", node.lineno, expression)
            else:
                add(owner, target, "call", confidence, node.lineno, expression)
        else:
            unresolved.append(
                {
                    "source": owner,
                    "kind": "call",
                    "line": node.lineno,
                    "expression": expression,
                    "reason": confidence,
                }
            )
    ordered = tuple(edges[key] for key in sorted(edges))
    unresolved.sort(key=lambda row: (row["source"], row["line"], row["kind"], row["expression"]))
    binding = graph_binding(index)
    metadata = {
        "schema_version": 1,
        "binding": binding,
        "graph_hash": stable_id(binding, [asdict(edge) for edge in ordered], unresolved),
        "build_seconds": time.perf_counter() - start,
        "edge_counts": dict(sorted(Counter(edge.kind for edge in ordered).items())),
        "confidence_counts": dict(sorted(Counter(edge.confidence for edge in ordered).items())),
        "unresolved_counts": dict(sorted(Counter(row["reason"] for row in unresolved).items())),
    }
    return RelationGraph(metadata, ordered, tuple(unresolved))


def build_graph(index: LoadedIndex, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Graph output already exists: {output}; choose a new file")
    graph = extract_graph(index)
    payload = {
        "metadata": graph.metadata,
        "edges": [asdict(edge) for edge in graph.edges],
        "unresolved": graph.unresolved,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=True, allow_nan=False)
            handle.write("\n")
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return graph.metadata


def load_graph(path: Path, index: LoadedIndex) -> RelationGraph:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if set(data) != {"metadata", "edges", "unresolved"}:
            raise ValueError("Invalid graph fields")
        metadata = data["metadata"]
        if metadata["schema_version"] != 1 or metadata["binding"] != graph_binding(index):
            raise ValueError("Graph cache mismatch; snapshot content or resolver changed")
        edges = tuple(Relation(**row) for row in data["edges"])
        ids = set()
        for edge in edges:
            if edge.source not in index.symbols or edge.target not in index.symbols:
                raise ValueError("Graph edge refers to a missing symbol")
            owner = index.symbols[edge.source]
            if (
                edge.kind not in RELATION_TYPES
                or edge.confidence not in {"static", "heuristic"}
                or edge.path != owner.path
                or type(edge.line) is not int
                or not owner.start_line <= edge.line <= owner.end_line
                or edge.id in ids
            ):
                raise ValueError("Invalid graph relation or duplicate edge")
            ids.add(edge.id)
        if metadata["graph_hash"] != stable_id(
            metadata["binding"], data["edges"], data["unresolved"]
        ):
            raise ValueError("Graph checksum mismatch")
        return RelationGraph(metadata, edges, tuple(data["unresolved"]))
    except (KeyError, TypeError) as error:
        raise ValueError("Invalid relation graph") from error
