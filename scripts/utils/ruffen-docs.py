# fork of https://github.com/asottile/blacken-docs adapted for ruff
from __future__ import annotations

import re
import sys
import argparse
import textwrap
import contextlib
import subprocess
from typing import Match, Optional, Sequence, Generator, NamedTuple, cast

MD_RE = re.compile(
    r"(?P<before>^(?P<indent> *)```\s*python\n)" r"(?P<code>.*?)" r"(?P<after>^(?P=indent)```\s*$)",
    re.DOTALL | re.MULTILINE,
)
MD_PYCON_RE = re.compile(
    r"(?P<before>^(?P<indent> *)```\s*pycon\n)" r"(?P<code>.*?)" r"(?P<after>^(?P=indent)```.*$)",
    re.DOTALL | re.MULTILINE,
)
PYCON_PREFIX = ">>> "
PYCON_CONTINUATION_PREFIX = "..."
PYCON_CONTINUATION_RE = re.compile(
    rf"^{re.escape(PYCON_CONTINUATION_PREFIX)}( |$)",
)
DEFAULT_LINE_LENGTH = 100


class CodeBlockError(NamedTuple):
    offset: int
    exc: Exception


def format_str(
    src: str,
) -> tuple[str, Sequence[CodeBlockError]]:
    """
    Format all Python and Python REPL code blocks within a Markdown string using the ruff formatter.
    
    Parameters:
        src (str): The Markdown source text to process.
    
    Returns:
        tuple[str, Sequence[CodeBlockError]]: A tuple containing the formatted Markdown string and a sequence of errors encountered during code block formatting.
    """
    errors: list[CodeBlockError] = []

    @contextlib.contextmanager
    def _collect_error(match: Match[str]) -> Generator[None, None, None]:
        """
        Context manager that captures exceptions raised during code block processing and records them as CodeBlockError instances with the error offset.
        
        Intended for use within formatting routines to associate errors with their position in the source.
        """
        try:
            yield
        except Exception as e:
            errors.append(CodeBlockError(match.start(), e))

    def _md_match(match: Match[str]) -> str:
        """
        Format a matched Python code block from Markdown using the ruff formatter.
        
        Replaces the original code block with its formatted version, preserving indentation and surrounding Markdown structure.
        """
        code = textwrap.dedent(match["code"])
        with _collect_error(match):
            code = format_code_block(code)
        code = textwrap.indent(code, match["indent"])
        return f"{match['before']}{code}{match['after']}"

    def _pycon_match(match: Match[str]) -> str:
        """
        Formats a Python REPL (pycon) code block by extracting, formatting, and reconstructing input fragments.
        
        Processes lines from a Markdown pycon code block, identifies REPL input fragments, formats each fragment using the code formatter, and reassembles the block with correct REPL prompts and indentation. Preserves blank lines and prompt structure to maintain REPL semantics.
        
        Returns:
            str: The formatted pycon code block as a string.
        """
        code = ""
        fragment = cast(Optional[str], None)

        def finish_fragment() -> None:
            """
            Finalize and format the current REPL input fragment, appending it to the reconstructed Python REPL code block.
            
            This function formats the accumulated REPL fragment using the code formatter, splits it into lines, and appends each line to the output code block with appropriate REPL prompts. Handles blank lines and continuation prompts to preserve REPL session structure.
            """
            nonlocal code
            nonlocal fragment

            if fragment is not None:
                with _collect_error(match):
                    fragment = format_code_block(fragment)
                fragment_lines = fragment.splitlines()
                code += f"{PYCON_PREFIX}{fragment_lines[0]}\n"
                for line in fragment_lines[1:]:
                    # Skip blank lines to handle Black adding a blank above
                    # functions within blocks. A blank line would end the REPL
                    # continuation prompt.
                    #
                    # >>> if True:
                    # ...     def f():
                    # ...         pass
                    # ...
                    if line:
                        code += f"{PYCON_CONTINUATION_PREFIX} {line}\n"
                if fragment_lines[-1].startswith(" "):
                    code += f"{PYCON_CONTINUATION_PREFIX}\n"
                fragment = None

        indentation = None
        for line in match["code"].splitlines():
            orig_line, line = line, line.lstrip()
            if indentation is None and line:
                indentation = len(orig_line) - len(line)
            continuation_match = PYCON_CONTINUATION_RE.match(line)
            if continuation_match and fragment is not None:
                fragment += line[continuation_match.end() :] + "\n"
            else:
                finish_fragment()
                if line.startswith(PYCON_PREFIX):
                    fragment = line[len(PYCON_PREFIX) :] + "\n"
                else:
                    code += orig_line[indentation:] + "\n"
        finish_fragment()
        return code

    def _md_pycon_match(match: Match[str]) -> str:
        """
        Processes a matched Python REPL code block from Markdown, formats its content, and re-indents it to match the original indentation.
        
        Returns:
            str: The reconstructed Markdown code block with formatted and properly indented REPL content.
        """
        code = _pycon_match(match)
        code = textwrap.indent(code, match["indent"])
        return f"{match['before']}{code}{match['after']}"

    src = MD_RE.sub(_md_match, src)
    src = MD_PYCON_RE.sub(_md_pycon_match, src)
    return src, errors


def format_code_block(code: str) -> str:
    """
    Format a Python code block using the ruff formatter.
    
    Parameters:
        code (str): The Python code to format.
    
    Returns:
        str: The formatted Python code as returned by ruff.
    
    Raises:
        CalledProcessError: If the ruff formatter fails or returns a non-zero exit code.
    """
    return subprocess.check_output(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--stdin-filename=script.py",
            f"--line-length={DEFAULT_LINE_LENGTH}",
        ],
        encoding="utf-8",
        input=code,
    )


def format_file(
    filename: str,
    skip_errors: bool,
) -> int:
    """
    Format all Python code blocks in a Markdown file and rewrite the file if changes are made.
    
    Parameters:
        filename (str): Path to the Markdown file to process.
        skip_errors (bool): If True, continue processing even if formatting errors occur.
    
    Returns:
        int: 0 if successful or no changes were made, 1 if errors occurred and were not skipped.
    """
    with open(filename, encoding="UTF-8") as f:
        contents = f.read()
    new_contents, errors = format_str(contents)
    for error in errors:
        lineno = contents[: error.offset].count("\n") + 1
        print(f"{filename}:{lineno}: code block parse error {error.exc}")
    if errors and not skip_errors:
        return 1
    if contents != new_contents:
        print(f"{filename}: Rewriting...")
        with open(filename, "w", encoding="UTF-8") as f:
            f.write(new_contents)
        return 0
    else:
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """
    Parse command-line arguments and format Python code blocks in specified Markdown files.
    
    Processes each provided filename, formatting embedded Python and Python REPL code blocks using the ruff formatter. Aggregates and returns an exit code indicating overall success or failure.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--line-length",
        type=int,
        default=DEFAULT_LINE_LENGTH,
    )
    parser.add_argument(
        "-S",
        "--skip-string-normalization",
        action="store_true",
    )
    parser.add_argument("-E", "--skip-errors", action="store_true")
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= format_file(filename, skip_errors=args.skip_errors)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
