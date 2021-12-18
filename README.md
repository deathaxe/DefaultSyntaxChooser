# Default Syntax Chooser

This Sublime Text 4 plugin provides the `set_default_syntax_dialect` command.

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

## Usage

A command for the target syntax is to be added to _Default.sublime-commands_

```json
[
    {
        "caption": "Set Syntax Dialect: SQL",
        "command": "assign_default_syntax_dialect",
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
