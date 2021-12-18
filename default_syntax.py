import re

import sublime
import sublime_plugin

from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Union


class DialectFileInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, default_syntax: sublime.Syntax):
        super().__init__()
        self.default_syntax = default_syntax

    def name(self) -> str:
        return "dialect_file"

    def placeholder(self) -> str:
        return "Choose the dialect to use as default syntax."

    def list_items(self) -> List[sublime.ListInputItem]:
        # Use first two scope levels to find dialects
        default_scopes = self.default_syntax.scope.split(".")
        default_scope = f"{default_scopes[0]}.{default_scopes[1]}"

        match = re.search(
            r"^extends:\s+(?:-\s+)?(\S+)",
            sublime.load_resource(self.default_syntax.path),
            flags=re.MULTILINE,
        )
        selected_syntax = sublime.syntax_from_path(match.group(1)) if match else None
        selected_kind = (sublime.KIND_ID_AMBIGUOUS, "✓", "Selected")

        items = []
        for syntax in sublime.list_syntaxes():
            if syntax.hidden:
                continue
            if syntax == self.default_syntax:
                continue
            if not syntax.scope.startswith(default_scope):
                continue
            items.append(
                sublime.ListInputItem(
                    text=syntax.name,
                    value=syntax.path,
                    kind=selected_kind
                    if syntax == selected_syntax
                    else sublime.KIND_AMBIGUOUS,
                )
            )
        return items


class SetDefaultSyntaxDialect(sublime_plugin.WindowCommand):
    """
    This class implements the `set_default_syntax_dialect` command.

    This command manipulates a syntax file (e.g.: SQL.sublime-syntax) to make
    it point to a desired dialect (e.g.: MySQL.sublime-syntax). As a result
    the dialect is used whenever the default syntax's scope (e.g.: `source.sql`)
    is addressed. This way it is possible to specify the syntax to use in
    embedded code blocks.

    Syntax definitions may embed others to highlight certain parts of a document
    with that external language. Very popular examples are:

    1) HTML embeds CSS and JavaScript.
    2) Markdown embeds many other syntaxes to highlight fenced code blocks
    3) Ruby/PHP embed various syntaxes (e.g.: SQL, XML, ...) to highlight HEREDOCs

    They do so by embedding scopes (e.g.: `embed: scope:source.sql`).

    But what if such a syntax has several dialects while the embedding syntax
    doesn't have any solution to distinguish them?

    Ruby/PHP only know about "SQL" syntax.
    But SQL may be used as synonym for MySQL, PostgresSQL, SQLight or T-SQL.

    Usage:
    ======

    A command for the target syntax is to be added to _Default.sublime-commands_

    ```json
    [
        {
            "caption": "Set Syntax Dialect: SQL",
            "command": "set_default_syntax_dialect",
            "args": {
                "syntax_file": "Packages/SQL/SQL.sublime-syntax"
            }
        }
    ]
    ```

    The target syntax should be an alias and must be extended from a dialect.

    ```yaml
    %YAML 1.2
    ---
    name: SQL
    scope: source.sql
    version: 2

    extends: Packages/SQL/MySQL.sublime-syntax

    file_extensions:
      - sql
      - ddl
      - dml

    first_line_match: |-
      (?xi:
        ^ \\s* -- .*? -\\*- .*? \\bsql\\b .*? -\\*-  # editorconfig
      )

    ```
    """

    def input(self, args: Dict[str, str]) -> Union[DialectFileInputHandler, None]:
        if not args.get("dialect_file"):
            default_syntax = sublime.syntax_from_path(args.get("syntax_file"))
            if default_syntax:
                return DialectFileInputHandler(default_syntax)
        return None

    def input_description(self) -> str:
        return "Syntax:"

    def run(self, syntax_file: str, dialect_file: str) -> None:
        # validate target syntax
        default_syntax = sublime.syntax_from_path(syntax_file)
        if not default_syntax:
            print(f'Error: "{syntax_file}" is no valid target syntax!')
            return

        # validate dialect syntax
        dialect_syntax = sublime.syntax_from_path(dialect_file)
        if not dialect_syntax:
            print(f'Error: "{dialect_file}" is no valid syntax!')
            return

        # open existing target syntax and replace dialect syntax
        # note: uses a naive search/replace approach to avoid YAML dependencies
        old_content = sublime.load_resource(default_syntax.path)
        new_content = re.sub(
            r"(^extends:\s+(?:-\s+)?)\S+",
            rf"\1{dialect_syntax.path}",
            old_content,
            flags=re.MULTILINE,
        )
        # don't touch syntax file if content is unchanged in order to
        # avoid re-indexing all open files and folders
        if old_content == new_content:
            return

        # write modified default syntax to extracted Packages path
        with open(
            file=Path(sublime.packages_path()).parent / default_syntax.path,
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as out:
            out.write(new_content)
