import hashlib
import io

import pytest

from structure_aware_retrieval.models import SourceFile
from structure_aware_retrieval.parsing import parse_file


def source(text: str | bytes, path: str = "pkg/example.py") -> SourceFile:
    data = text.encode() if isinstance(text, str) else text
    return SourceFile(path, hashlib.sha256(data).hexdigest(), data)


def test_decorators_nested_scopes_imports_and_exact_ranges() -> None:
    code = (
        "from .helpers import send as transmit\n"
        "class Client:\n"
        "    @decorate\n"
        "    async def fetch(\n"
        "        self, url: str,\n"
        "    ) -> str:\n"
        '        """Fetch a URL."""\n'
        "        def normalize(value):\n"
        "            return value.strip()\n"
        "        return transmit(normalize(url))\n"
    )
    parsed = parse_file(source(code), "snapshot")
    symbols = {item.qualified_name: item for item in parsed.symbols}
    method = symbols["pkg.example.Client.fetch"]
    nested = symbols["pkg.example.Client.fetch.normalize"]

    assert (method.kind, method.start_line, method.end_line) == ("method", 3, 10)
    assert method.signature == "async def fetch(self, url: str) -> str:"
    assert method.docstring == "Fetch a URL."
    assert nested.kind == "function"
    assert nested.parent_id == method.id
    assert parsed.imports[0].module == "helpers"
    assert parsed.imports[0].alias == "transmit"
    assert parsed.imports[0].level == 1
    covered = []
    for chunk in parsed.chunks:
        assert chunk.text == "".join(
            code.splitlines(keepends=True)[chunk.start_line - 1 : chunk.end_line]
        )
        covered.extend(range(chunk.start_line, chunk.end_line + 1))
    assert sorted(covered) == list(range(1, 11))
    assert len(covered) == len(set(covered))


def test_long_functions_are_bounded_without_losing_lines() -> None:
    code = "def long_function():\n" + "    value = 1\n" * 9
    parsed = parse_file(source(code), "snapshot", max_chunk_lines=3)
    assert [chunk.end_line - chunk.start_line + 1 for chunk in parsed.chunks] == [3, 3, 3, 1]
    assert "".join(chunk.text for chunk in parsed.chunks) == code
    assert len({chunk.symbol_id for chunk in parsed.chunks}) == 1


def test_ids_are_repeatable_and_snapshot_scoped() -> None:
    file = source("def same():\n    pass\n\ndef same():\n    pass\n")
    first = parse_file(file, "snapshot")
    assert first == parse_file(file, "snapshot")
    assert len({item.id for item in first.symbols}) == len(first.symbols)
    assert first.chunks[0].id != parse_file(file, "other").chunks[0].id


def test_pep263_encoding_and_unicode_line_separators() -> None:
    latin = parse_file(source(b"# coding: latin-1\r\nname = 'caf\xe9'\r\n"), "s")
    assert "café" in latin.chunks[0].text
    code = "label = 'a\u2028b'\n\ndef café():\n    return label\n"
    parsed = parse_file(source(code), "s")
    function = parsed.symbols[1]
    assert (function.start_line, function.end_line) == (3, 4)
    assert parsed.chunks[-1].text == "".join(io.StringIO(code).readlines()[2:])


def test_empty_module_has_no_chunks() -> None:
    parsed = parse_file(source("", "pkg/__init__.py"), "s")
    assert parsed.chunks == []
    assert parsed.symbols[0].qualified_name == "pkg"


def test_definitions_in_control_flow_keep_lexical_parent() -> None:
    parsed = parse_file(source("if True:\n    class Example:\n        def run(self): pass\n"), "s")
    assert parsed.symbols[-1].qualified_name == "pkg.example.Example.run"
    assert parsed.symbols[-1].kind == "method"


def test_python312_type_parameters_and_class_keywords() -> None:
    parsed = parse_file(source("class Box[T](Base, metaclass=Meta):\n    pass\n"), "s")
    assert parsed.symbols[1].signature == "class Box[T](Base, metaclass=Meta):"


@pytest.mark.parametrize("code", ["def broken(:\n", b"name = '\xff'\n"])
def test_invalid_source_is_not_silently_accepted(code: str | bytes) -> None:
    with pytest.raises((SyntaxError, UnicodeError)):
        parse_file(source(code), "s")
