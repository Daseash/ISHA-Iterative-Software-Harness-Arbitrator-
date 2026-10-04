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
    # Do not import the backend module here to avoid unintended side effects
    # like clearing the Gcf state.
    return backend

## Patch

```diff

```
