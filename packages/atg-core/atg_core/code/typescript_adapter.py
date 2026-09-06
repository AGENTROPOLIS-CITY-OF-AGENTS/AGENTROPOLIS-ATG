"""TypeScript <-> ATG behavioural IR.

Only the subset that the emitter produces is parsed back. Anything outside the
subset raises :class:`UnsupportedConstruct` rather than being silently accepted,
because an unparsed construct cannot be proven equivalent.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from . import ir

TS_TYPE_FROM_CANONICAL = {
    "integer": ("number", "TypeScript has no integer type; integer widens to IEEE-754 double"),
    "number": ("number", ""),
    "string": ("string", ""),
    "boolean": ("boolean", ""),
    "void": ("void", ""),
    "unknown": ("unknown", ""),
}

CANONICAL_FROM_TS = {"number": "number", "string": "string", "boolean": "boolean", "void": "void", "unknown": "unknown"}

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<number>\d+\.\d+|\d+)
  | (?P<string>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
  | (?P<op>===|!==|=>|<=|>=|\|\||&&|[(){}\[\];:,.<>+\-*/=?|])
  | (?P<ident>[A-Za-z_$][A-Za-z0-9_$]*)
    """,
    re.VERBOSE | re.DOTALL,
)


class _Token:
    __slots__ = ("kind", "value", "pos")

    def __init__(self, kind: str, value: str, pos: int) -> None:
        self.kind, self.value, self.pos = kind, value, pos

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{self.kind}:{self.value}>"


def _tokenize(source: str) -> List[_Token]:
    tokens: List[_Token] = []
    index = 0
    while index < len(source):
        match = _TOKEN_RE.match(source, index)
        if not match:
            raise ir.UnsupportedConstruct("typescript.token", source[index : index + 20])
        index = match.end()
        kind = match.lastgroup or ""
        if kind in ("ws", "comment"):
            continue
        tokens.append(_Token(kind, match.group(), match.start()))
    return tokens


