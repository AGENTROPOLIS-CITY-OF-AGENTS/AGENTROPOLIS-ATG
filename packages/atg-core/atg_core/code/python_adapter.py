"""Python <-> ATG behavioural IR."""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Tuple

from . import ir

PY_TYPE_MAP = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
    "None": "void",
    "NoneType": "void",
    "Any": "unknown",
}

BUILTIN_CALLS = {"len": "length", "sum": "sum", "abs": "abs", "min": "min", "max": "max", "round": "round"}
CANONICAL_TO_PY_CALL = {v: k for k, v in BUILTIN_CALLS.items()}

BINOPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}
COMPARES = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}


def _annotation_to_type(node: Optional[ast.AST]) -> str:
    if node is None:
        return "unknown"
    if isinstance(node, ast.Constant) and node.value is None:
        return "void"
    if isinstance(node, ast.Name):
        return PY_TYPE_MAP.get(node.id, node.id.lower())
    if isinstance(node, ast.Attribute):
        return PY_TYPE_MAP.get(node.attr, node.attr.lower())
    if isinstance(node, ast.Subscript):
        base = _annotation_to_type(node.value)
        args = node.slice
        if isinstance(args, ast.Tuple):
            inner = [_annotation_to_type(e) for e in args.elts]
        else:
            inner = [_annotation_to_type(args)]
        if base in ("list", "sequence", "iterable"):
            return f"list<{inner[0]}>"
        if base in ("dict", "mapping"):
            return f"map<{inner[0]},{inner[-1]}>"
        if base == "optional":
            return f"optional<{inner[0]}>"
        return f"{base}<{','.join(inner)}>"
    raise ir.UnsupportedConstruct("python.annotation", ast.dump(node))


