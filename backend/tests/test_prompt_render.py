import pytest
from service.prompt_render import (
    extract_placeholders, validate_template,
    render_prompt, PromptValidationError
)


def test_extract_placeholders_basic():
    s = "hi {a} and {b} and {a}"
    assert extract_placeholders(s) == {"a", "b"}


def test_validate_template_ok():
    validate_template("hi {x} {y}", ["x", "y"])


def test_validate_template_missing_var_declaration():
    with pytest.raises(PromptValidationError):
        validate_template("hi {x} {y}", ["x"])


def test_validate_template_unused_declared_var():
    with pytest.raises(PromptValidationError):
        validate_template("hi {x}", ["x", "y"])


def test_render_prompt_substitutes():
    out = render_prompt("hi {scenario} {tone}",
                       {"scenario": "a", "tone": "b"})
    assert out == "hi a b"


def test_render_prompt_strict_missing_key():
    with pytest.raises(PromptValidationError):
        render_prompt("hi {missing}", {})