class _Parser:
    def __init__(self, tokens: List[_Token]) -> None:
        self.tokens = tokens
        self.i = 0

    # -- token helpers -------------------------------------------------
    def peek(self, offset: int = 0) -> Optional[_Token]:
        index = self.i + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def at(self, value: str) -> bool:
        token = self.peek()
        return token is not None and token.value == value

    def eat(self, value: str) -> bool:
        if self.at(value):
            self.i += 1
            return True
        return False

    def expect(self, value: str) -> _Token:
        token = self.peek()
        if token is None or token.value != value:
            raise ir.UnsupportedConstruct("typescript.expected", f"{value!r} got {token.value if token else 'EOF'!r}")
        self.i += 1
        return token

    def expect_ident(self) -> str:
        token = self.peek()
        if token is None or token.kind != "ident":
            raise ir.UnsupportedConstruct("typescript.identifier", token.value if token else "EOF")
        self.i += 1
        return token.value

    # -- grammar -------------------------------------------------------
    def parse_functions(self) -> List[Dict[str, Any]]:
        contracts = []
        while self.peek() is not None:
            contracts.append(self.parse_function())
        if not contracts:
            raise ir.UnsupportedConstruct("typescript.module", "no function declarations found")
        return contracts

    def parse_function(self) -> Dict[str, Any]:
        self.eat("export")
        self.expect("function")
        name = self.expect_ident()
        self.expect("(")
        params = []
        while not self.at(")"):
            param_name = self.expect_ident()
            optional = self.eat("?")
            self.expect(":")
            param_type = self.parse_type()
            default = None
            if self.eat("="):
                default = self.parse_expression()
            params.append(
                {
                    "name": ir.to_snake_case(param_name),
                    "type": param_type,
                    "optional": optional or default is not None,
                    "default": default,
                }
            )
            if not self.eat(","):
                break
        self.expect(")")
        self.expect(":")
        returns = self.parse_type()
        statements = self.parse_block()
        errors = sorted({s["error"] for s in _walk(statements) if s.get("stmt") == "raise"})
        return {
            "name": ir.to_snake_case(name),
            "params": params,
            "returns": returns,
            "errors": errors,
            "docstring": "",
            "statements": statements,
        }

    def parse_type(self) -> str:
        base = self.expect_ident()
        if self.eat("<"):
            args = [self.parse_type()]
            while self.eat(","):
                args.append(self.parse_type())
            self.expect(">")
            if base == "Record":
                base = f"map<{args[0]},{args[-1]}>"
            elif base == "Array":
                base = f"list<{args[0]}>"
            else:
                base = f"{base.lower()}<{','.join(args)}>"
        else:
            base = CANONICAL_FROM_TS.get(base, base.lower())
        while self.eat("["):
            self.expect("]")
            base = f"list<{base}>"
        if self.at("|") and self.peek(1) is not None and self.peek(1).value == "null":
            self.expect("|")
            self.expect("null")
            base = f"optional<{base}>"
        return base

    def parse_block(self) -> List[Dict[str, Any]]:
        self.expect("{")
        statements = []
        while not self.at("}"):
            statements.append(self.parse_statement())
        self.expect("}")
        return statements

    def parse_statement(self) -> Dict[str, Any]:
        token = self.peek()
        if token is None:
            raise ir.UnsupportedConstruct("typescript.statement", "EOF")
        if token.value == "if":
            self.i += 1
            self.expect("(")
            test = self.parse_expression()
            self.expect(")")
            then = self.parse_block()
            orelse: List[Dict[str, Any]] = []
            if self.eat("else"):
                orelse = self.parse_block()
            return ir.stmt_if(test, then, orelse)
        if token.value == "throw":
            self.i += 1
            self.expect("new")
            self.expect_ident()
            self.expect("(")
            message_expr = self.parse_expression()
            self.expect(")")
            self.eat(";")
            if message_expr.get("node") != "const":
                raise ir.UnsupportedConstruct("typescript.throw_message", "non-literal error message")
            return _decode_error(str(message_expr["value"]))
        if token.value in ("const", "let"):
            self.i += 1
            target = self.expect_ident()
            self.expect("=")
            value = self.parse_expression()
            self.eat(";")
            return ir.stmt_assign(ir.to_snake_case(target), value)
        if token.value == "return":
            self.i += 1
            if self.eat(";"):
                return ir.stmt_return(None)
            value = self.parse_expression()
            self.eat(";")
            return ir.stmt_return(value)
        raise ir.UnsupportedConstruct("typescript.statement", token.value)

    # -- expressions ---------------------------------------------------
    def parse_expression(self) -> Dict[str, Any]:
        return ir.normalize_expression(self.parse_comparison())

    def parse_comparison(self) -> Dict[str, Any]:
        left = self.parse_additive()
        token = self.peek()
        if token and token.value in ("===", "!==", "<", "<=", ">", ">="):
            self.i += 1
            op = {"===": "==", "!==": "!="}.get(token.value, token.value)
            return ir.compare(op, left, self.parse_additive())
        return left

    def parse_additive(self) -> Dict[str, Any]:
        node = self.parse_multiplicative()
        while True:
            token = self.peek()
            if token and token.value in ("+", "-"):
                self.i += 1
                node = ir.binop(token.value, node, self.parse_multiplicative())
            else:
                return node

    def parse_multiplicative(self) -> Dict[str, Any]:
        node = self.parse_unary()
        while True:
            token = self.peek()
            if token and token.value in ("*", "/", "%"):
                self.i += 1
                node = ir.binop(token.value, node, self.parse_unary())
            else:
                return node

    def parse_unary(self) -> Dict[str, Any]:
        if self.eat("-"):
            return ir.binop("-", ir.const(0, "integer"), self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> Dict[str, Any]:
        node = self.parse_primary()
        while self.at("."):
            self.expect(".")
            member = self.expect_ident()
            if self.at("("):
                args = self.parse_arguments()
                if node.get("node") == "name" and node.get("id") == "Math":
                    node = ir.call(member, args)
                else:
                    node = ir.call(member, [node] + args)
            elif member == "length":
                node = ir.call("length", [node])
            else:
                raise ir.UnsupportedConstruct("typescript.member", member)
        return node

    def parse_arguments(self) -> List[Dict[str, Any]]:
        self.expect("(")
        args: List[Dict[str, Any]] = []
        while not self.at(")"):
            args.append(self.parse_expression())
            if not self.eat(","):
                break
        self.expect(")")
        return args

    def parse_primary(self) -> Dict[str, Any]:
        token = self.peek()
        if token is None:
            raise ir.UnsupportedConstruct("typescript.expression", "EOF")
        if token.kind == "number":
            self.i += 1
            value = float(token.value) if "." in token.value else int(token.value)
            return ir.const(value, "number" if "." in token.value else "integer")
        if token.kind == "string":
            self.i += 1
            return ir.const(_decode_string(token.value), "string")
        if token.value in ("true", "false"):
            self.i += 1
            return ir.const(token.value == "true", "boolean")
        if token.value == "(":
            arrow = self._try_parse_arrow()
            if arrow is not None:
                return arrow
            self.expect("(")
            inner = self.parse_expression()
            self.expect(")")
            return inner
        if token.kind == "ident":
            self.i += 1
            if self.at("("):
                args = self.parse_arguments()
                return ir.call(token.value, args)
            return ir.name(token.value)
        raise ir.UnsupportedConstruct("typescript.expression", token.value)

    def _try_parse_arrow(self) -> Optional[Dict[str, Any]]:
        start = self.i
        try:
            self.expect("(")
            params: List[str] = []
            while not self.at(")"):
                params.append(self.expect_ident())
                if not self.eat(","):
                    break
            self.expect(")")
            self.expect("=>")
        except ir.UnsupportedConstruct:
            self.i = start
            return None
        body = self.parse_expression()
        return ir.lambda_(params, body)


def _decode_string(raw: str) -> str:
    return raw[1:-1].replace('\\"', '"').replace("\\'", "'").replace("\\\\", "\\")


_ERROR_PREFIX = re.compile(r"^([a-z_]+):\s*(.*)$", re.DOTALL)


def _decode_error(message: str) -> Dict[str, Any]:
    match = _ERROR_PREFIX.match(message)
    if match:
        return ir.stmt_raise(match.group(1), match.group(2))
    return ir.stmt_raise("invalid_argument", message)


def _walk(statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for statement in statements:
        out.append(statement)
        if statement.get("stmt") == "if":
            out += _walk(statement.get("then", []))
            out += _walk(statement.get("else", []))
    return out


def parse_functions(source: str) -> List[Dict[str, Any]]:
    return _Parser(_tokenize(source)).parse_functions()


# -- emission ----------------------------------------------------------------

def _ts_type(canonical: str, notes: List[str]) -> str:
    if canonical.startswith("list<"):
        return f"{_ts_type(canonical[5:-1], notes)}[]"
    if canonical.startswith("optional<"):
        return f"{_ts_type(canonical[9:-1], notes)} | null"
    if canonical.startswith("map<"):
        key, value = canonical[4:-1].split(",", 1)
        return f"Record<{_ts_type(key, notes)}, {_ts_type(value, notes)}>"
    mapped, note = TS_TYPE_FROM_CANONICAL.get(canonical, (canonical, ""))
    if note and note not in notes:
        notes.append(note)
    return mapped


def _emit_expr(node: Dict[str, Any]) -> str:
    kind = node["node"]
    if kind == "name":
        return ir.to_camel_case(node["id"])
    if kind == "const":
        value = node["value"]
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, bool):
            return "true" if value else "false"
        return repr(value)
    if kind == "call":
        return _emit_call(node)
    if kind == "binop":
        return f"({_emit_expr(node['left'])} {node['op']} {_emit_expr(node['right'])})"
    if kind == "compare":
        op = {"==": "===", "!=": "!=="}.get(node["op"], node["op"])
        return f"{_emit_expr(node['left'])} {op} {_emit_expr(node['right'])}"
    if kind == "lambda":
        return "(" + ", ".join(node["params"]) + ") => " + _emit_expr(node["body"])
    raise ir.UnsupportedConstruct("typescript.emit_expression", kind)


def _emit_call(node: Dict[str, Any]) -> str:
    fn, args = node["fn"], node["args"]
    if fn == "length" and len(args) == 1:
        return f"{_emit_expr(args[0])}.length"
    if fn == "sum" and len(args) == 1:
        return f"{_emit_expr(args[0])}.reduce((acc, value) => acc + value, 0)"
    if fn in ("min", "max", "abs", "round"):
        return f"Math.{fn}(" + ", ".join(_emit_expr(a) for a in args) + ")"
    return f"{ir.to_camel_case(fn)}(" + ", ".join(_emit_expr(a) for a in args) + ")"


def _emit_statements(statements: List[Dict[str, Any]], indent: str) -> List[str]:
    lines: List[str] = []
    for statement in statements:
        kind = statement["stmt"]
        if kind == "if":
            lines.append(f"{indent}if ({_emit_expr(statement['test'])}) {{")
            lines += _emit_statements(statement["then"], indent + "  ")
            if statement.get("else"):
                lines.append(f"{indent}}} else {{")
                lines += _emit_statements(statement["else"], indent + "  ")
            lines.append(f"{indent}}}")
        elif kind == "raise":
            message = f"{statement['error']}: {statement['message']}".replace('"', '\\"')
            lines.append(f'{indent}throw new Error("{message}");')
        elif kind == "assign":
            lines.append(f"{indent}const {ir.to_camel_case(statement['target'])} = {_emit_expr(statement['value'])};")
        elif kind == "return":
            value = statement.get("value")
            lines.append(f"{indent}return {_emit_expr(value)};" if value else f"{indent}return;")
        else:
            raise ir.UnsupportedConstruct("typescript.emit_statement", kind)
    return lines


def emit_functions(contracts: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    notes: List[str] = []
    lines: List[str] = []
    for contract in contracts:
        if contract.get("docstring"):
            lines.append(f"/** {contract['docstring']} */")
        params = ", ".join(
            f"{ir.to_camel_case(p['name'])}: {_ts_type(p['type'], notes)}"
            + (f" = {_emit_expr(p['default'])}" if p.get("default") else "")
            for p in contract["params"]
        )
        returns = _ts_type(contract["returns"], notes)
        lines.append(f"export function {ir.to_camel_case(contract['name'])}({params}): {returns} {{")
        lines += _emit_statements(contract["statements"], "  ")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", notes
