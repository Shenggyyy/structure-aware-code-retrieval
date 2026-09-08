"""AST symbols and non-overlapping, line-bounded source chunks."""

import ast
import io
import itertools
import tokenize
from pathlib import PurePosixPath

from structure_aware_retrieval.models import (
    Chunk,
    ImportReference,
    ParsedFile,
    SourceFile,
    Symbol,
    stable_id,
)

Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _signature(node: Definition) -> str:
    type_parameters = (
        "[" + ", ".join(ast.unparse(value) for value in node.type_params) + "]"
        if node.type_params
        else ""
    )
    if isinstance(node, ast.ClassDef):
        arguments = [ast.unparse(value) for value in [*node.bases, *node.keywords]]
        return f"class {node.name}{type_parameters}({', '.join(arguments)}):"
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}{type_parameters}({ast.unparse(node.args)}){returns}:"


def parse_file(source: SourceFile, snapshot_id: str, *, max_chunk_lines: int = 80) -> ParsedFile:
    """Preserve original decoded lines, including decorators and encoding cookies.

    Each line belongs to its deepest enclosing definition. Parent chunks contain
    the remaining source, so entire classes/files do not duplicate child functions.
    """
    if max_chunk_lines < 1:
        raise ValueError("max_chunk_lines must be positive")
    encoding, _ = tokenize.detect_encoding(io.BytesIO(source.data).readline)
    text = io.StringIO(source.data.decode(encoding), newline=None).read()
    tree = ast.parse(text, filename=source.path)
    lines = io.StringIO(text).readlines()
    path = PurePosixPath(source.path)
    module_name = ".".join(path.with_suffix("").parts)
    if module_name.endswith(".__init__"):
        module_name = module_name.removesuffix(".__init__")
    module = Symbol(
        stable_id(snapshot_id, source.path, "module"),
        source.path,
        path.stem,
        module_name,
        "module",
        None,
        1,
        max(1, len(lines)),
        "",
        ast.get_docstring(tree),
    )
    symbols = [module]
    imports: list[ImportReference] = []

    def visit(node: ast.AST, owner: Symbol) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            start = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            end = node.end_lineno or node.lineno
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            if kind == "function" and owner.kind == "class":
                kind = "method"
            name = f"{owner.qualified_name}.{node.name}"
            owner = Symbol(
                stable_id(snapshot_id, source.path, kind, name, start, end),
                source.path,
                node.name,
                name,
                kind,
                owner.id,
                start,
                end,
                _signature(node),
                ast.get_docstring(node),
            )
            symbols.append(owner)
        elif isinstance(node, ast.Import):
            imports.extend(
                ImportReference(owner.id, item.name, None, item.asname, 0, node.lineno)
                for item in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports.extend(
                ImportReference(
                    owner.id, node.module or "", item.name, item.asname, node.level, node.lineno
                )
                for item in node.names
            )
        for child in ast.iter_child_nodes(node):
            visit(child, owner)

    visit(tree, module)
    owners = [module.id] * len(lines)
    # AST traversal visits parents before children; deeper definitions replace them.
    for symbol in symbols[1:]:
        owners[symbol.start_line - 1 : symbol.end_line] = [symbol.id] * (
            symbol.end_line - symbol.start_line + 1
        )
    chunks: list[Chunk] = []
    for owner_id, group in itertools.groupby(enumerate(owners), key=lambda item: item[1]):
        indices = [index for index, _ in group]
        for offset in range(0, len(indices), max_chunk_lines):
            start = indices[offset] + 1
            end = indices[min(offset + max_chunk_lines, len(indices)) - 1] + 1
            chunk_text = "".join(lines[start - 1 : end])
            if chunk_text.strip():
                chunks.append(
                    Chunk(
                        stable_id(snapshot_id, owner_id, start, end),
                        owner_id,
                        source.path,
                        start,
                        end,
                        chunk_text,
                    )
                )
    return ParsedFile(symbols, chunks, imports)
