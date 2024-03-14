from collections.abc import Callable, Mapping, Sequence
from functools import cached_property

import attrs

from puya.errors import Errors
from puya.options import PuyaOptions
from puya.parse import ParseResult, SourceLocation


@attrs.frozen
class SourceMeta:
    location: str | None
    code: Sequence[str] | None


_EmptyMeta = SourceMeta(None, None)


@attrs.define
class CompileContext:
    options: PuyaOptions
    parse_result: ParseResult
    errors: Errors
    read_source: Callable[[str], Sequence[str] | None]

    @cached_property
    def module_paths(self) -> Mapping[str, str]:
        return {m.fullname: m.path for m in self.parse_result.ordered_modules}

    def try_get_source(self, location: SourceLocation | None) -> SourceMeta:
        if location is None:
            return _EmptyMeta
        source_lines = self.read_source(location.file)
        if not source_lines:
            src_content = list[str]()
        else:
            start_line = end_line = location.line
            if location.end_line:
                end_line = location.end_line
            src_content = list(
                source_lines[start_line - 1 : end_line]  # location.lines is one-indexed
            )

            start_column = location.column
            end_column = location.end_column
            if not src_content:
                self.errors.warning(f"Could not locate source: {location}", None)
            elif start_line == end_line and start_column is not None and end_column is not None:
                src_content[0] = src_content[0][start_column:end_column]
            else:
                if start_column is not None:
                    src_content[0] = src_content[0][start_column:]
                if end_column is not None:
                    src_content[-1] = src_content[-1][:end_column]
        return SourceMeta(location=str(location), code=src_content)
