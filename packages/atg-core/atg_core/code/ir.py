"""Behavioural IR shared by every code dialect.

Code translation preserves behaviour and contracts, not tokens. Every language
adapter parses into this IR and emits from it; anything a language adapter
cannot express in the IR is raised as :class:`UnsupportedConstruct` so the
caller can record an unknown instead of pretending equivalence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

CANONICAL_TYPES = (
    "integer",
    "number",
    "string",
    "boolean",
    "void",
    "unknown",
)

CANONICAL_ERRORS = {
    "ValueError": "invalid_argument",
    "TypeError": "type_error",
    "KeyError": "missing_key",
    "ZeroDivisionError": "division_by_zero",
    "NotImplementedError": "not_implemented",
    "Error": "invalid_argument",
    "RangeError": "out_of_range",
    "TypeError_ts": "type_error",
}

ERROR_TO_PYTHON = {
    "invalid_argument": "ValueError",
    "type_error": "TypeError",
    "missing_key": "KeyError",
    "division_by_zero": "ZeroDivisionError",
    "not_implemented": "NotImplementedError",
    "out_of_range": "RangeError",
}


class UnsupportedConstruct(Exception):
    """Raised when a source construct has no proven IR equivalent."""

    def __init__(self, construct: str, detail: str = "") -> None:
        super().__init__(f"{construct}: {detail}" if detail else construct)
        self.construct = construct
        self.detail = detail


# -- expression constructors -------------------------------------------------

def name(identifier: str) -> Dict[str, Any]:
    return {"node": "name", "id": identifier}


def const(value: Any, type_name: str = "unknown") -> Dict[str, Any]:
    return {"node": "const", "value": value, "type": type_name}


def call(fn: str, args: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"node": "call", "fn": fn, "args": args}


def binop(op: str, left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    return {"node": "binop", "op": op, "left": left, "right": right}


def compare(op: str, left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    return {"node": "compare", "op": op, "left": left, "right": right}


def lambda_(params: List[str], body: Dict[str, Any]) -> Dict[str, Any]:
    return {"node": "lambda", "params": params, "body": body}


# -- statement constructors --------------------------------------------------

def stmt_if(test: Dict[str, Any], then: List[Dict[str, Any]], orelse: Optional[List[Dict[str, Any]]] = None):
    return {"stmt": "if", "test": test, "then": then, "else": orelse or []}


def stmt_raise(error: str, message: str) -> Dict[str, Any]:
    return {"stmt": "raise", "error": error, "message": message}


def stmt_assign(target: str, value: Dict[str, Any]) -> Dict[str, Any]:
    return {"stmt": "assign", "target": target, "value": value}


def stmt_return(value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {"stmt": "return", "value": value}


# -- naming ------------------------------------------------------------------

def to_camel_case(identifier: str) -> str:
    head, *rest = identifier.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest if part)


def to_snake_case(identifier: str) -> str:
    out: List[str] = []
    for index, char in enumerate(identifier):
        if char.isupper():
            if index:
                out.append("_")
            out.append(char.lower())
        else:
            out.append(char)
    return "".join(out)


# -- normalisation -----------------------------------------------------------

_SUM_LAMBDA_OPS = {"+"}


def normalize_expression(node: Dict[str, Any]) -> Dict[str, Any]:
    """Fold dialect idioms into canonical operations."""
    if not isinstance(node, dict):
        return node
    kind = node.get("node")
    if kind == "call":
        args = [normalize_expression(arg) for arg in node.get("args", [])]
        fn = node["fn"]
        folded = _fold_reduce(fn, args)
        if folded is not None:
            return folded
        return call(fn, args)
    if kind == "binop":
        return binop(node["op"], normalize_expression(node["left"]), normalize_expression(node["right"]))
    if kind == "compare":
        return compare(node["op"], normalize_expression(node["left"]), normalize_expression(node["right"]))
    if kind == "lambda":
        return lambda_(node["params"], normalize_expression(node["body"]))
    return node


def _fold_reduce(fn: str, args: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """`xs.reduce((a, b) => a + b, 0)` is the canonical `sum(xs)`."""
    if fn != "reduce" or len(args) != 3:
        return None
    subject, fn_arg, initial = args
    if fn_arg.get("node") != "lambda" or len(fn_arg.get("params", [])) != 2:
        return None
    body = fn_arg["body"]
    if body.get("node") != "binop" or body.get("op") not in _SUM_LAMBDA_OPS:
        return None
    left, right = body["left"], body["right"]
    params = fn_arg["params"]
    if {left.get("id"), right.get("id")} != set(params):
        return None
    if initial.get("node") != "const" or initial.get("value") not in (0, 0.0):
        return None
    return call("sum", [subject])


def expression_signature(node: Optional[Dict[str, Any]]) -> str:
    """Stable text form used for behavioural comparison."""
    if node is None:
        return "void"
    kind = node.get("node")
    if kind == "name":
        return to_snake_case(node["id"])
    if kind == "const":
        return f"const({node['value']!r})"
    if kind == "call":
        return f"{node['fn']}(" + ",".join(expression_signature(a) for a in node.get("args", [])) + ")"
    if kind == "binop":
        return f"({expression_signature(node['left'])}{node['op']}{expression_signature(node['right'])})"
    if kind == "compare":
        return f"({expression_signature(node['left'])}{node['op']}{expression_signature(node['right'])})"
    if kind == "lambda":
        return "lambda(" + ",".join(node["params"]) + ")->" + expression_signature(node["body"])
    return "unknown"


def statement_signature(statement: Dict[str, Any]) -> str:
    kind = statement.get("stmt")
    if kind == "if":
        then = ";".join(statement_signature(s) for s in statement.get("then", []))
        orelse = ";".join(statement_signature(s) for s in statement.get("else", []))
        return f"if({expression_signature(statement['test'])}){{{then}}}else{{{orelse}}}"
    if kind == "raise":
        return f"raise({statement['error']}:{statement['message']})"
    if kind == "assign":
        return f"{to_snake_case(statement['target'])}={expression_signature(statement['value'])}"
    if kind == "return":
        return f"return({expression_signature(statement.get('value'))})"
    return "unknown"


def behavior_signature(statements: List[Dict[str, Any]]) -> str:
    return ";".join(statement_signature(s) for s in statements)