def _expr(node: ast.AST) -> Dict[str, Any]:
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool):
            return ir.const(value, "boolean")
        if isinstance(value, int):
            return ir.const(value, "integer")
        if isinstance(value, float):
            return ir.const(value, "number")
        if isinstance(value, str):
            return ir.const(value, "string")
        raise ir.UnsupportedConstruct("python.constant", repr(value))
    if isinstance(node, ast.Name):
        return ir.name(node.id)
    if isinstance(node, ast.BinOp):
        op = BINOPS.get(type(node.op))
        if op is None:
            raise ir.UnsupportedConstruct("python.binop", type(node.op).__name__)
        return ir.binop(op, _expr(node.left), _expr(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return ir.binop("-", ir.const(0, "integer"), _expr(node.operand))
    if isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise ir.UnsupportedConstruct("python.chained_compare", ast.dump(node))
        op = COMPARES.get(type(node.ops[0]))
        if op is None:
            raise ir.UnsupportedConstruct("python.compare", type(node.ops[0]).__name__)
        return ir.compare(op, _expr(node.left), _expr(node.comparators[0]))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ir.UnsupportedConstruct("python.call_target", ast.dump(node.func))
        fn = BUILTIN_CALLS.get(node.func.id)
        if fn is None:
            raise ir.UnsupportedConstruct("python.call", node.func.id)
        if node.keywords:
            raise ir.UnsupportedConstruct("python.call_keywords", node.func.id)
        return ir.call(fn, [_expr(arg) for arg in node.args])
    raise ir.UnsupportedConstruct("python.expression", type(node).__name__)


def _statements(body: List[ast.stmt]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for node in body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # docstring
        if isinstance(node, ast.If):
            out.append(ir.stmt_if(_expr(node.test), _statements(node.body), _statements(node.orelse)))
        elif isinstance(node, ast.Raise):
            out.append(_raise(node))
        elif isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                raise ir.UnsupportedConstruct("python.assign_target", ast.dump(node))
            out.append(ir.stmt_assign(node.targets[0].id, _expr(node.value)))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            out.append(ir.stmt_assign(node.target.id, _expr(node.value)))
        elif isinstance(node, ast.Return):
            out.append(ir.stmt_return(_expr(node.value) if node.value is not None else None))
        else:
            raise ir.UnsupportedConstruct("python.statement", type(node).__name__)
    return out


def _raise(node: ast.Raise) -> Dict[str, Any]:
    exc = node.exc
    if not isinstance(exc, ast.Call) or not isinstance(exc.func, ast.Name):
        raise ir.UnsupportedConstruct("python.raise", ast.dump(node))
    error = ir.CANONICAL_ERRORS.get(exc.func.id, exc.func.id.lower())
    message = ""
    if exc.args:
        first = exc.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            message = first.value
        else:
            raise ir.UnsupportedConstruct("python.raise_message", ast.dump(first))
    return ir.stmt_raise(error, message)


def parse_functions(source: str) -> List[Dict[str, Any]]:
    """Parse Python source into a list of canonical function contracts."""
    tree = ast.parse(source)
    contracts: List[Dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            raise ir.UnsupportedConstruct("python.module_member", type(node).__name__)
        contracts.append(_function(node))
    if not contracts:
        raise ir.UnsupportedConstruct("python.module", "no function definitions found")
    return contracts


def _function(node: ast.FunctionDef) -> Dict[str, Any]:
    args = node.args
    if args.vararg or args.kwarg or args.posonlyargs or args.kwonlyargs:
        raise ir.UnsupportedConstruct("python.signature", "variadic or keyword-only parameters")
    defaults: List[Optional[ast.expr]] = [None] * (len(args.args) - len(args.defaults)) + list(args.defaults)
    params = []
    for arg, default in zip(args.args, defaults, strict=True):
        params.append(
            {
                "name": arg.arg,
                "type": _annotation_to_type(arg.annotation),
                "optional": default is not None,
                "default": _expr(default) if default is not None else None,
            }
        )
    statements = _statements(node.body)
    errors = sorted({s["error"] for s in _walk(statements) if s.get("stmt") == "raise"})
    return {
        "name": ir.to_snake_case(node.name),
        "params": params,
        "returns": _annotation_to_type(node.returns),
        "errors": errors,
        "docstring": ast.get_docstring(node) or "",
        "statements": [ir.normalize_expression(s) if "node" in s else _normalize_stmt(s) for s in statements],
    }


def _normalize_stmt(statement: Dict[str, Any]) -> Dict[str, Any]:
    kind = statement.get("stmt")
    if kind == "if":
        return ir.stmt_if(
            ir.normalize_expression(statement["test"]),
            [_normalize_stmt(s) for s in statement["then"]],
            [_normalize_stmt(s) for s in statement["else"]],
        )
    if kind == "assign":
        return ir.stmt_assign(statement["target"], ir.normalize_expression(statement["value"]))
    if kind == "return":
        value = statement.get("value")
        return ir.stmt_return(ir.normalize_expression(value) if value else None)
    return statement


def _walk(statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for statement in statements:
        out.append(statement)
        if statement.get("stmt") == "if":
            out += _walk(statement.get("then", []))
            out += _walk(statement.get("else", []))
    return out


# -- emission ----------------------------------------------------------------

def _py_type(canonical: str) -> str:
    reverse = {v: k for k, v in PY_TYPE_MAP.items()}
    if canonical.startswith("list<"):
        return f"List[{_py_type(canonical[5:-1])}]"
    if canonical.startswith("optional<"):
        return f"Optional[{_py_type(canonical[9:-1])}]"
    if canonical.startswith("map<"):
        key, value = canonical[4:-1].split(",", 1)
        return f"Dict[{_py_type(key)}, {_py_type(value)}]"
    return reverse.get(canonical, canonical)


def _emit_expr(node: Dict[str, Any]) -> str:
    kind = node["node"]
    if kind == "name":
        return ir.to_snake_case(node["id"])
    if kind == "const":
        return repr(node["value"])
    if kind == "call":
        fn = CANONICAL_TO_PY_CALL.get(node["fn"], node["fn"])
        return f"{fn}(" + ", ".join(_emit_expr(a) for a in node["args"]) + ")"
    if kind == "binop":
        return f"({_emit_expr(node['left'])} {node['op']} {_emit_expr(node['right'])})"
    if kind == "compare":
        return f"{_emit_expr(node['left'])} {node['op']} {_emit_expr(node['right'])}"
    raise ir.UnsupportedConstruct("python.emit_expression", kind)


def _emit_statements(statements: List[Dict[str, Any]], indent: str) -> List[str]:
    lines: List[str] = []
    for statement in statements:
        kind = statement["stmt"]
        if kind == "if":
            lines.append(f"{indent}if {_emit_expr(statement['test'])}:")
            lines += _emit_statements(statement["then"], indent + "    ") or [f"{indent}    pass"]
            if statement.get("else"):
                lines.append(f"{indent}else:")
                lines += _emit_statements(statement["else"], indent + "    ")
        elif kind == "raise":
            exc = ir.ERROR_TO_PYTHON.get(statement["error"], "ValueError")
            lines.append(f"{indent}raise {exc}({statement['message']!r})")
        elif kind == "assign":
            lines.append(f"{indent}{ir.to_snake_case(statement['target'])} = {_emit_expr(statement['value'])}")
        elif kind == "return":
            value = statement.get("value")
            lines.append(f"{indent}return {_emit_expr(value)}" if value else f"{indent}return")
        else:
            raise ir.UnsupportedConstruct("python.emit_statement", kind)
    return lines


def emit_functions(contracts: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """Emit Python source; returns (source, notes)."""
    notes: List[str] = []
    typing_needed = any(
        p["type"].startswith(("list<", "map<", "optional<"))
        for contract in contracts
        for p in contract["params"]
    ) or any(contract["returns"].startswith(("list<", "map<", "optional<")) for contract in contracts)
    lines: List[str] = []
    if typing_needed:
        lines.append("from typing import Dict, List, Optional")
        lines.append("")
        lines.append("")
    for contract in contracts:
        params = ", ".join(
            f"{p['name']}: {_py_type(p['type'])}"
            + (f" = {_emit_expr(p['default'])}" if p.get("default") else "")
            for p in contract["params"]
        )
        lines.append(f"def {ir.to_snake_case(contract['name'])}({params}) -> {_py_type(contract['returns'])}:")
        if contract.get("docstring"):
            lines.append(f'    """{contract["docstring"]}"""')
        lines += _emit_statements(contract["statements"], "    ")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", notes
