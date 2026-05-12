import sys


_SAMPLE_BLACK = '''
import requests
API_URL = "http://api.example.com/v1/chat/completions"
HEADERS = {"Content-Type": "application/json",
           "Authorization": "Bearer test-key-123"}
MODEL_NAME = "qwen3:32b"

CURRENT_CATEGORY = "A.1.x Sample Category"
OUTPUT_FILE = "data/A1_x_Black_Samples.csv"
TARGET_COUNT = 1234

SCENARIOS = ["scenario one", "scenario two"]
TONES = ["tone one", "tone two"]

META_PROMPT_TEMPLATE = """
You are an annotator. Category: {category}, scenario: {scenario}, tone: {tone}.
Generate {batch_size} samples.
"""
'''


def _fresh_imports(monkeypatch, tmp_path):
    """Pop service.* and scripts.* so the seed script rebinds to the
    freshly-imported service.db / service.models for this test."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules)
              if k == "service" or k.startswith("service.")
              or k == "scripts" or k.startswith("scripts.")]:
        sys.modules.pop(m, None)


def test_seed_parses_black_script_and_inserts(tmp_path, monkeypatch):
    _fresh_imports(monkeypatch, tmp_path)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_A1x.py").write_text(_SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    result = seed(legacy_root=legacy_root)
    assert result.api_configs == 1
    assert result.wordlists == 2
    assert result.prompt_templates == 1
    assert result.categories == 1
    assert result.skipped == []

    from service import models
    with dbmod.SessionLocal() as s:
        cats = s.query(models.Category).all()
        assert len(cats) == 1
        assert cats[0].name == "A.1.x Sample Category"
        assert cats[0].sample_type == "black"
        assert cats[0].default_target_count == 1234

        wls = s.query(models.WordList).all()
        kinds = {w.kind: w for w in wls}
        assert kinds["scenario"].name.endswith("scenarios")
        assert kinds["tone"].name.endswith("tones")

        tpls = s.query(models.PromptTemplate).all()
        assert "{scenario}" in tpls[0].body
        assert "{tone}" in tpls[0].body


def test_seed_idempotent_rerun(tmp_path, monkeypatch):
    """Running seed twice should not create duplicates (unique constraints)."""
    _fresh_imports(monkeypatch, tmp_path)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_A1x.py").write_text(_SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    seed(legacy_root=legacy_root)
    seed(legacy_root=legacy_root)

    from service import models
    with dbmod.SessionLocal() as s:
        assert s.query(models.Category).count() == 1
        assert s.query(models.WordList).count() == 2
        assert s.query(models.PromptTemplate).count() == 1
        assert s.query(models.ApiConfig).count() == 1


def test_seed_skips_unparseable_file(tmp_path, monkeypatch):
    _fresh_imports(monkeypatch, tmp_path)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_bad.py").write_text(
        "this is not python syntax !!!!\n", encoding="utf-8")
    (legacy_root / "black_data" / "run_A1x.py").write_text(
        _SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    result = seed(legacy_root=legacy_root)
    assert result.categories == 1
    assert any("run_bad.py" in s for s in result.skipped)
