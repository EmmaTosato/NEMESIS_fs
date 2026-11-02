"""One module per panel of the page: a block of the Embedding Explorer that a run either has
or does not have (the component maps only for a PCA run, everything about clusters only for a
clustering run).

A panel reads a run and returns the components that show it. It holds no app state and
registers no callback of its own yet - build_app still wires them.
"""
