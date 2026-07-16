"""CLI entry point: run a configurable chain of dimensionality-reduction /
clustering steps ("analysis pipeline") driven by a config file.

Usage:
    python -m src.pipeline.run_analysis_pipeline --config config/lesion_embedding.json

Each step's result is cached under the config's `cache_root`, keyed by a hash
of everything that produced it (see src.pipeline.checkpoint) - a rerun of the
same config only recomputes steps whose upstream chain actually changed.

This is the pipeline skeleton only: STEP_REGISTRY (src.analysis.steps) is
currently empty, so a real config naming real steps does not exist yet - the
`registry` parameter on main()/run_steps() lets tests exercise this CLI's own
wiring (config loading, checkpointing, report/log writing) against a small
fake registry, without any real domain step needing to exist yet.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.analysis.config import AnalysisPipelineConfig, load_config
from src.analysis.steps import STEP_REGISTRY, StepDefinition
from src.pipeline.checkpoint import get_or_run
from src.utils.step import StepResult

REPORTS_ROOT = Path("reports") / "analysis_pipeline"
LOGS_ROOT = Path("logs") / "analysis_pipeline"
REPORT_FILENAME_PREFIX = "run_summary"


@dataclass(frozen=True)
class StepRunSummary:
    index: int
    name: str
    cached: bool
    output_shape: tuple[int, ...]
    cache_dir: Path


def run_steps(
    config: AnalysisPipelineConfig, registry: dict[str, StepDefinition]
) -> list[StepRunSummary]:
    """Runs every step in `config.steps` in order, through the checkpoint
    layer, returning a summary per step for the report. `registry` is an
    explicit parameter (not looked up from a module-level import at call
    time) so callers - tests in particular - can inject a small fake
    registry without needing any real step implementation to exist."""
    summaries: list[StepRunSummary] = []
    result: StepResult | None = None
    prior_hash: str | None = None

    for index, step in enumerate(config.steps):
        result, prior_hash, was_cached = get_or_run(
            cache_root=config.cache_root,
            step_index=index,
            step_name=step.name,
            params=step.params,
            prior_chain_hash=prior_hash,
            run_fn=registry[step.name].run,
            step_input=result,
            overwrite=config.overwrite_cache,
        )
        cache_dir = config.cache_root / f"{index:02d}_{step.name}_{prior_hash[:10]}"
        summaries.append(
            StepRunSummary(
                index=index,
                name=step.name,
                cached=was_cached,
                output_shape=result.X.shape,
                cache_dir=cache_dir,
            )
        )
    return summaries


def _config_summary(config: AnalysisPipelineConfig) -> str:
    """JSON dump of the fields actually used from the config file - derived
    from the parsed AnalysisPipelineConfig (not a re-read of the file) so it
    can never drift from what the run actually used."""
    payload = {
        "modality": config.modality,
        "project": config.project,
        "cache_root": str(config.cache_root),
        "overwrite_cache": config.overwrite_cache,
        "steps": [{"name": s.name, "params": s.params} for s in config.steps],
    }
    return json.dumps(payload, indent=2)


def _build_report(config: AnalysisPipelineConfig, summaries: list[StepRunSummary], now: datetime) -> str:
    lines = [
        f"# {config.project}_{config.modality}_{now.strftime('%d-%m-%y')}",
        f"## {now.strftime('%H:%M')}",
        "",
        "## Config",
        "",
        "```json",
        _config_summary(config),
        "```",
        "",
        "## Steps",
        "",
        "| index | step | cached | output shape | cache dir |",
        "|---|---|---|---|---|",
    ]
    for s in summaries:
        cached_label = "yes" if s.cached else "no"
        lines.append(f"| {s.index} | {s.name} | {cached_label} | {s.output_shape} | {s.cache_dir} |")
    return "\n".join(lines)


def _write_report(
    config: AnalysisPipelineConfig, summaries: list[StepRunSummary], now: datetime | None = None
) -> Path:
    now = now or datetime.now()
    report_dir = REPORTS_ROOT / config.project / config.modality
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.md"
    report_path.write_text(_build_report(config, summaries, now))
    return report_path


def _log_path(config: AnalysisPipelineConfig, now: datetime) -> Path:
    log_dir = LOGS_ROOT / config.project / config.modality
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{REPORT_FILENAME_PREFIX}__{now.strftime('%d-%m-%y__%H-%M')}.log"


def _attach_file_handler(log_path: Path) -> None:
    """Persist the same narrative already printed to console into a log
    file. Removes any FileHandler left over from a previous main() call in
    the same process (e.g. repeated invocations in a notebook) - otherwise
    log lines from a later run would keep being written into an earlier
    run's file."""
    root_logger = logging.getLogger()
    for old_handler in [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]:
        root_logger.removeHandler(old_handler)
        old_handler.close()
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root_logger.addHandler(handler)


def main(argv: list[str] | None = None, registry: dict[str, StepDefinition] | None = None) -> int:
    """`registry` defaults to the real STEP_REGISTRY. Tests inject their own
    small fake registry instead, so this CLI's own wiring (argument parsing,
    config validation, checkpointing, report/log writing) can be exercised
    end-to-end without any real domain step needing to exist yet."""
    registry = STEP_REGISTRY if registry is None else registry

    parser = argparse.ArgumentParser(
        description="Run a configurable chain of dimensionality-reduction/clustering steps."
    )
    parser.add_argument("--config", required=True, help="Path to an analysis-pipeline config JSON file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # basicConfig() is a no-op if the root logger already has a handler (e.g. under
    # pytest, or a second call in the same interpreter) - set the level explicitly
    # so INFO records still reach our FileHandler even when that happens.
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = load_config(args.config, registry)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    now = datetime.now()
    try:
        log_path = _log_path(config, now)
        _attach_file_handler(log_path)
    except OSError as exc:
        # No file handler yet at this point - this still reaches the console
        # StreamHandler from basicConfig() above.
        logging.error("cannot set up log file: %s", exc, exc_info=True)
        return 1

    try:
        summaries = run_steps(config, registry)
    except (FileNotFoundError, ValueError, OSError) as exc:
        logging.error("pipeline run failed: %s", exc, exc_info=True)
        return 1

    try:
        report_path = _write_report(config, summaries, now)
    except OSError as exc:
        logging.error("cannot write report: %s", exc, exc_info=True)
        return 1

    logging.info("done - report written to %s, log written to %s", report_path, log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
