# django__django-11422

## Plan

Step 1: Root cause — main() computes the wrong expression — the arithmetic operator does not match the documented behaviour in the report.
Step 2: Edit compress.py — in main(), apply: replace the return expression with the operator the report expects.

## Patch

```diff

```
