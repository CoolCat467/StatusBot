"""Translates Mypy's output into GitHub's error/warning annotation syntax.

See: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

This first is run with Mypy's output piped in, to collect messages in
mypy_annotate.dat. After all platforms run, we run this again, which prints the
messages in GitHub's format but with cross-platform failures deduplicated.
"""

# Original Source:
# https://github.com/python-trio/trio/blob/main/src/trio/_tools/mypy_annotate.py
# Dual-licensed under your choice of MIT or Apache 2

# MIT License
# Copyright (c) 2023-2026 Trio contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Apache 2.0 License
# Copyright 2023-2026 Trio contributors
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from __future__ import annotations

import argparse
import pickle
import re
import sys

import attrs

# Example: 'package/filename.py:42:1:46:3: error: Type error here [code]'
report_re = re.compile(
    r"""
    ([^:]+):  # Filename (anything but ":")
    ([0-9]+):  # Line number (start)
    (?:([0-9]+):  # Optional column number
      (?:([0-9]+):([0-9]+):)?  # then also optionally, 2 more numbers for end columns
    )?
    \s*(error|warn|note):  # Kind, prefixed with space
    (.+)  # Message
    """,
    re.VERBOSE,
)

mypy_to_github = {
    "error": "error",
    "warn": "warning",
    "note": "notice",
}


@attrs.frozen(kw_only=True)
class Result:
    """Accumulated results, used as a dict key to deduplicate."""

    filename: str
    start_line: int
    kind: str
    message: str
    start_col: int | None = None
    end_line: int | None = None
    end_col: int | None = None


def process_line(line: str) -> Result | None:
    """Process mypy line and return Result object or None if parse error."""
    if match := report_re.fullmatch(line.rstrip()):
        filename, st_line, st_col, end_line, end_col, kind, message = (
            match.groups()
        )
        return Result(
            filename=filename,
            start_line=int(st_line),
            start_col=int(st_col) if st_col is not None else None,
            end_line=int(end_line) if end_line is not None else None,
            end_col=int(end_col) if end_col is not None else None,
            kind=mypy_to_github[kind],
            message=message,
        )
    return None


def export(results: dict[Result, list[str]]) -> None:
    """Display the collected results."""
    for res, platforms in results.items():
        print(
            f"::{res.kind} file={res.filename},line={res.start_line},",
            end="",
        )
        if res.start_col is not None:
            print(f"col={res.start_col},", end="")
            if res.end_col is not None and res.end_line is not None:
                print(
                    f"endLine={res.end_line},endColumn={res.end_col},",
                    end="",
                )
                message = f"({res.start_line}:{res.start_col} - {res.end_line}:{res.end_col}):{res.message}"
            else:
                message = f"({res.start_line}:{res.start_col}):{res.message}"
        else:
            message = f"{res.start_line}:{res.message}"
        print(f"title=Mypy-{'+'.join(platforms)}::{res.filename}:{message}")


def main(argv: list[str]) -> None:
    """Look for error messages, and convert the format."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dumpfile",
        help="File to write pickled messages to.",
        required=True,
    )
    parser.add_argument(
        "--platform",
        help="OS name, if set Mypy should be piped to stdin.",
        default=None,
    )
    cmd_line = parser.parse_args(argv)

    results: dict[Result, list[str]]
    try:
        # S301 `pickle` and modules that wrap it can be unsafe when used to
        # deserialize untrusted data, possible security issue.
        # Not security issue because this is used for tests, not in project
        # itself.
        with open(cmd_line.dumpfile, "rb") as f:
            results = pickle.load(f)  # noqa: S301
    except (FileNotFoundError, pickle.UnpicklingError):
        # If we fail to load, assume it's an old result.
        results = {}

    if cmd_line.platform is None:
        # Write out the results.
        export(results)
    else:
        platform: str = cmd_line.platform
        for line in sys.stdin:
            parsed = process_line(line)
            if parsed is not None:
                try:
                    results[parsed].append(platform)
                except KeyError:
                    results[parsed] = [platform]
            sys.stdout.write(line)
        with open(cmd_line.dumpfile, "wb") as f:
            pickle.dump(results, f)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
