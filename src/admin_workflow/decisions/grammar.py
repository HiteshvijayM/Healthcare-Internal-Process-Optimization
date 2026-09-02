"""Declarative rule evaluation — the restricted grammar of RC-5.

There is no ``eval``. The grammar is: field references, string/number literals,
and the operators ``equals``, ``contains``, ``contains_any``, ``in``,
``is_present``, ``is_missing``, ``and``, ``or``, ``not``, ``always``.

Keeping the grammar closed is what makes FR-017's "inspectable by a
non-technical reviewer" true rather than aspirational — a reviewer can read every
expression the engine is capable of evaluating.
"""

from __future__ import annotations

import ast
import re
from typing import Any, Callable

_LIST_RE = re.compile(r"\[.*?\]", re.S)


class GrammarError(ValueError):
    """The expression used something outside the permitted grammar (RC-5)."""


def _parse_literal_list(token: str) -> list[str]:
    try:
        parsed = ast.literal_eval(token)
    except (ValueError, SyntaxError) as exc:
        raise GrammarError(f"not a literal list: {token!r}") from exc
    if not isinstance(parsed, (list, tuple)):
        raise GrammarError(f"expected a list literal, got {token!r}")
    return [str(item) for item in parsed]


def _as_text(value: Any) -> str:
    return "" if value is None else str(value).lower()


def _eval_atom(expr: str, ctx: dict[str, Any]) -> bool:
    expr = expr.strip()
    if expr == "always":
        return True

    if " contains_any " in expr:
        field, _, rhs = expr.partition(" contains_any ")
        haystack = _as_text(ctx.get(field.strip()))
        return any(needle.lower() in haystack for needle in _parse_literal_list(rhs.strip()))

    if " contains " in expr:
        field, _, rhs = expr.partition(" contains ")
        return _parse_scalar(rhs).lower() in _as_text(ctx.get(field.strip()))

    if " equals " in expr:
        field, _, rhs = expr.partition(" equals ")
        return _as_text(ctx.get(field.strip())) == _parse_scalar(rhs).lower()

    if " in " in expr:
        field, _, rhs = expr.partition(" in ")
        return _as_text(ctx.get(field.strip())) in [v.lower() for v in _parse_literal_list(rhs.strip())]

    if expr.endswith(" is_present"):
        return ctx.get(expr[: -len(" is_present")].strip()) not in (None, "")

    if expr.endswith(" is_missing"):
        return ctx.get(expr[: -len(" is_missing")].strip()) in (None, "")

    raise GrammarError(f"unrecognised expression: {expr!r}")


def _parse_scalar(token: str) -> str:
    token = token.strip()
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token[1:-1]
    return token


def _split_top_level(expr: str, keyword: str) -> list[str] | None:
    """Split on a keyword that is not inside a bracketed literal list."""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    tokens = expr.split(" ")
    i = 0
    while i < len(tokens):
        token = tokens[i]
        depth += token.count("[") - token.count("]")
        if token == keyword and depth == 0:
            parts.append(" ".join(buf))
            buf = []
        else:
            buf.append(token)
        i += 1
    parts.append(" ".join(buf))
    return parts if len(parts) > 1 else None


def evaluate(expression: str, ctx: dict[str, Any]) -> bool:
    """Evaluate one ``when`` expression against a flat context mapping."""
    expr = expression.strip()

    or_parts = _split_top_level(expr, "or")
    if or_parts:
        return any(evaluate(part, ctx) for part in or_parts)

    and_parts = _split_top_level(expr, "and")
    if and_parts:
        return all(evaluate(part, ctx) for part in and_parts)

    if expr.startswith("not "):
        return not evaluate(expr[4:], ctx)

    return _eval_atom(expr, ctx)


PERMITTED_OPERATORS: frozenset[str] = frozenset(
    {"equals", "contains", "contains_any", "in", "is_present", "is_missing", "and", "or", "not", "always"}
)


def uses_only_permitted_grammar(expression: str) -> bool:
    """RC-5 contract check. Strips literal lists first so their contents are not
    mistaken for operators."""
    stripped = _LIST_RE.sub(" ", expression)
    stripped = re.sub(r"'[^']*'|\"[^\"]*\"", " ", stripped)
    for token in stripped.split():
        if token in PERMITTED_OPERATORS:
            continue
        if re.fullmatch(r"[a-z_][a-z0-9_]*", token):  # a field reference
            continue
        if re.fullmatch(r"-?\d+(\.\d+)?", token):  # a numeric literal
            continue
        return False
    return True
