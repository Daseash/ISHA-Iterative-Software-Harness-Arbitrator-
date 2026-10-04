# pylint-dev__pylint-5859

## Plan

@@
-        self._notes_regexp = re.compile(r'^(?:%s):' % '|'.join(self.notes))
+        # Escape note tags so that tags made only of punctuation are treated
+        # as literal text rather than regex meta‑characters.
+        escaped_notes = [re.escape(note) for note in self.notes]
+        self._notes_regexp = re.compile(r'^(?:%s):' % '|'.join(escaped_notes))

## Patch

```diff

```
