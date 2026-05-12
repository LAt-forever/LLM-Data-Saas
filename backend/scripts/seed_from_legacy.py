"""One-shot migration: read llm-data-create/ scripts -> populate the DB.

Idempotent: re-runs will not create duplicates because:
  - ApiConfig.name is unique
  - WordList.name is unique
  - PromptTemplate.name is unique
  - Category(sample_type, name) is unique
"""
import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from service import crud, db as dbmod, models
from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


@dataclass
class SeedResult:
    api_configs: int = 0
    wordlists: int = 0
    prompt_templates: int = 0
    categories: int = 0
    skipped: list[str] = field(default_factory=list)


def _module_top_level_literals(path: Path) -> dict:
    """Return a dict of top-level NAME = literal assignments. Skip any
    statement that contains non-literal expressions (calls, attribute access,
    etc.) -- we only want simple constants and list/dict of literals."""
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src, filename=str(path))
    out: dict = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        out[name] = value
    return out


def _extract_call_kwargs(path: Path, names: set[str]) -> dict:
    """Walk the module AST. For every Call node, collect keyword args whose
    name is in `names` and whose value is a string literal. Return the FIRST
    such value per name. Uses utf-8-sig so BOM-prefixed files parse cleanly."""
    src = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return {}
    result: dict = {}
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        for kw in n.keywords:
            if (kw.arg in names
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                    and kw.arg not in result):
                result[kw.arg] = kw.value.value
    return result


def _ensure_api_config(db, *, name, base_url, api_key, model_name, api_type) -> int:
    obj = db.query(models.ApiConfig).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_api_config(db, ApiConfigCreate(
        name=name, base_url=base_url, api_key=api_key,
        model_name=model_name, type=api_type))
    return obj.id


def _ensure_wordlist(db, *, name, kind, items) -> int:
    obj = db.query(models.WordList).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_wordlist(db, WordListCreate(name=name, kind=kind, items=items))
    return obj.id


def _ensure_template(db, *, name, body, variables) -> int:
    obj = db.query(models.PromptTemplate).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_prompt_template(db, PromptTemplateCreate(
        name=name, body=body, variables=variables))
    return obj.id


