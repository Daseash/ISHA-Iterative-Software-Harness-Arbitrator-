# django__django-11620

## Plan

**Step 1 – Root cause**
`django.urls.resolvers` resolves URL patterns by iterating over the converters for each captured parameter. It wraps the call to `converter.to_python(value)` in a `try/except` that only catches `ValueError`. When a path converter raises `Http404` (e.g., to implement a `get_object_or_404`‑style check), the exception bubbles out of the resolver instead of being treated as “this pattern does not match”. In DEBUG mode Django’s normal 404 handling is bypassed, and the uncaught `Http404` is turned into the generic “A server error occurred…” page (a 500 response).

**Step 2 – Required code changes**

| File | Location | Change |
|------|----------|--------|
| `django/urls/resolvers.py` | Add import | Insert `from django.http import Http404` near the other imports. |
| `django/urls/resolvers.py` | Inside the loop that converts captured values (around line where `converter.to_python` is called) | Replace the current exception handling:<br><br>```python<br>try:<br>    value = converter.to_python(value)<br>except ValueError:<br>    return None<br>```<br>with:<br><br>```python<br>try:<br>    value = converter.to_python(value)<br>except (ValueError, Http404):<br>    # Treat both as a non‑matching conversion – let resolver try the next pattern<br>    return None<br>```<br>Optionally add a short comment explaining the rationale. |

These two modifications make the resolver treat `Http404` the same way it treats `ValueError`, allowing the URL resolver to skip the current pattern and ultimately return a proper 404 response (with the detailed debug page when `DEBUG = True`). No other files need to be touched, preserving atomicity.

**Confidence:** 0.93

## Patch

```diff

```
