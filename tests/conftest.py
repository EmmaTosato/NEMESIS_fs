"""Configurazione pytest condivisa.

- backend matplotlib non interattivo (nessuna finestra, nessuna dipendenza dal display);
- profilo `hypothesis` deterministico: i fallimenti sono sempre riproducibili con lo stesso seed
  (`derandomize=True`), senza database di esempi locale e senza limite di tempo per esempio
  (i test sono veloci, ma il primo import di sklearn/scipy no).
"""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from hypothesis import HealthCheck, settings

settings.register_profile(
    "nemesis",
    max_examples=60,
    derandomize=True,
    deadline=None,
    database=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
settings.load_profile("nemesis")


@pytest.fixture
def rng() -> np.random.Generator:
    """Generatore con seed fisso: stesso test, stessi dati, sempre."""
    return np.random.default_rng(12345)


@pytest.fixture
def lesion_matrix_run(tmp_path, monkeypatch):
    """Cartella di una vera run di `build_lesion_matrix` (8 soggetti, 10x10x10, voxelwise)."""
    from tests.factories.lesion_dataset import run_build_lesion_matrix

    return run_build_lesion_matrix(tmp_path, monkeypatch)
