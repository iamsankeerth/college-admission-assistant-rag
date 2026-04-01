# Testing Guide

## Running Tests

```bash
pytest
```

## CI Environment

All tests run on **Ubuntu Latest** in GitHub Actions. See `.github/workflows/ci.yml`.

## Windows Local Development

Some Windows environments block access to pytest's default system-temp directory (`%TEMP%`), which can cause permission errors in tests that use `tmp_path`. Two tests in this project are affected:

- `test_ingestion_service_indexes_local_file` (`tests/test_official_retrieval_and_verification.py`)
- `test_run_full_eval_without_gemini_key_writes_skipped_report` (`tests/test_full_eval.py`)

Both are switched to use the `workspace_tmp_path` fixture (defined in `tests/conftest.py`), which creates a repo-local temp directory at `tmp_test/` instead of relying on the system temp.

## workspace_tmp_path Fixture

```python
@pytest.fixture
def workspace_tmp_path():
    tmp_dir = ROOT / "tmp_test"
    tmp_dir.mkdir(exist_ok=True)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)
```

The `tmp_test/` directory is git-ignored. Switch any additional test that encounters Windows temp-permission failures to this fixture instead of the standard `tmp_path`.
