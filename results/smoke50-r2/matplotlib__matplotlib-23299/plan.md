# matplotlib__matplotlib-23299

## Plan

def get_backend():
    """
    Return the name of the current backend.
    """
    from matplotlib import rcParams, rcsetup
    backend = rcParams["backend"]
    if backend is None:
        backend = rcsetup.defaultBackend
    # Import the backend module to ensure it is loaded.
    import importlib
    importlib.import_module(f"matplotlib.backends.backend_{backend}")
    return backend

## Patch

```diff

```
