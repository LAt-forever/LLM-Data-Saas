import re
from typing import Mapping


_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptValidationError(ValueError):
    pass


def extract_placeholders(body: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(body))


def validate_template(body: str, variables: list[str]) -> None:
    body_vars = extract_placeholders(body)
    declared = set(variables)
    missing = body_vars - declared
    unused = declared - body_vars
    problems = []
    if missing:
        problems.append(f"body uses undeclared variables: {sorted(missing)}")
    if unused:
        problems.append(f"declared but unused variables: {sorted(unused)}")
    if problems:
        raise PromptValidationError("; ".join(problems))


def render_prompt(body: str, values: Mapping[str, str]) -> str:
    needed = extract_placeholders(body)
    missing = needed - set(values)
    if missing:
        raise PromptValidationError(f"missing values for placeholders: {sorted(missing)}")

    def _sub(m: re.Match[str]) -> str:
        return str(values[m.group(1)])

    return _PLACEHOLDER_RE.sub(_sub, body)
