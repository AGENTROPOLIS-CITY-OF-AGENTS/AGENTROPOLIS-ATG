"""Shell dialect semantics.

PowerShell is not a POSIX shell with different spelling: the pipeline carries
typed objects rather than bytes, error handling is separate from exit codes and
globbing happens in a different place. Those divergences are returned
explicitly instead of being smoothed over by a token-level rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

POSIX_DIALECTS = ("sh", "bash", "zsh")
OBJECT_DIALECTS = ("powershell",)


@dataclass
class ShellOperation:
    op: str
    arguments: List[str] = field(default_factory=list)
    raw: str = ""


PIPELINE_MODEL = {
    "sh": "byte-stream",
    "bash": "byte-stream",
    "zsh": "byte-stream",
    "powershell": "object-stream",
}

DIVERGENCES = [
    {
        "id": "shell.divergence.pipeline_model",
        "statement": "POSIX pipelines carry untyped bytes; PowerShell pipelines carry typed .NET objects.",
        "impact": "high",
        "consequence": "Text-parsing stages (awk/cut/sed) have no behavioural equivalent on objects.",
    },
    {
        "id": "shell.divergence.error_channel",
        "statement": (
            "POSIX signals failure with exit status; PowerShell distinguishes "
            "terminating errors, $LASTEXITCODE and $?."
        ),
        "impact": "high",
        "consequence": "`set -e` semantics are not reproduced by $ErrorActionPreference.",
    },
    {
        "id": "shell.divergence.globbing",
        "statement": (
            "POSIX shells expand globs before invoking the command; "
            "PowerShell passes wildcards to the cmdlet."
        ),
        "impact": "medium",
        "consequence": "Argument counts and quoting behaviour differ for wildcard-bearing commands.",
    },
    {
        "id": "shell.divergence.word_splitting",
        "statement": "POSIX performs word splitting and field separation via IFS; PowerShell does not.",
        "impact": "medium",
        "consequence": "Unquoted variable expansion is not behaviour preserving in either direction.",
    },
    {
        "id": "shell.divergence.exit_semantics",
        "statement": "PowerShell cmdlets return objects; native exit codes only exist for external executables.",
        "impact": "medium",
        "consequence": "Scripts that branch on exit status must be restructured, not transliterated.",
    },
]

COMMAND_MAP: Dict[str, Dict[str, Any]] = {
    "list_directory": {
        "sh": "ls",
        "powershell": "Get-ChildItem",
        "equivalence": "partial",
        "note": "ls emits formatted text lines; Get-ChildItem emits FileSystemInfo objects.",
    },
    "remove_recursive": {
        "sh": "rm -rf",
        "powershell": "Remove-Item -Recurse -Force",
        "equivalence": "partial",
        "note": "PowerShell honours providers and -WhatIf; rm operates on the filesystem only.",
    },
    "filter_lines": {
        "sh": "grep",
        "powershell": "Where-Object",
        "equivalence": "none",
        "note": "grep filters text lines; Where-Object filters objects by property predicate.",
    },
    "select_field": {
        "sh": "awk '{print $1}'",
        "powershell": "Select-Object -First 1 -ExpandProperty Name",
        "equivalence": "none",
        "note": "Positional field extraction has no object-model equivalent.",
    },
    "print": {
        "sh": "echo",
        "powershell": "Write-Output",
        "equivalence": "partial",
        "note": "Write-Output emits an object to the pipeline; echo writes bytes to stdout.",
    },
    "set_variable": {
        "sh": "VAR=value",
        "powershell": "$Var = 'value'",
        "equivalence": "partial",
        "note": "POSIX variables are strings; PowerShell variables are typed objects.",
    },
}

_POSIX_TOKENS = {
    "ls": "list_directory",
    "rm": "remove_recursive",
    "grep": "filter_lines",
    "awk": "select_field",
    "echo": "print",
}

_PS_TOKENS = {
    "get-childitem": "list_directory",
    "remove-item": "remove_recursive",
    "where-object": "filter_lines",
    "select-object": "select_field",
    "write-output": "print",
}


def parse_pipeline(script: str, dialect: str) -> List[ShellOperation]:
    tokens = _PS_TOKENS if dialect in OBJECT_DIALECTS else _POSIX_TOKENS
    operations: List[ShellOperation] = []
    for stage in script.strip().split("|"):
        stage = stage.strip()
        if not stage:
            continue
        head = stage.split()[0].lower()
        op = tokens.get(head)
        if op is None:
            operations.append(ShellOperation(op="unknown_command", arguments=[stage], raw=stage))
        else:
            operations.append(ShellOperation(op=op, arguments=stage.split()[1:], raw=stage))
    return operations


def translate_pipeline(
    script: str, source_dialect: str, target_dialect: str
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (translated script, applied mappings, semantic divergences)."""
    operations = parse_pipeline(script, source_dialect)
    source_model = PIPELINE_MODEL.get(source_dialect)
    target_model = PIPELINE_MODEL.get(target_dialect)
    if source_model is None or target_model is None:
        raise ValueError(f"unsupported shell dialect pair: {source_dialect} -> {target_dialect}")

    divergences: List[Dict[str, Any]] = []
    if source_model != target_model:
        divergences = [dict(item) for item in DIVERGENCES]

    applied: List[Dict[str, Any]] = []
    stages: List[str] = []
    target_key = "powershell" if target_dialect in OBJECT_DIALECTS else "sh"
    for operation in operations:
        entry = COMMAND_MAP.get(operation.op)
        if entry is None:
            applied.append(
                {
                    "rule_id": f"shell.unmapped.{operation.op}",
                    "op": operation.op,
                    "equivalence": "none",
                    "note": f"no registered semantic mapping for {operation.raw!r}",
                    "escalate": True,
                }
            )
            stages.append(f"# UNMAPPED: {operation.raw}")
            continue
        stages.append(entry[target_key])
        applied.append(
            {
                "rule_id": f"shell.map.{source_dialect}_{target_dialect}.{operation.op}",
                "op": operation.op,
                "source_form": entry["sh" if source_dialect not in OBJECT_DIALECTS else "powershell"],
                "target_form": entry[target_key],
                "equivalence": entry["equivalence"],
                "note": entry["note"],
                "escalate": entry["equivalence"] == "none",
            }
        )
    return " | ".join(stages), applied, divergences


def pipeline_model(dialect: str) -> str:
    model = PIPELINE_MODEL.get(dialect)
    if model is None:
        raise ValueError(f"unsupported shell dialect: {dialect}")
    return model
