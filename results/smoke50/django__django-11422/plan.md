# django__django-11422

## Plan

@functools.lru_cache(maxsize=1)
def iter_modules_and_files(modules, extra_files):
    ...
    results = set()
    for filename in itertools.chain(sys_file_paths, extra_files):
        if not filename:
            continue
        path = pathlib.Path(filename)
        if not path.exists():
            continue
        results.add(path.resolve().absolute())
    return frozenset(results)

## Patch

```diff

```
