# django__django-11133

## Plan

@content.setter
def content(self, value):
    # Convert memoryview to bytes
    if isinstance(value, memoryview):
        value = bytes(value)
    # ... existing logic for bytes, str, etc. ...

## Patch

```diff

```
