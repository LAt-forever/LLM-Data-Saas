import pytest
from pydantic import ValidationError

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate,
    CategoryCreate, TaskCreate
)


def test_api_config_create_valid():
    cfg = ApiConfigCreate(name="x", base_url="http://a", api_key="k",
                          model_name="m", type="openai")
    assert cfg.type == "openai"


def test_api_config_create_rejects_bad_type():
    with pytest.raises(ValidationError):
        ApiConfigCreate(name="x", base_url="http://a", api_key="k",
                        model_name="m", type="bogus")


def test_wordlist_create_requires_items_list():
    wl = WordListCreate(name="s", kind="scenario", items=["a", "b"])
    assert wl.items == ["a", "b"]
    with pytest.raises(ValidationError):
        WordListCreate(name="s", kind="banned", items=[])


def test_task_create_param_bounds():
    base = dict(category_id=1, api_config_id=1, target_count=10,
                batch_size=5, max_workers=2, max_per_file=1000)
    TaskCreate(**base)
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "target_count": 0})
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "max_workers": 999})
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "batch_size": 9999})


def test_wordlist_update_rejects_empty_items():
    from service.schemas import WordListUpdate
    WordListUpdate(items=["a"])      # OK
    WordListUpdate(items=None)       # OK (means: don't update items)
    WordListUpdate()                 # OK (no fields set)
    with pytest.raises(ValidationError):
        WordListUpdate(items=[])     # explicit empty list rejected
