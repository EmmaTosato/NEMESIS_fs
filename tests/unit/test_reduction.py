"""Unit tests for src/analysis/reduction.py."""

import numpy as np

from src.analysis.reduction import REDUCTION_METHODS, pca_embed, tsne_embed, umap_embed

_X = np.random.default_rng(0).random((30, 15))


def test_registry_has_expected_methods():
    assert set(REDUCTION_METHODS) == {"umap", "tsne", "pca"}
    assert REDUCTION_METHODS["umap"] is umap_embed
    assert REDUCTION_METHODS["tsne"] is tsne_embed
    assert REDUCTION_METHODS["pca"] is pca_embed


def test_pca_embed_shape_and_determinism():
    params = {"n_components": 3}
    out1 = pca_embed(_X, params)
    out2 = pca_embed(_X, params)
    assert out1.shape == (30, 3)
    assert np.allclose(out1, out2)  # PCA is deterministic, no random_state needed


def test_umap_embed_shape():
    out = umap_embed(_X, {"n_neighbors": 5, "min_dist": 0.1, "n_components": 2, "random_state": 0})
    assert out.shape == (30, 2)


def test_tsne_embed_shape():
    out = tsne_embed(_X, {"perplexity": 5, "n_components": 2, "random_state": 0})
    assert out.shape == (30, 2)
