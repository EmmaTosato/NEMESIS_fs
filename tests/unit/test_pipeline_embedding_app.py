"""Unit tests for src/pipeline/embedding_app.py's main() (the CLI entry point) -
AUDIT_FINDINGS.md #45: this file didn't exist before, main()'s own error handling
(specifically app.run()'s OSError) had no test coverage of its own (only
src/analysis/embedding_app.py's underlying functions were tested).
"""

from src.analysis.embedding_app import ProductionRun
from src.pipeline import embedding_app


def _fake_run():
    return ProductionRun(modality="lesion", pipeline="dim_reduction", method="umap", run_name="run-a", path=None)


def test_main_no_production_runs_found_returns_1(tmp_path, monkeypatch):
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [])
    exit_code = embedding_app.main(["--results-root", str(tmp_path)])
    assert exit_code == 1


def test_main_server_port_in_use_returns_1_not_raw_traceback(tmp_path, monkeypatch):
    """AUDIT_FINDINGS.md #45 regression: app.run() used to have no try/except at all - an
    OSError from a port already in use (a realistic scenario: a leftover instance of this
    same app already running) propagated as a raw traceback instead of a clean return 1."""
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [_fake_run()])

    class _FakeApp:
        def run(self, debug, port):
            raise OSError(f"[Errno 48] Address already in use: {port}")

    monkeypatch.setattr(embedding_app, "build_app", lambda runs: _FakeApp())

    exit_code = embedding_app.main(["--results-root", str(tmp_path), "--port", "8060"])
    assert exit_code == 1


def test_main_build_app_value_error_returns_1(tmp_path, monkeypatch):
    monkeypatch.setattr(embedding_app, "discover_production_runs", lambda results_root: [_fake_run()])

    def _raise(runs):
        raise ValueError("mixed pipelines with incompatible run shapes")

    monkeypatch.setattr(embedding_app, "build_app", _raise)

    exit_code = embedding_app.main(["--results-root", str(tmp_path)])
    assert exit_code == 1
