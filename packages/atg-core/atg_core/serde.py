"""Deterministic dataclass <-> plain-data serialisation.

The ATG layer must be transport neutral: every canonical object has to survive a
round trip through JSON without depending on a serialisation framework.
"""

from __future__ import annotations

import dataclasses
import typing
from typing import Any, Dict, List, Type, TypeVar, Union

T = TypeVar("T")


def to_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def _is_optional(annotation: Any) -> bool:
    return typing.get_origin(annotation) is Union and type(None) in typing.get_args(annotation)


def _unwrap_optional(annotation: Any) -> Any:
    args = [a for a in typing.get_args(annotation) if a is not type(None)]
    return args[0] if len(args) == 1 else Any


def from_jsonable(cls: Type[T], data: Any) -> T:
    """Rebuild a dataclass tree from plain data, ignoring unknown keys."""
    if data is None:
        return None  # type: ignore[return-value]
    if not (dataclasses.is_dataclass(cls) and isinstance(cls, type)):
        return data
    hints = typing.get_type_hints(cls)
    kwargs: Dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        if field.name not in data:
            continue
        annotation = hints.get(field.name, Any)
        kwargs[field.name] = _coerce(annotation, data[field.name])
    return cls(**kwargs)  # type: ignore[arg-type]


def _coerce(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    if _is_optional(annotation):
        annotation = _unwrap_optional(annotation)
    origin = typing.get_origin(annotation)
    if origin in (list, List):
        (item_type,) = typing.get_args(annotation) or (Any,)
        return [_coerce(item_type, item) for item in value]
    if origin in (dict, Dict):
        return dict(value)
    if dataclasses.is_dataclass(annotation) and isinstance(annotation, type):
        return from_jsonable(annotation, value)
    return value