def _ensure_category(db, *, sample_type, name, prompt_template_id,
                     scenario_list_id, tone_list_id, default_target_count) -> int:
    obj = db.query(models.Category).filter_by(
        sample_type=sample_type, name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_category(db, CategoryCreate(
        sample_type=sample_type, name=name, description="",
        prompt_template_id=prompt_template_id,
        scenario_list_id=scenario_list_id,
        tone_list_id=tone_list_id,
        default_target_count=default_target_count))
    return obj.id


def _seed_black_file(db, path: Path, result: SeedResult) -> None:
    consts = _module_top_level_literals(path)
    cat_name = consts.get("CURRENT_CATEGORY")
    scenarios = consts.get("SCENARIOS")
    tones = consts.get("TONES")
    body = consts.get("META_PROMPT_TEMPLATE")
    api_url = consts.get("API_URL")
    headers = consts.get("HEADERS")
    model_name = consts.get("MODEL_NAME")
    target_count = consts.get("TARGET_COUNT", 0)

    if not all([cat_name, scenarios, tones, body, api_url, headers, model_name]):
        result.skipped.append(f"{path.name}: missing one of required constants")
        return

    auth = headers.get("Authorization", "") if isinstance(headers, dict) else ""
    api_key = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else auth

    _ensure_api_config(
        db, name=f"black/{model_name}", base_url=api_url.rsplit("/v1/", 1)[0],
        api_key=api_key, model_name=model_name, api_type="raw")
    s_id = _ensure_wordlist(db, name=f"{path.stem}-scenarios",
                            kind="scenario", items=list(scenarios))
    t_id = _ensure_wordlist(db, name=f"{path.stem}-tones",
                            kind="tone", items=list(tones))
    tpl_id = _ensure_template(
        db, name=f"{path.stem}-template", body=body,
        variables=["category", "scenario", "tone", "batch_size"])
    _ensure_category(
        db, sample_type="black", name=cat_name,
        prompt_template_id=tpl_id, scenario_list_id=s_id, tone_list_id=t_id,
        default_target_count=int(target_count) if target_count else 0)


def _seed_gray_white_file(db, path: Path, sample_type: str, result: SeedResult) -> None:
    consts = _module_top_level_literals(path)
    call_kwargs = _extract_call_kwargs(path, {"base_url"})
    scenarios = (consts.get("GRAY_SCENARIOS")
                 or consts.get("WHITE_SCENARIOS")
                 or consts.get("SCENARIOS"))
    tones = consts.get("TONES")
    templates = consts.get("META_TEMPLATES")
    api_key = consts.get("PROXY_API_KEY") or consts.get("DEEPSEEK_API_KEY")
    base_url = (consts.get("base_url")
                or consts.get("BASE_URL")
                or call_kwargs.get("base_url")
                or "https://api.deepseek.com")
    model_name = consts.get("MODEL_NAME")
    target_count = consts.get("TARGET_COUNT", 0)

    if not all([scenarios, tones, templates, api_key, model_name]):
        result.skipped.append(f"{path.name}: missing one of required constants")
        return

    body = "\n\n[VARIANT-BREAK]\n\n".join(str(t) for t in templates)

    _ensure_api_config(
        db, name=f"{sample_type}/{model_name}",
        base_url=base_url, api_key=api_key,
        model_name=model_name, api_type="openai")
    s_id = _ensure_wordlist(db, name=f"{sample_type}-scenarios",
                            kind="scenario", items=list(scenarios))
    t_id = _ensure_wordlist(db, name=f"{sample_type}-tones",
                            kind="tone", items=list(tones))
    tpl_id = _ensure_template(
        db, name=f"{sample_type}-template", body=body,
        variables=["scenario", "tone", "batch_size"])
    _ensure_category(
        db, sample_type=sample_type, name=f"{sample_type}-default",
        prompt_template_id=tpl_id, scenario_list_id=s_id, tone_list_id=t_id,
        default_target_count=int(target_count) if target_count else 0)


def _counts() -> dict:
    with dbmod.SessionLocal() as s:
        return {
            "api_config": s.query(models.ApiConfig).count(),
            "wordlist": s.query(models.WordList).count(),
            "prompt_template": s.query(models.PromptTemplate).count(),
            "category": s.query(models.Category).count(),
        }


def seed(*, legacy_root: Path) -> SeedResult:
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    result = SeedResult()
    pre = _counts()

    with dbmod.SessionLocal() as db:
        # Black samples
        black_dir = legacy_root / "black_data"
        if black_dir.is_dir():
            for p in sorted(black_dir.glob("run_*.py")):
                try:
                    _seed_black_file(db, p, result)
                except (SyntaxError, ValueError, IntegrityError) as e:
                    db.rollback()
                    result.skipped.append(f"{p.name}: {type(e).__name__}: {e}")

        # Gray + white
        for sample_type, rel in [("gray", "gray_data/code/generate_gray_deepseek.py"),
                                 ("white", "white_data/code/generate_white_deepseek.py")]:
            f = legacy_root / rel
            if not f.is_file():
                continue
            try:
                _seed_gray_white_file(db, f, sample_type, result)
            except (SyntaxError, ValueError, IntegrityError) as e:
                db.rollback()
                result.skipped.append(f"{f.name}: {type(e).__name__}: {e}")

    post = _counts()
    result.api_configs = post["api_config"] - pre["api_config"]
    result.wordlists = post["wordlist"] - pre["wordlist"]
    result.prompt_templates = post["prompt_template"] - pre["prompt_template"]
    result.categories = post["category"] - pre["category"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-root", type=Path,
                        default=Path("../llm-data-create"))
    args = parser.parse_args()
    result = seed(legacy_root=args.legacy_root)
    print(json.dumps({
        "api_configs": result.api_configs,
        "wordlists": result.wordlists,
        "prompt_templates": result.prompt_templates,
        "categories": result.categories,
        "skipped": result.skipped,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
