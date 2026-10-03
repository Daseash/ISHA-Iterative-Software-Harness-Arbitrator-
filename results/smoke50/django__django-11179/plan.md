# django__django-11179

## Plan

if self.can_fast_delete(specified_objects):
       self.fast_deletes = []
       # Clear PKs of instances that were fast‑deleted
       for model, instances in self.data.items():
           for obj in instances:
               obj.pk = None
       self.fast_deletes = []
       return

## Patch

```diff

```
